import logging
import stripe
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request

from api.deps import get_current_user, UserContext
from core.config import get_settings
from core.limiter import limiter
from db.supabase import get_stripe_customer_id, set_stripe_customer_id, update_plan_and_status
from models.requests import CheckoutRequest
from models.responses import BillingUrlResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/billing", tags=["billing"])

_PLAN_TO_PRICE = {
    "solo": lambda s: s.stripe_price_solo,
    "pro": lambda s: s.stripe_price_pro,
}

_PRICE_TO_PLAN = {}


def _get_stripe():
    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key
    return settings


@router.post("/checkout", response_model=BillingUrlResponse)
@limiter.limit("10/minute")
async def create_checkout(
    request: Request,
    body: CheckoutRequest,
    user: UserContext = Depends(get_current_user),
):
    settings = _get_stripe()

    customer_id = get_stripe_customer_id(user.id)
    if not customer_id:
        customer = stripe.Customer.create(email=user.email, metadata={"user_id": user.id})
        customer_id = customer.id
        set_stripe_customer_id(user.id, customer_id)

    price_id = _PLAN_TO_PRICE[body.plan](settings)
    if not price_id:
        raise HTTPException(status_code=500, detail="Plano não configurado")

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[{"price": price_id, "quantity": 1}],
        success_url=f"{settings.frontend_url}/sucesso",
        cancel_url=f"{settings.frontend_url}/#precos",
        metadata={"user_id": user.id, "plan": body.plan},
    )

    return BillingUrlResponse(url=session.url)


@router.post("/portal", response_model=BillingUrlResponse)
async def create_portal(user: UserContext = Depends(get_current_user)):
    settings = _get_stripe()

    customer_id = get_stripe_customer_id(user.id)
    if not customer_id:
        raise HTTPException(status_code=400, detail="Nenhuma assinatura encontrada")

    session = stripe.billing_portal.Session.create(
        customer=customer_id,
        return_url=f"{settings.frontend_url}/configuracoes",
    )

    return BillingUrlResponse(url=session.url)


@router.post("/webhook", status_code=200)
async def stripe_webhook(request: Request):
    settings = _get_stripe()

    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig, settings.stripe_webhook_secret)
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Assinatura inválida")

    try:
        _handle_event(event)
    except Exception as e:
        logger.error(f"Erro ao processar webhook {event['type']}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar evento")

    return {"received": True}


def _handle_event(event: dict) -> None:
    etype = event["type"]
    data = event["data"]["object"]

    if etype == "checkout.session.completed":
        user_id = data.get("metadata", {}).get("user_id")
        plan = data.get("metadata", {}).get("plan")
        subscription_id = data.get("subscription")
        if not user_id or not plan:
            return
        sub = stripe.Subscription.retrieve(subscription_id)
        period_end = datetime.fromtimestamp(sub["current_period_end"], tz=timezone.utc)
        update_plan_and_status(user_id, plan, "active", subscription_id, period_end)

    elif etype == "customer.subscription.deleted":
        customer_id = data.get("customer")
        period_end_ts = data.get("current_period_end")
        _downgrade_by_customer(customer_id, period_end_ts)

    elif etype == "customer.subscription.updated":
        customer_id = data.get("customer")
        status = data.get("status")
        subscription_id = data.get("id")
        period_end_ts = data.get("current_period_end")
        period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc) if period_end_ts else None
        user_id = _user_id_from_customer(customer_id)
        if user_id:
            if status in ("canceled", "unpaid"):
                update_plan_and_status(user_id, "free", status, subscription_id, period_end)
            else:
                update_plan_and_status(user_id, _plan_from_subscription(data), status, subscription_id, period_end)

    elif etype == "invoice.payment_failed":
        customer_id = data.get("customer")
        user_id = _user_id_from_customer(customer_id)
        if user_id:
            update_plan_and_status(user_id, _get_current_plan(user_id), "past_due")


def _user_id_from_customer(customer_id: str) -> str | None:
    try:
        from db.supabase import get_admin
        result = get_admin().table("profiles").select("id").eq("stripe_customer_id", customer_id).single().execute()
        return result.data.get("id") if result.data else None
    except Exception:
        return None


def _get_current_plan(user_id: str) -> str:
    from db.supabase import get_user_plan
    return get_user_plan(user_id)


def _downgrade_by_customer(customer_id: str, period_end_ts: int | None) -> None:
    user_id = _user_id_from_customer(customer_id)
    if not user_id:
        return
    period_end = datetime.fromtimestamp(period_end_ts, tz=timezone.utc) if period_end_ts else None
    update_plan_and_status(user_id, "free", "canceled", None, period_end)


def _plan_from_subscription(sub: dict) -> str:
    settings = get_settings()
    items = sub.get("items", {}).get("data", [])
    if not items:
        return "free"
    price_id = items[0].get("price", {}).get("id", "")
    if price_id == settings.stripe_price_pro:
        return "pro"
    if price_id == settings.stripe_price_solo:
        return "solo"
    return "free"
