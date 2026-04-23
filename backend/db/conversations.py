import logging
from db.supabase import get_admin

logger = logging.getLogger(__name__)

_WINDOW = 5


def get_or_create_conversation(user_id: str) -> str:
    admin = get_admin()
    result = (
        admin.table("conversations")
        .select("id")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    if result.data:
        return result.data[0]["id"]

    created = admin.table("conversations").insert({"user_id": user_id, "summary": ""}).execute()
    return created.data[0]["id"]


def get_history(conversation_id: str) -> tuple[str, list[dict]]:
    admin = get_admin()

    conv = admin.table("conversations").select("summary").eq("id", conversation_id).single().execute()
    summary = conv.data.get("summary", "") if conv.data else ""

    msgs = (
        admin.table("messages")
        .select("role, content")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )

    messages = msgs.data or []
    pairs = _to_pairs(messages)
    recent = pairs[-_WINDOW:]

    historico = [{"pergunta": p, "resposta": r} for p, r in recent]
    return summary, historico


def save_message(conversation_id: str, role: str, content: str) -> None:
    get_admin().table("messages").insert({
        "conversation_id": conversation_id,
        "role": role,
        "content": content,
    }).execute()


def count_pairs(conversation_id: str) -> int:
    result = (
        get_admin().table("messages")
        .select("id", count="exact")
        .eq("conversation_id", conversation_id)
        .eq("role", "user")
        .execute()
    )
    return result.count or 0


def pop_oldest_pair(conversation_id: str) -> tuple[str, str] | None:
    admin = get_admin()
    msgs = (
        admin.table("messages")
        .select("id, role, content")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .limit(2)
        .execute()
    )
    rows = msgs.data or []
    if len(rows) < 2:
        return None

    pergunta = next((r["content"] for r in rows if r["role"] == "user"), None)
    resposta = next((r["content"] for r in rows if r["role"] == "assistant"), None)
    if not pergunta or not resposta:
        return None

    ids = [r["id"] for r in rows]
    admin.table("messages").delete().in_("id", ids).execute()
    return pergunta, resposta


def update_summary(conversation_id: str, summary: str) -> None:
    get_admin().table("conversations").update({"summary": summary}).eq("id", conversation_id).execute()


def reset_conversation(user_id: str) -> str:
    created = get_admin().table("conversations").insert({"user_id": user_id, "summary": ""}).execute()
    return created.data[0]["id"]


def _to_pairs(messages: list[dict]) -> list[tuple[str, str]]:
    pairs = []
    i = 0
    while i < len(messages) - 1:
        if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
            pairs.append((messages[i]["content"], messages[i + 1]["content"]))
            i += 2
        else:
            i += 1
    return pairs
