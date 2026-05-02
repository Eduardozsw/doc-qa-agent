import logging
import resend
from core.config import get_settings

logger = logging.getLogger(__name__)

_PLAN_INFO = {
    "solo": {"name": "Solo", "docs": "10", "queries": "300", "page_number": False},
    "pro":  {"name": "Pro",  "docs": "20", "queries": "1.000", "page_number": True},
}


def send_welcome_email(to_email: str, plan: str, name: str = "") -> None:
    settings = get_settings()
    if not settings.resend_api_key or not settings.resend_from_email:
        logger.warning("Resend não configurado, email de boas-vindas ignorado")
        return

    info = _PLAN_INFO.get(plan)
    if not info:
        return

    greeting = f"Olá{', ' + name if name else ''}!"
    page_row = (
        '<li style="color:rgba(255,255,255,0.72);font-size:13px;padding:4px 0">'
        "✦&nbsp; Respostas com número de página</li>"
        if info["page_number"] else ""
    )
    app_url = settings.frontend_url

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#08080f;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif">
  <div style="max-width:520px;margin:0 auto;padding:40px 20px">

    <div style="text-align:center;margin-bottom:28px">
      <div style="display:inline-block;padding:6px 18px;background:rgba(245,158,11,0.08);border:1px solid rgba(245,158,11,0.2);border-radius:99px">
        <span style="color:#f59e0b;font-weight:700;font-size:15px">MindDoc</span>
      </div>
    </div>

    <div style="background:#0f0f1e;border:1px solid rgba(255,255,255,0.07);border-radius:18px;padding:32px 28px">
      <h1 style="color:#ffffff;font-size:22px;font-weight:700;margin:0 0 8px;letter-spacing:-0.4px">
        Bem-vindo ao plano {info['name']}! 🎉
      </h1>
      <p style="color:rgba(255,255,255,0.5);font-size:14px;line-height:1.6;margin:0 0 24px">
        {greeting} Seu plano está ativo e pronto para usar.
      </p>

      <div style="background:rgba(245,158,11,0.05);border:1px solid rgba(245,158,11,0.12);border-radius:10px;padding:18px 20px;margin-bottom:24px">
        <p style="color:rgba(255,255,255,0.35);font-size:11px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;margin:0 0 12px">
          O que está incluído
        </p>
        <ul style="margin:0;padding:0;list-style:none">
          <li style="color:rgba(255,255,255,0.72);font-size:13px;padding:4px 0">✦&nbsp; Busca em {info['docs']} documentos simultâneos</li>
          <li style="color:rgba(255,255,255,0.72);font-size:13px;padding:4px 0">✦&nbsp; {info['queries']} perguntas por mês</li>
          <li style="color:rgba(255,255,255,0.72);font-size:13px;padding:4px 0">✦&nbsp; Histórico de conversas</li>
          {page_row}
        </ul>
      </div>

      <a href="{app_url}/app"
         style="display:block;text-align:center;background:linear-gradient(135deg,#f59e0b,#d97706);color:#08080f;font-weight:700;font-size:14px;text-decoration:none;padding:13px 20px;border-radius:9px">
        Acessar o MindDoc →
      </a>
    </div>

    <p style="text-align:center;color:rgba(255,255,255,0.2);font-size:12px;margin-top:20px;line-height:1.6">
      Dúvidas? Responda este email, estamos aqui para ajudar.
    </p>

  </div>
</body>
</html>"""

    try:
        resend.api_key = settings.resend_api_key
        resend.Emails.send({
            "from": settings.resend_from_email,
            "to": [to_email],
            "subject": f"Bem-vindo ao plano {info['name']}! 🎉",
            "html": html,
        })
        logger.info(f"Email de boas-vindas enviado para {to_email} (plano {plan})")
    except Exception as e:
        logger.error(f"Falha ao enviar email de boas-vindas para {to_email}: {e}")
