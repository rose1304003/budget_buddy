from __future__ import annotations
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field, Relationship

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tg_user_id: int = Field(index=True, unique=True)
    first_name: str = ""
    last_name: str = ""
    username: str = ""
    language_code: str = ""
    created_at: datetime = Field(default_factory=datetime.utcnow)

    categories: list["Category"] = Relationship(back_populates="user")
    transactions: list["Transaction"] = Relationship(back_populates="user")

class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    name: str = Field(index=True)
    kind: str = Field(default="expense")  # expense | income | debt
    color: str = Field(default="#22d3ee")
    icon: str = Field(default="tag")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    user: Optional[User] = Relationship(back_populates="categories")

class Transaction(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", index=True)

    type: str = Field(default="expense")  # expense | income
    amount: int
    note: str = ""
    occurred_at: datetime = Field(default_factory=datetime.utcnow, index=True)

    user: Optional[User] = Relationship(back_populates="transactions")
