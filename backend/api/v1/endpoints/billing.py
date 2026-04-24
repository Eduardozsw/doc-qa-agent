import json
import logging
import stripe
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request

from api.deps import get_current_user, UserContext
from core.config import get_settings
from core.limiter import limiter
from db.supabase import get_customer_id, set_customer_id, update_plan_and_status, get_user_plan
from models.requests import CheckoutRequest
from models.responses import BillingUrlResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

_WEBHOOK_EVENT_TTL = 7 * 86400


def _stripe():
    stripe.api_key = get_settings().stripe_secret_key
    return stripe


@router.post("/checkout", response_model=BillingUrlResponse)
@limiter.limit("10/minute")
async def create_checkout(
    request: Request,
    body: CheckoutRequest,
    user: UserContext = Depends(get_current_user),
):
    settings = get_settings()
    s = _stripe()

    price_id = (
        settings.stripe_price_solo if body.plan == "solo"
        else settings.stripe_price_pro
    )
    if not price_id:
        raise HTTPException(status_code=500, detail="Plano não configurado")

    customer_id = get_customer_id(user.id)

    if not customer_id:
        try:
            customer = s.Customer.create(
                email=user.email,
                name=user.name or user.email,
                metadata={"user_id": user.id},
            )
            customer_id = customer.id
            set_customer_id(user.id, customer_id)
        except stripe.StripeError as e:
            logger.error(f"Stripe Customer.create falhou: {e}")
            raise HTTPException(status_code=502, detail=f"Erro Stripe ao criar cliente: {e.user_message}")

    try:
        session = s.checkout.Session.create(
            customer=customer_id,
            mode="subscription",
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=f"{settings.frontend_url}/sucesso",
            cancel_url=f"{settings.frontend_url}/#precos",
            subscription_data={"metadata": {"user_id": user.id, "plan": body.plan}},
        )
    except stripe.StripeError as e:
        logger.error(f"Stripe checkout.Session.create falhou: {e}")
        raise HTTPException(status_code=502, detail=f"Erro Stripe: {e.user_message}")

    return BillingUrlResponse(url=session.url)


@router.post("/portal", response_model=BillingUrlResponse)
async def create_portal(user: UserContext = Depends(get_current_user)):
    s = _stripe()
    customer_id = get_customer_id(user.id)
    if not customer_id:
        raise HTTPException(status_code=400, detail="Nenhuma assinatura encontrada")

    try:
        portal = s.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{get_settings().frontend_url}/configuracoes",
        )
    except stripe.StripeError as e:
        logger.error(f"Stripe billing_portal.Session.create falhou: {e}")
        raise HTTPException(status_code=502, detail=f"Erro Stripe: {e.user_message}")

    return BillingUrlResponse(url=portal.url)


@router.post("/webhook", status_code=200)
async def stripe_webhook(request: Request):
    settings = get_settings()
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = _stripe().Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except stripe.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Assinatura inválida")

    from db.redis import get_client as get_redis
    event_id = event.get("id")
    if event_id:
        key = f"stripe:webhook:{event_id}"
        try:
            if not get_redis().set(key, "1", nx=True, ex=_WEBHOOK_EVENT_TTL):
                logger.info(f"Webhook {event_id} já processado, ignorando replay")
                return {"received": True, "duplicate": True}
        except Exception as e:
            logger.warning(f"Falha no dedupe de webhook (prosseguindo): {e}")

    try:
        _handle_event(event)
    except Exception as e:
        logger.error(f"Erro ao processar webhook {event.get('type')}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar evento")

    return {"received": True}


def _handle_event(event: dict) -> None:
    etype = event.get("type")
    data = event.get("data", {}).get("object", {})

    if etype == "checkout.session.completed":
        user_id = data.get("metadata", {}).get("user_id")
        customer_id = data.get("customer")
        if not user_id and customer_id:
            user_id = _user_id_from_customer(customer_id)
        plan = data.get("metadata", {}).get("plan", "solo")
        subscription_id = data.get("subscription")
        if user_id:
            period_end = _period_end_from_subscription(subscription_id)
            update_plan_and_status(user_id, plan, "active", subscription_id, period_end)

    elif etype == "invoice.paid":
        subscription_id = data.get("subscription")
        customer_id = data.get("customer")
        user_id = _user_id_from_customer(customer_id)
        if user_id:
            current_plan = get_user_plan(user_id)
            period_end = _period_end_from_subscription(subscription_id)
            update_plan_and_status(user_id, current_plan, "active", subscription_id, period_end)

    elif etype == "customer.subscription.deleted":
        customer_id = data.get("customer")
        user_id = _user_id_from_customer(customer_id)
        canceled_at = data.get("canceled_at")
        period_end = datetime.fromtimestamp(canceled_at, tz=timezone.utc) if canceled_at else None
        if user_id:
            update_plan_and_status(user_id, "free", "canceled", None, period_end)


def _user_id_from_customer(customer_id: str) -> str | None:
    if not customer_id:
        return None
    try:
        from db.supabase import get_admin
        result = (
            get_admin()
            .table("profiles")
            .select("id")
            .eq("customer_id", customer_id)
            .single()
            .execute()
        )
        return result.data.get("id") if result.data else None
    except Exception:
        return None


def _period_end_from_subscription(subscription_id: str | None) -> datetime | None:
    if not subscription_id:
        return None
    try:
        sub = _stripe().Subscription.retrieve(subscription_id)
        ts = sub.get("current_period_end")
        return datetime.fromtimestamp(ts, tz=timezone.utc) if ts else None
    except Exception:
        return None
