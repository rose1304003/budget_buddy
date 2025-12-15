"""Database seeding for default categories."""

from sqlmodel import Session, select
from .models import Category

DEFAULT_CATEGORIES = [
    ("Coffee & Snacks", "expense", "#22d3ee", "coffee"),
    ("Transport", "expense", "#22d3ee", "car"),
    ("Groceries", "expense", "#22d3ee", "shopping-basket"),
    ("Bills & Utilities", "expense", "#22d3ee", "zap"),
    ("Education", "expense", "#22d3ee", "graduation-cap"),
    ("Salary", "income", "#22d3ee", "wallet"),
]

def ensure_seed(session: Session, user_id: int) -> None:
    """Ensure default categories exist for a user.
    
    Creates default categories if the user has no categories yet.
    This is called automatically when a user is created or accessed.
    
    Args:
        session: Database session
        user_id: User ID to seed categories for
    """
    existing = session.exec(select(Category).where(Category.user_id == user_id)).first()
    if existing:
        return
    for name, kind, color, icon in DEFAULT_CATEGORIES:
        session.add(
            Category(
                user_id=user_id,
                name=name,
                kind=kind,
                color=color,
                icon=icon,
                is_active=True
            )
        )
    session.commit()
