"""Root pytest hooks."""


def pytest_collection_modifyitems(items: list) -> None:
    """Run WebSocket tests last to avoid event-loop conflicts with async tests."""
    ws_items = [item for item in items if "test_websocket_chat" in item.nodeid]
    if not ws_items:
        return
    other_items = [item for item in items if item not in ws_items]
    items[:] = other_items + ws_items
