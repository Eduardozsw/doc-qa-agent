import pytest

from db.conversations import (
    count_pairs,
    get_history,
    get_or_create_conversation,
    pop_oldest_pair,
    reset_conversation,
    save_message,
    update_summary,
)
from db.users import create_user


@pytest.fixture
def user_id(db):
    user = create_user("conversas@teste.com", "senha1234", "Fulano")
    return user["id"]


@pytest.mark.db
def test_get_or_create_conversation_creates_once(user_id):
    conv_id_1 = get_or_create_conversation(user_id)
    conv_id_2 = get_or_create_conversation(user_id)
    assert conv_id_1 == conv_id_2
    assert isinstance(conv_id_1, str)


@pytest.mark.db
def test_save_message_and_get_history(user_id):
    conv_id = get_or_create_conversation(user_id)
    save_message(conv_id, "user", "qual o prazo?")
    save_message(conv_id, "assistant", "30 dias")

    summary, historico = get_history(conv_id, user_id)
    assert summary == ""
    assert historico == [{"pergunta": "qual o prazo?", "resposta": "30 dias"}]


@pytest.mark.db
def test_get_history_window_keeps_last_5_pairs(user_id):
    conv_id = get_or_create_conversation(user_id)
    for i in range(7):
        save_message(conv_id, "user", f"pergunta {i}")
        save_message(conv_id, "assistant", f"resposta {i}")

    _, historico = get_history(conv_id, user_id)
    assert len(historico) == 5
    assert historico[0]["pergunta"] == "pergunta 2"
    assert historico[-1]["pergunta"] == "pergunta 6"


@pytest.mark.db
def test_count_pairs_counts_user_messages(user_id):
    conv_id = get_or_create_conversation(user_id)
    save_message(conv_id, "user", "p1")
    save_message(conv_id, "assistant", "r1")
    save_message(conv_id, "user", "p2")
    save_message(conv_id, "assistant", "r2")

    assert count_pairs(conv_id) == 2


@pytest.mark.db
def test_pop_oldest_pair_removes_and_returns(user_id):
    conv_id = get_or_create_conversation(user_id)
    save_message(conv_id, "user", "p1")
    save_message(conv_id, "assistant", "r1")
    save_message(conv_id, "user", "p2")
    save_message(conv_id, "assistant", "r2")

    pair = pop_oldest_pair(conv_id)
    assert pair == ("p1", "r1")
    assert count_pairs(conv_id) == 1


@pytest.mark.db
def test_pop_oldest_pair_returns_none_when_less_than_2_messages(user_id):
    conv_id = get_or_create_conversation(user_id)
    save_message(conv_id, "user", "p1")
    assert pop_oldest_pair(conv_id) is None


@pytest.mark.db
def test_update_summary_persists(user_id):
    conv_id = get_or_create_conversation(user_id)
    update_summary(conv_id, "resumo da conversa")
    summary, _ = get_history(conv_id, user_id)
    assert summary == "resumo da conversa"


@pytest.mark.db
def test_reset_conversation_creates_new_id(user_id):
    conv_id_1 = get_or_create_conversation(user_id)
    conv_id_2 = reset_conversation(user_id)
    assert conv_id_1 != conv_id_2
    assert get_or_create_conversation(user_id) == conv_id_2
