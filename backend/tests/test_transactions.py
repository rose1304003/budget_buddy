"""
Tests for transaction endpoints.

Copy this to: backend/tests/test_transactions.py

Run tests with: pytest tests/test_transactions.py -v
"""

import pytest
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.models import Transaction, User, Category
from tests.conftest import create_test_init_data, assert_response_ok, assert_valid_transaction


class TestTransactionList:
    """Tests for GET /api/transactions"""
    
    def test_list_empty_transactions(self, client: TestClient, auth_headers: dict):
        """Should return empty list for new user"""
        response = client.get("/api/transactions", headers=auth_headers)
        assert_response_ok(response)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0
    
    def test_list_transactions(
        self,
        client: TestClient,
        auth_headers: dict,
        test_transaction: Transaction
    ):
        """Should return list of user's transactions"""
        response = client.get("/api/transactions", headers=auth_headers)
        assert_response_ok(response)
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert_valid_transaction(data[0])
        assert data[0]["id"] == test_transaction.id
    
    def test_list_transactions_with_limit(
        self,
        client: TestClient,
        auth_headers: dict,
        session: Session,
        test_user: User,
        test_category: Category
    ):
        """Should respect limit parameter"""
        # Create 10 transactions
        for i in range(10):
            tx = Transaction(
                user_id=test_user.id,
                category_id=test_category.id,
                type="expense",
                amount=1000 * (i + 1),
                note=f"Transaction {i}"
            )
            session.add(tx)
        session.commit()
        
        # Request only 5
        response = client.get("/api/transactions?limit=5", headers=auth_headers)
        assert_response_ok(response)
        
        data = response.json()
        assert len(data) == 5
    
    def test_list_transactions_ordered_by_date(
        self,
        client: TestClient,
        auth_headers: dict,
        session: Session,
        test_user: User,
        test_category: Category
    ):
        """Should return transactions ordered by date (newest first)"""
        now = datetime.utcnow()
        
        # Create transactions with different dates
        for i in range(3):
            tx = Transaction(
                user_id=test_user.id,
                category_id=test_category.id,
                type="expense",
                amount=1000,
                note=f"Transaction {i}",
                occurred_at=now - timedelta(days=i)
            )
            session.add(tx)
        session.commit()
        
        response = client.get("/api/transactions", headers=auth_headers)
        assert_response_ok(response)
        
        data = response.json()
        assert len(data) == 3
        
        # Verify ordering (newest first)
        dates = [datetime.fromisoformat(tx["occurred_at"].replace('Z', '+00:00')) for tx in data]
        assert dates == sorted(dates, reverse=True)


