"""
Enhanced schemas with comprehensive validation.

Copy this to: backend/app/schemas.py (replace existing)
"""

from __future__ import annotations
from pydantic import BaseModel, Field, field_validator, ConfigDict
from datetime import datetime, timedelta
from typing import Optional, Literal
import re


class MeOut(BaseModel):
    """User information output"""
    tg_user_id: int
    first_name: str
    last_name: str = ""
    username: str = ""
    language_code: str = ""
    
    model_config = ConfigDict(from_attributes=True)


class CategoryCreate(BaseModel):
    """Create category request"""
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    kind: Literal["expense", "income", "debt"] = Field(default="expense", description="Category type")
    color: str = Field(..., pattern=r"^#[0-9A-Fa-f]{6}$", description="Hex color code")
    icon: str = Field(..., min_length=1, max_length=50, description="Icon identifier")
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate and sanitize category name"""
        # Strip whitespace
        v = v.strip()
        
        if not v:
            raise ValueError("Category name cannot be empty")
        
        # Remove multiple consecutive spaces
        v = re.sub(r'\s+', ' ', v)
        
        # Check for potential SQL injection patterns
        dangerous_patterns = [
            'drop ', 'delete ', 'insert ', 'update ', 'select ',
            '--', ';', '/*', '*/', 'xp_', 'sp_', 'exec'
        ]
        
        v_lower = v.lower()
        for pattern in dangerous_patterns:
            if pattern in v_lower:
                raise ValueError(f"Invalid characters in category name: '{pattern}'")
        
        # Check for XSS patterns
        xss_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=']
        for pattern in xss_patterns:
            if pattern in v_lower:
                raise ValueError(f"Invalid characters in category name: '{pattern}'")
        
        return v
    
    @field_validator('icon')
    @classmethod
    def validate_icon(cls, v: str) -> str:
        """Validate icon name"""
        # Only allow alphanumeric, dash, and underscore
        if not re.match(r'^[a-z0-9_-]+$', v.lower()):
            raise ValueError("Icon name must contain only letters, numbers, dashes, and underscores")
        
        return v.lower()
    
    @field_validator('color')
    @classmethod
    def validate_color(cls, v: str) -> str:
        """Validate and normalize color"""
        v = v.upper()
        
        # Additional validation: ensure it's not just #000000 or #FFFFFF repeatedly
        if v == "#000000" or v == "#FFFFFF":
            # These are valid but maybe warn in logs
            pass
        
        return v


class CategoryUpdate(BaseModel):
    """Update category request"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    kind: Optional[Literal["expense", "income", "debt"]] = None
    color: Optional[str] = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")
    icon: Optional[str] = Field(None, min_length=1, max_length=50)
    is_active: Optional[bool] = None
    
    # Reuse validators from CategoryCreate
    _validate_name = field_validator('name')(CategoryCreate.validate_name.__func__)
    _validate_icon = field_validator('icon')(CategoryCreate.validate_icon.__func__)
    _validate_color = field_validator('color')(CategoryCreate.validate_color.__func__)


