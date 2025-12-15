"""FastAPI application main module."""

from backend.app.telegram_webhook import router as telegram_router
app.include_router(telegram_router)

from __future__ import annotations
from datetime import datetime, timedelta

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, func

from .settings import settings
from .db import init_db, get_session
from .deps import get_current_user
from .models import User, Category, Transaction
from .schemas import MeOut, CategoryCreate, CategoryOut, CategoryUpdate, TxCreate, TxOut, StatsOut
from .seed import ensure_seed
from .middleware import (
    RateLimitMiddleware,
    RequestLoggingMiddleware,
    SecurityHeadersMiddleware,
)

app = FastAPI(title=settings.app_name)

# CORS Middleware
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middlewares (order matters - they execute bottom to top)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware, log_request_body=False)
app.add_middleware(RateLimitMiddleware, calls=200, period=60)


@app.on_event("startup")
def _startup():
    """Initialize database on application startup."""
    init_db()


def _get_or_create_user(session: Session, tg):
    """Get or create user from Telegram data."""
    user = session.exec(select(User).where(User.tg_user_id == tg.id)).first()
    if not user:
        user = User(
            tg_user_id=tg.id,
            first_name=tg.first_name,
            last_name=tg.last_name,
            username=tg.username,
            language_code=tg.language_code,
        )
        session.add(user)
        session.commit()
        session.refresh(user)
    else:
        user.first_name = tg.first_name
        user.last_name = tg.last_name
        user.username = tg.username
        user.language_code = tg.language_code
        session.add(user)
        session.commit()

    ensure_seed(session, user.id)
    return user


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"ok": True, "app": settings.app_name}


@app.get("/api/me", response_model=MeOut)
def me(tg=Depends(get_current_user), session: Session = Depends(get_session)):
    """Get current authenticated user information."""
    user = _get_or_create_user(session, tg)
    return MeOut(
        tg_user_id=user.tg_user_id,
        first_name=user.first_name,
        last_name=user.last_name,
        username=user.username,
        language_code=user.language_code,
    )


@app.get("/api/categories", response_model=list[CategoryOut])
def list_categories(tg=Depends(get_current_user), session: Session = Depends(get_session)):
    """List all categories for the authenticated user."""
    user = _get_or_create_user(session, tg)
    items = session.exec(
        select(Category)
        .where(Category.user_id == user.id)
        .order_by(Category.kind, Category.name)
    ).all()
    return [
        CategoryOut(
            id=c.id,
            name=c.name,
            kind=c.kind,
            color=c.color,
            icon=c.icon,
            is_active=c.is_active
        )
        for c in items
    ]


@app.post("/api/categories", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    tg=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new category for the authenticated user."""
    user = _get_or_create_user(session, tg)
    c = Category(
        user_id=user.id,
        name=payload.name.strip(),
        kind=payload.kind,
        color=payload.color,
        icon=payload.icon,
        is_active=True
    )
    session.add(c)
    session.commit()
    session.refresh(c)
    return CategoryOut(
        id=c.id,
        name=c.name,
        kind=c.kind,
        color=c.color,
        icon=c.icon,
        is_active=c.is_active
    )


@app.patch("/api/categories/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    payload: CategoryUpdate,
    tg=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update an existing category."""
    user = _get_or_create_user(session, tg)
    c = session.get(Category, category_id)
    if not c or c.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    
    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(c, k, v)
    
    session.add(c)
    session.commit()
    session.refresh(c)
    return CategoryOut(
        id=c.id,
        name=c.name,
        kind=c.kind,
        color=c.color,
        icon=c.icon,
        is_active=c.is_active
    )


@app.delete("/api/categories/{category_id}")
def delete_category(
    category_id: int,
    tg=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a category."""
    user = _get_or_create_user(session, tg)
    c = session.get(Category, category_id)
    if not c or c.user_id != user.id:
        raise HTTPException(status_code=404, detail="Category not found")
    session.delete(c)
    session.commit()
    return {"ok": True}


@app.get("/api/transactions", response_model=list[TxOut])
def list_transactions(
    limit: int = 50,
    tg=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """List transactions for the authenticated user."""
    user = _get_or_create_user(session, tg)
    items = session.exec(
        select(Transaction)
        .where(Transaction.user_id == user.id)
        .order_by(Transaction.occurred_at.desc())
        .limit(min(limit, 200))
    ).all()
    return [
        TxOut(
            id=t.id,
            type=t.type,
            amount=t.amount,
            note=t.note,
            occurred_at=t.occurred_at,
            category_id=t.category_id
        )
        for t in items
    ]


@app.post("/api/transactions", response_model=TxOut)
def create_transaction(
    payload: TxCreate,
    tg=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Create a new transaction."""
    user = _get_or_create_user(session, tg)
    occurred = payload.occurred_at or datetime.utcnow()
    t = Transaction(
        user_id=user.id,
        category_id=payload.category_id,
        type=payload.type,
        amount=int(payload.amount),
        note=payload.note.strip() if payload.note else "",
        occurred_at=occurred,
    )
    session.add(t)
    session.commit()
    session.refresh(t)
    return TxOut(
        id=t.id,
        type=t.type,
        amount=t.amount,
        note=t.note,
        occurred_at=t.occurred_at,
        category_id=t.category_id
    )


@app.delete("/api/transactions/{tx_id}")
def delete_transaction(
    tx_id: int,
    tg=Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete a transaction."""
    user = _get_or_create_user(session, tg)
    t = session.get(Transaction, tx_id)
    if not t or t.user_id != user.id:
        raise HTTPException(status_code=404, detail="Transaction not found")
    session.delete(t)
    session.commit()
    return {"ok": True}


@app.get("/api/stats", response_model=StatsOut)
def stats(tg=Depends(get_current_user), session: Session = Depends(get_session)):
    """Get statistics for the authenticated user."""
    user = _get_or_create_user(session, tg)

    now = datetime.utcnow()
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    def sum_type(since: datetime, typ: str) -> int:
        q = select(func.coalesce(func.sum(Transaction.amount), 0)).where(
            Transaction.user_id == user.id,
            Transaction.type == typ,
            Transaction.occurred_at >= since,
        )
        return int(session.exec(q).one())

    week_spent = sum_type(week_start, "expense")
    week_income = sum_type(week_start, "income")
    month_spent = sum_type(month_start, "expense")
    month_income = sum_type(month_start, "income")

    inc_all = int(session.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.user_id == user.id, Transaction.type == "income")
    ).one())
    exp_all = int(session.exec(
        select(func.coalesce(func.sum(Transaction.amount), 0))
        .where(Transaction.user_id == user.id, Transaction.type == "expense")
    ).one())
    balance = inc_all - exp_all

    return StatsOut(
        balance=balance,
        week_spent=week_spent,
        week_income=week_income,
        month_spent=month_spent,
        month_income=month_income,
    )