class TestTransactionCreate:
    """Tests for POST /api/transactions"""
    
    def test_create_expense(
        self,
        client: TestClient,
        auth_headers: dict,
        test_category: Category
    ):
        """Should create a new expense transaction"""
        payload = {
            "type": "expense",
            "amount": 75000,
            "note": "Coffee and snacks",
            "category_id": test_category.id
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert_response_ok(response, 200)
        
        data = response.json()
        assert_valid_transaction(data)
        assert data["type"] == "expense"
        assert data["amount"] == 75000
        assert data["note"] == "Coffee and snacks"
        assert data["category_id"] == test_category.id
    
    def test_create_income(
        self,
        client: TestClient,
        auth_headers: dict,
        test_category: Category
    ):
        """Should create a new income transaction"""
        payload = {
            "type": "income",
            "amount": 500000,
            "note": "Salary",
            "category_id": test_category.id
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert_response_ok(response)
        
        data = response.json()
        assert data["type"] == "income"
        assert data["amount"] == 500000
    
    def test_create_transaction_with_custom_date(
        self,
        client: TestClient,
        auth_headers: dict,
        test_category: Category
    ):
        """Should accept custom occurred_at date"""
        occurred_at = (datetime.utcnow() - timedelta(days=2)).isoformat() + "Z"
        
        payload = {
            "type": "expense",
            "amount": 25000,
            "note": "Past expense",
            "category_id": test_category.id,
            "occurred_at": occurred_at
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert_response_ok(response)
        
        data = response.json()
        assert "occurred_at" in data
    
    def test_create_transaction_without_category(
        self,
        client: TestClient,
        auth_headers: dict
    ):
        """Should allow creating transaction without category"""
        payload = {
            "type": "expense",
            "amount": 10000,
            "note": "Uncategorized expense"
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert_response_ok(response)
        
        data = response.json()
        assert data["category_id"] is None
    
    def test_create_transaction_without_note(
        self,
        client: TestClient,
        auth_headers: dict,
        test_category: Category
    ):
        """Should allow empty note"""
        payload = {
            "type": "expense",
            "amount": 5000,
            "category_id": test_category.id
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert_response_ok(response)
        
        data = response.json()
        assert data["note"] == ""


class TestTransactionValidation:
    """Tests for transaction input validation"""
    
    def test_reject_negative_amount(self, client: TestClient, auth_headers: dict):
        """Should reject negative amounts"""
        payload = {
            "type": "expense",
            "amount": -1000,
            "note": "Invalid"
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert response.status_code == 422  # Validation error
    
    def test_reject_zero_amount(self, client: TestClient, auth_headers: dict):
        """Should reject zero amounts"""
        payload = {
            "type": "expense",
            "amount": 0,
            "note": "Invalid"
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert response.status_code == 422
    
    def test_reject_invalid_type(self, client: TestClient, auth_headers: dict):
        """Should reject invalid transaction type"""
        payload = {
            "type": "invalid",
            "amount": 1000,
            "note": "Invalid type"
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert response.status_code == 422
    
    def test_reject_too_large_amount(self, client: TestClient, auth_headers: dict):
        """Should reject unreasonably large amounts"""
        payload = {
            "type": "expense",
            "amount": 1_000_000_000,  # 1 billion
            "note": "Too large"
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert response.status_code == 422
    
    def test_sanitize_note(
        self,
        client: TestClient,
        auth_headers: dict,
        test_category: Category
    ):
        """Should sanitize and trim note text"""
        payload = {
            "type": "expense",
            "amount": 1000,
            "note": "  Multiple   spaces   ",
            "category_id": test_category.id
        }
        
        response = client.post("/api/transactions", json=payload, headers=auth_headers)
        assert_response_ok(response)
        
        data = response.json()
        # Note should be trimmed
        assert data["note"].strip() == data["note"]


class TestTransactionDelete:
    """Tests for DELETE /api/transactions/{id}"""
    
    def test_delete_transaction(
        self,
        client: TestClient,
        auth_headers: dict,
        test_transaction: Transaction
    ):
        """Should delete user's own transaction"""
        response = client.delete(
            f"/api/transactions/{test_transaction.id}",
            headers=auth_headers
        )
        assert_response_ok(response)
        
        data = response.json()
        assert data["ok"] is True
        
        # Verify it's deleted
        response = client.get("/api/transactions", headers=auth_headers)
        data = response.json()
        assert len(data) == 0
    
    def test_delete_nonexistent_transaction(self, client: TestClient, auth_headers: dict):
        """Should return 404 for nonexistent transaction"""
        response = client.delete("/api/transactions/99999", headers=auth_headers)
        assert response.status_code == 404
    
    def test_cannot_delete_other_user_transaction(
        self,
        client: TestClient,
        test_bot_token: str,
        session: Session,
        test_transaction: Transaction
    ):
        """Should not allow deleting another user's transaction"""
        # Create different user's auth
        other_user_headers = {
            "X-TG-Init-Data": create_test_init_data(
                user_id=999999,  # Different user
                bot_token=test_bot_token
            )
        }
        
        response = client.delete(
            f"/api/transactions/{test_transaction.id}",
            headers=other_user_headers
        )
        assert response.status_code == 404  # Should not find it


class TestTransactionAuth:
    """Tests for transaction authentication"""
    
    def test_list_without_auth(self, client: TestClient):
        """Should reject requests without auth"""
        response = client.get("/api/transactions")
        assert response.status_code == 401
    
    def test_create_without_auth(self, client: TestClient):
        """Should reject transaction creation without auth"""
        payload = {
            "type": "expense",
            "amount": 1000,
            "note": "Test"
        }
        response = client.post("/api/transactions", json=payload)
        assert response.status_code == 401
    
    def test_delete_without_auth(self, client: TestClient):
        """Should reject deletion without auth"""
        response = client.delete("/api/transactions/1")
        assert response.status_code == 401
    
    def test_with_invalid_init_data(self, client: TestClient):
        """Should reject invalid initData"""
        headers = {"X-TG-Init-Data": "invalid_data"}
        response = client.get("/api/transactions", headers=headers)
        assert response.status_code == 401


# Parametrized tests
@pytest.mark.parametrize("transaction_type,amount,note", [
    ("expense", 1000, "Small expense"),
    ("expense", 999999, "Large expense"),
    ("income", 500000, "Salary payment"),
    ("income", 1, "Tiny income"),
])
def test_create_various_transactions(
    client: TestClient,
    auth_headers: dict,
    test_category: Category,
    transaction_type: str,
    amount: int,
    note: str
):
    """Test creating various valid transactions"""
    payload = {
        "type": transaction_type,
        "amount": amount,
        "note": note,
        "category_id": test_category.id
    }
    
    response = client.post("/api/transactions", json=payload, headers=auth_headers)
    assert_response_ok(response)
    
    data = response.json()
    assert data["type"] == transaction_type
    assert data["amount"] == amount
    assert data["note"] == note
