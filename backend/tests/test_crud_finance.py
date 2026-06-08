"""CRUD and aggregate tests for finance transactions."""

from datetime import date

import pytest
from httpx import AsyncClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_income_transaction(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Salário",
            "amount": "5000.00",
            "type": "income",
            "category": "Salário",
            "transaction_date": "2026-06-01",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["type"] == "income"
    assert body["data"]["amount"] == "5000.00"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_create_expense_transaction(client: AsyncClient) -> None:
    response = await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Supermercado",
            "amount": "150.50",
            "type": "expense",
            "category": "Alimentação",
            "transaction_date": "2026-06-02",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["type"] == "expense"


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_transactions(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Item 1",
            "amount": "10.00",
            "type": "expense",
            "category": "Outros",
            "transaction_date": "2026-06-03",
        },
    )
    response = await client.get("/api/v1/finance/transactions", params={"page": 1, "page_size": 10})
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert len(body["data"]["items"]) >= 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_transactions_filter_by_type(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Receita teste",
            "amount": "100.00",
            "type": "income",
            "category": "Freelance",
            "transaction_date": "2026-06-04",
        },
    )
    await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Despesa teste",
            "amount": "50.00",
            "type": "expense",
            "category": "Transporte",
            "transaction_date": "2026-06-04",
        },
    )

    response = await client.get(
        "/api/v1/finance/transactions",
        params={"type": "income", "start_date": "2026-06-04", "end_date": "2026-06-04"},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert all(item["type"] == "income" for item in items)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_list_transactions_filter_by_category(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Farmácia",
            "amount": "80.00",
            "type": "expense",
            "category": "Saúde",
            "transaction_date": "2026-06-05",
        },
    )

    response = await client.get(
        "/api/v1/finance/transactions",
        params={"category": "Saúde", "start_date": "2026-06-05", "end_date": "2026-06-05"},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert all(item["category"] == "Saúde" for item in items)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_update_and_delete_transaction(client: AsyncClient) -> None:
    create_resp = await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Original",
            "amount": "25.00",
            "type": "expense",
            "category": "Lazer",
            "transaction_date": "2026-06-06",
        },
    )
    tx_id = create_resp.json()["data"]["id"]

    update_resp = await client.patch(
        f"/api/v1/finance/transactions/{tx_id}",
        json={"description": "Atualizado", "amount": "30.00"},
    )
    assert update_resp.status_code == 200
    updated = update_resp.json()["data"]
    assert updated["description"] == "Atualizado"
    assert updated["amount"] == "30.00"

    delete_resp = await client.delete(f"/api/v1/finance/transactions/{tx_id}")
    assert delete_resp.status_code == 200

    not_found = await client.get(f"/api/v1/finance/transactions/{tx_id}")
    assert not_found.status_code == 404


@pytest.mark.integration
@pytest.mark.asyncio
async def test_finance_summary(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Entrada",
            "amount": "1000.00",
            "type": "income",
            "category": "Salário",
            "transaction_date": "2026-06-07",
        },
    )
    await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Saída",
            "amount": "200.00",
            "type": "expense",
            "category": "Moradia",
            "transaction_date": "2026-06-07",
        },
    )

    response = await client.get(
        "/api/v1/finance/summary",
        params={"start_date": "2026-06-07", "end_date": "2026-06-07"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert float(data["income"]) >= 1000.0
    assert float(data["expense"]) >= 200.0
    assert float(data["balance"]) == float(data["income"]) - float(data["expense"])
    assert data["transactions_count"] >= 2


@pytest.mark.integration
@pytest.mark.asyncio
async def test_finance_by_category(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Cat A",
            "amount": "40.00",
            "type": "expense",
            "category": "CatTest",
            "transaction_date": "2026-06-08",
        },
    )

    response = await client.get(
        "/api/v1/finance/by-category",
        params={"start_date": "2026-06-08", "end_date": "2026-06-08"},
    )
    assert response.status_code == 200
    rows = response.json()["data"]
    categories = {row["category"] for row in rows}
    assert "CatTest" in categories


@pytest.mark.integration
@pytest.mark.asyncio
async def test_finance_by_day(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "Dia",
            "amount": "15.00",
            "type": "expense",
            "category": "Outros",
            "transaction_date": "2026-06-09",
        },
    )

    response = await client.get(
        "/api/v1/finance/by-day",
        params={"start_date": "2026-06-09", "end_date": "2026-06-09"},
    )
    assert response.status_code == 200
    rows = response.json()["data"]
    assert any(row["date"] == "2026-06-09" for row in rows)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_finance_search_filter(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/finance/transactions",
        json={
            "description": "BuscaUnicaXYZ",
            "amount": "9.99",
            "type": "expense",
            "category": "Outros",
            "transaction_date": str(date.today()),
        },
    )

    response = await client.get(
        "/api/v1/finance/transactions",
        params={"search": "BuscaUnicaXYZ"},
    )
    assert response.status_code == 200
    items = response.json()["data"]["items"]
    assert any("BuscaUnicaXYZ" in item["description"] for item in items)
