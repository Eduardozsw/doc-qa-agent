import base64
import hmac
import hashlib
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Request

import abacatepay

from api.deps import get_current_user, UserContext
from core.config import get_settings
from core.limiter import limiter
from db.supabase import get_customer_id, set_customer_id, update_plan_and_status, get_user_plan
from models.requests import CheckoutRequest
from models.responses import BillingUrlResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/billing", tags=["billing"])

_WEBHOOK_EVENT_TTL = 7 * 86400



def _get_client():
    settings = get_settings()
    return abacatepay.AbacatePay(settings.abacatepay_api_key), settings


@router.post("/checkout", response_model=BillingUrlResponse)
@limiter.limit("10/minute")
async def create_checkout(
    request: Request,
    body: CheckoutRequest,
    user: UserContext = Depends(get_current_user),
):
    client, settings = _get_client()

    product_id = (
        settings.abacatepay_product_solo if body.plan == "solo"
        else settings.abacatepay_product_pro
    )
    if not product_id:
        raise HTTPException(status_code=500, detail="Plano não configurado")

    customer_id = get_customer_id(user.id)

    try:
        billing = client.billing.create(
            products=[{"external_id": product_id, "name": body.plan, "quantity": 1, "price": 1900 if body.plan == "solo" else 4900, "description": f"Plano {body.plan}"}],
            return_url=f"{settings.frontend_url}/#precos",
            completion_url=f"{settings.frontend_url}/sucesso",
            customer_id=customer_id,
            metadata={"user_id": user.id, "plan": body.plan},
        )
    except Exception as e:
        logger.error(f"AbacatePay billing.create falhou: {e}")
        raise HTTPException(status_code=502, detail=f"Erro AbacatePay: {e}")

    if not customer_id and hasattr(billing, "customer") and billing.customer:
        new_customer_id = getattr(billing.customer, "id", None)
        if new_customer_id:
            set_customer_id(user.id, new_customer_id)

    return BillingUrlResponse(url=billing.url)


@router.post("/portal", response_model=BillingUrlResponse)
async def create_portal(user: UserContext = Depends(get_current_user)):
    raise HTTPException(status_code=501, detail="Gerenciamento de assinatura em breve")


@router.post("/webhook", status_code=200)
async def abacatepay_webhook(request: Request):
    _, settings = _get_client()
    payload = await request.body()
    sig = request.headers.get("x-webhook-signature", "")

    # V2: HMAC-SHA256 com o secret definido no painel, codificado em base64
    expected = base64.b64encode(
        hmac.new(settings.abacatepay_webhook_secret.encode(), payload, hashlib.sha256).digest()
    ).decode()

    if not hmac.compare_digest(expected, sig):
        raise HTTPException(status_code=400, detail="Assinatura inválida")

    event = json.loads(payload)

    from db.redis import get_client as get_redis
    event_id = event.get("id")
    if event_id:
        key = f"abacatepay:webhook:{event_id}"
        try:
            if not get_redis().set(key, "1", nx=True, ex=_WEBHOOK_EVENT_TTL):
                logger.info(f"Webhook {event_id} já processado, ignorando replay")
                return {"received": True, "duplicate": True}
        except Exception as e:
            logger.warning(f"Falha no dedupe de webhook (prosseguindo): {e}")

    try:
        _handle_event(event)
    except Exception as e:
        logger.error(f"Erro ao processar webhook {event.get('event')}: {e}")
        raise HTTPException(status_code=500, detail="Erro ao processar evento")

    return {"received": True}


def _handle_event(event: dict) -> None:
    etype = event.get("event")
    data = event.get("data", {})
    subscription = data.get("subscription", {})
    customer = data.get("customer", {})
    metadata = subscription.get("metadata") or {}

    if etype == "subscription.completed":
        user_id = metadata.get("user_id") or _user_id_from_customer(customer.get("id"))
        plan = metadata.get("plan", "solo")
        subscription_id = subscription.get("id")
        period_end = _parse_date(subscription.get("updatedAt"))
        if user_id:
            update_plan_and_status(user_id, plan, "active", subscription_id, period_end)

    elif etype == "subscription.renewed":
        user_id = _user_id_from_customer(customer.get("id"))
        subscription_id = subscription.get("id")
        period_end = _parse_date(subscription.get("updatedAt"))
        if user_id:
            current_plan = get_user_plan(user_id)
            update_plan_and_status(user_id, current_plan, "active", subscription_id, period_end)

    elif etype == "subscription.cancelled":
        user_id = metadata.get("user_id") or _user_id_from_customer(customer.get("id"))
        period_end = _parse_date(subscription.get("canceledAt"))
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


def _parse_date(value) -> datetime | None:
    if not value:
        return None
    if isinstance(value, int):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None
    return None