class CategoryOut(BaseModel):
    """Category output"""
    id: int
    name: str
    kind: str
    color: str
    icon: str
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class TxCreate(BaseModel):
    """Create transaction request"""
    type: Literal["expense", "income"] = Field(..., description="Transaction type")
    amount: int = Field(..., gt=0, lt=1_000_000_000, description="Amount in cents/smallest currency unit")
    note: str = Field(default="", max_length=500, description="Optional note or description")
    category_id: Optional[int] = Field(default=None, ge=1, description="Category ID")
    occurred_at: Optional[datetime] = Field(default=None, description="When the transaction occurred")
    
    @field_validator('note')
    @classmethod
    def validate_note(cls, v: str) -> str:
        """Sanitize note text"""
        if not v:
            return ""
        
        # Strip whitespace
        v = v.strip()
        
        # Remove control characters but keep newlines and tabs
        v = ''.join(char for char in v if char.isprintable() or char in ['\n', '\t'])
        
        # Remove multiple consecutive spaces
        v = re.sub(r' +', ' ', v)
        
        # Remove multiple consecutive newlines
        v = re.sub(r'\n{3,}', '\n\n', v)
        
        # Enforce max length strictly
        v = v[:500]
        
        # Basic XSS prevention
        xss_patterns = ['<script', 'javascript:', 'onerror=', 'onclick=', 'onload=']
        v_lower = v.lower()
        for pattern in xss_patterns:
            if pattern in v_lower:
                raise ValueError(f"Invalid content in note: '{pattern}'")
        
        return v
    
    @field_validator('occurred_at')
    @classmethod
    def validate_occurred_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate transaction date"""
        if v is None:
            return v
        
        now = datetime.utcnow()
        
        # Don't allow future dates (with 1 day grace period for timezone issues)
        if v > now + timedelta(days=1):
            raise ValueError("Transaction date cannot be more than 1 day in the future")
        
        # Don't allow very old dates (10 years)
        if v < now - timedelta(days=365 * 10):
            raise ValueError("Transaction date cannot be more than 10 years in the past")
        
        return v
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: int) -> int:
        """Additional amount validation"""
        if v <= 0:
            raise ValueError("Amount must be positive")
        
        if v > 999_999_999:
            raise ValueError("Amount is too large")
        
        # Check for suspicious patterns (e.g., exact powers of 10 over a certain size)
        # This could indicate testing or fraudulent behavior
        if v >= 1_000_000 and v % 1_000_000 == 0:
            # Log this for investigation
            pass
        
        return v
    
    @field_validator('category_id')
    @classmethod
    def validate_category_id(cls, v: Optional[int]) -> Optional[int]:
        """Validate category ID"""
        if v is None:
            return v
        
        if v < 1:
            raise ValueError("Invalid category ID")
        
        # Note: We can't check if category exists here, that's done in the endpoint
        return v


class TxOut(BaseModel):
    """Transaction output"""
    id: int
    type: str
    amount: int
    note: str
    occurred_at: datetime
    category_id: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class StatsOut(BaseModel):
    """Statistics output"""
    balance: int = Field(..., description="Current balance (income - expenses)")
    week_spent: int = Field(..., description="Amount spent this week")
    week_income: int = Field(..., description="Income this week")
    month_spent: int = Field(..., description="Amount spent this month")
    month_income: int = Field(..., description="Income this month")
    
    model_config = ConfigDict(from_attributes=True)


# Additional schemas for future features
class BudgetGoal(BaseModel):
    """Budget goal schema"""
    category_id: Optional[int] = None
    amount: int = Field(..., gt=0)
    period: Literal["daily", "weekly", "monthly"] = "monthly"
    start_date: datetime
    end_date: Optional[datetime] = None


class TransactionFilter(BaseModel):
    """Filter parameters for transaction queries"""
    type: Optional[Literal["expense", "income"]] = None
    category_id: Optional[int] = None
    min_amount: Optional[int] = Field(None, ge=0)
    max_amount: Optional[int] = Field(None, ge=0)
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    search: Optional[str] = Field(None, max_length=100)
    
    @field_validator('search')
    @classmethod
    def validate_search(cls, v: Optional[str]) -> Optional[str]:
        """Sanitize search query"""
        if not v:
            return None
        
        v = v.strip()
        
        # Remove dangerous characters
        v = re.sub(r'[<>\'";]', '', v)
        
        return v[:100] if v else None


class ExportRequest(BaseModel):
    """Export data request"""
    format: Literal["csv", "excel", "json"] = "csv"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_categories: bool = True


class ErrorResponse(BaseModel):
    """Standard error response"""
    error: str
    details: Optional[dict] = None
    request_id: Optional[str] = None


class SuccessResponse(BaseModel):
    """Standard success response"""
    ok: bool = True
    message: Optional[str] = None
    data: Optional[dict] = None
