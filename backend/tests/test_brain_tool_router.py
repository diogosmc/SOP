"""Tests for brain tool router."""

from app.brain.schemas import ConversationContext
from app.brain.tool_router import decide_actions
from app.telegram.instructor import classify_telegram_message


def _context(message: str) -> ConversationContext:
    classification = classify_telegram_message(message)
    return ConversationContext(
        message=message,
        classification=classification,
        intent=classification["intent"],
        is_ack=message.strip().lower() in {"não vlw", "vlw", "ok"},
    )


def test_ack_has_no_actions() -> None:
    actions = decide_actions("Não vlw", _context("Não vlw"))
    assert len(actions) == 1
    assert actions[0].action == "none"


def test_autoescola_actions() -> None:
    actions = decide_actions("Amanhã tenho autoescola às 8", _context("Amanhã tenho autoescola às 8"))
    types = {a.action for a in actions}
    assert "update_journal" in types
    assert "create_memory" in types


def test_study_revision_actions() -> None:
    actions = decide_actions(
        "Preciso revisar anatomia amanhã",
        _context("Preciso revisar anatomia amanhã"),
    )
    types = {a.action for a in actions}
    assert "create_task" in types


def test_expense_actions() -> None:
    actions = decide_actions("Gastei 20 no lanche", _context("Gastei 20 no lanche"))
    types = {a.action for a in actions}
    assert "create_finance_transaction" in types


def test_note_actions() -> None:
    actions = decide_actions(
        "Anota que segunda eu preciso resolver pendências",
        _context("Anota que segunda eu preciso resolver pendências"),
    )
    assert any(a.action == "create_note" for a in actions)
