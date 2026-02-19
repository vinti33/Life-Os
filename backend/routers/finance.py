"""
LifeOS Finance Router — Financial Management & Analytics
========================================================
Endpoints for managing transactions, budgets, and retrieving
aggregated financial metrics.
"""

from datetime import datetime, date, timedelta
from typing import List, Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from beanie import PydanticObjectId
from beanie.operators import In, And, GTE, LTE

from models import User, Transaction, Budget, TransactionType
from routers.auth import get_current_user
from utils.logger import get_logger

log = get_logger("router.finance")

router = APIRouter(prefix="/finance", tags=["finance"])

# --- Request Models ---

class TransactionCreate(BaseModel):
    date: str = Field(..., description="YYYY-MM-DD")
    amount: float = Field(..., gt=0)
    type: TransactionType
    category: str
    description: Optional[str] = None
    merchant: Optional[str] = None
    tags: List[str] = []
    is_recurring: bool = False

class BudgetCreate(BaseModel):
    month: str = Field(..., description="YYYY-MM")
    category: str
    amount_limit: float = Field(..., gt=0)
    is_hard_limit: bool = False

# --- Endpoints ---

@router.post("/transactions", response_model=Dict[str, str])
async def log_transaction(
    txn: TransactionCreate,
    user: User = Depends(get_current_user)
):
    """Log a new financial transaction (Income/Expense)."""
    new_txn = Transaction(
        user_id=user.id,
        **txn.dict()
    )
    await new_txn.insert()
    log.info(f"Transaction logged: user={user.id}, amount={txn.amount}, cat={txn.category}")
    return {"id": str(new_txn.id), "status": "recorded"}

@router.get("/transactions", response_model=List[Transaction])
async def get_transactions(
    month: Optional[str] = None, # YYYY-MM
    category: Optional[str] = None,
    limit: int = 50,
    user: User = Depends(get_current_user)
):
    """Get recent transactions, optionally filtered by month or category."""
    query = [Transaction.user_id == user.id]
    
    if month:
        start_date = f"{month}-01"
        # Simple string comparison works for ISO dates
        end_date = f"{month}-31" 
        query.append(Transaction.date >= start_date)
        query.append(Transaction.date <= end_date)
        
    if category:
        query.append(Transaction.category == category)
        
    txns = await Transaction.find(*query).sort(-Transaction.date).limit(limit).to_list()
    return txns

@router.post("/budgets", response_model=Dict[str, str])
async def set_budget(
    budget: BudgetCreate,
    user: User = Depends(get_current_user)
):
    """Set or update a monthly budget for a category."""
    existing = await Budget.find_one(
        Budget.user_id == user.id,
        Budget.month == budget.month,
        Budget.category == budget.category
    )
    
    if existing:
        existing.amount_limit = budget.amount_limit
        existing.is_hard_limit = budget.is_hard_limit
        existing.updated_at = datetime.utcnow()
        await existing.save()
        return {"id": str(existing.id), "status": "updated"}
    else:
        new_budget = Budget(
            user_id=user.id,
            **budget.dict()
        )
        await new_budget.insert()
        return {"id": str(new_budget.id), "status": "created"}

@router.get("/dashboard")
async def get_finance_dashboard(
    month: Optional[str] = None,
    user: User = Depends(get_current_user)
):
    """
    Returns aggregated metrics for the finance dashboard.
    Robust implementation with safe defaults.
    """
    try:
        # Default to current month if not provided
        if not month:
            month = date.today().strftime("%Y-%m")

        # 1. Validate Month Format & Calculate Date Range
        try:
            target_date = datetime.strptime(month, "%Y-%m")
            # Calculate last day of month
            next_month = target_date.replace(day=28) + timedelta(days=4)
            last_day = next_month - timedelta(days=next_month.day)
            
            start_date = f"{month}-01"
            end_date = last_day.strftime("%Y-%m-%d")
        except ValueError:
             log.warning(f"Invalid month format: {month}. Falling back to empty defaults.")
             raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM.")

        # 2. Fetch Transactions (Safe)
        try:
            txns = await Transaction.find(
                Transaction.user_id == user.id,
                Transaction.date >= start_date,
                Transaction.date <= end_date
            ).to_list()
        except Exception as e:
            log.error(f"DB Error fetching transactions: {e}", exc_info=True)
            txns = []

        # 3. Aggregations (Zero-Safe)
        total_income = sum(t.amount for t in txns if t.type == TransactionType.INCOME) or 0.0
        total_expense = sum(t.amount for t in txns if t.type == TransactionType.EXPENSE) or 0.0
        total_invested = sum(t.amount for t in txns if t.type == TransactionType.INVESTMENT) or 0.0
        
        savings = total_income - total_expense
        # Avoid division by zero
        savings_rate = (savings / total_income * 100) if total_income > 0 else 0.0
        
        # 4. Category Breakdown
        category_actuals = {}
        for t in txns:
            if t.type == TransactionType.EXPENSE:
                category_actuals[t.category] = category_actuals.get(t.category, 0) + t.amount

        # 5. Fetch Budgets (Safe)
        try:
            budgets = await Budget.find(
                Budget.user_id == user.id,
                Budget.month == month
            ).to_list()
            budget_map = {b.category: b.amount_limit for b in budgets}
        except Exception as e:
            log.error(f"DB Error fetching budgets: {e}", exc_info=True)
            budget_map = {}
        
        # 6. Build Budget vs Actual List
        budget_vs_actual = []
        all_categories = set(category_actuals.keys()) | set(budget_map.keys())
        
        for cat in all_categories:
            actual = category_actuals.get(cat, 0.0)
            limit = budget_map.get(cat, 0.0)
            status = "ok"
            
            percentage = 0.0
            if limit > 0:
                percentage = (actual / limit) * 100
                if percentage > 100: status = "exceeded"
                elif percentage > 85: status = "warning"
            elif actual > 0:
                # No budget but spending exists -> unexpected
                status = "warning"
                percentage = 100.0 

            budget_vs_actual.append({
                "category": cat,
                "actual": round(actual, 2),
                "budget": round(limit, 2),
                "status": status,
                "percentage": round(percentage, 1)
            })

        # 7. Calculate Total Balance (Lifetime)
        try:
            # Simple aggregation: Sum(Income) - Sum(Expense) for ALL time
            total_inc_all = await Transaction.find(
                Transaction.user_id == user.id, 
                Transaction.type == TransactionType.INCOME
            ).sum(Transaction.amount) or 0.0
            
            total_exp_all = await Transaction.find(
                Transaction.user_id == user.id, 
                Transaction.type == TransactionType.EXPENSE
            ).sum(Transaction.amount) or 0.0
            
            total_balance = total_inc_all - total_exp_all
        except Exception as e:
            log.error(f"Error calculating total balance: {e}")
            total_balance = 0.0
            
        return {
            "month": month,
            "metrics": {
                "total_balance": round(total_balance, 2),
                "total_income": round(total_income, 2),
                "total_expense": round(total_expense, 2),
                "net_savings": round(savings, 2),
                "savings_rate": round(savings_rate, 1),
                "burn_rate": round(total_expense, 2)
            },
            "budget_performance": sorted(budget_vs_actual, key=lambda x: x['actual'], reverse=True),
            "recent_transactions": txns[:5]
        }

    except HTTPException:
        raise
    except Exception as e:
        log.error(f"Critical error in finance dashboard: {e}", exc_info=True)
        # Return safe default instead of 500ing the entire UI
        return {
            "month": month or "Unknown",
            "metrics": {
                "total_balance": 0.0,
                "total_income": 0, "total_expense": 0,
                "net_savings": 0, "savings_rate": 0, "burn_rate": 0
            },
            "budget_performance": [],
            "recent_transactions": []
        }

class BalanceUpdate(BaseModel):
    target_balance: float

@router.post("/balance", response_model=Dict[str, str])
async def set_balance(
    update: BalanceUpdate,
    user: User = Depends(get_current_user)
):
    """
    Sets the user's total balance by creating an adjustment transaction.
    """
    # 1. Calculate current balance (All time)
    total_inc_all = await Transaction.find(
        Transaction.user_id == user.id, 
        Transaction.type == TransactionType.INCOME
    ).sum(Transaction.amount) or 0.0
    
    total_exp_all = await Transaction.find(
        Transaction.user_id == user.id, 
        Transaction.type == TransactionType.EXPENSE
    ).sum(Transaction.amount) or 0.0
    
    current_balance = total_inc_all - total_exp_all
    
    diff = update.target_balance - current_balance
    
    if abs(diff) < 0.01:
        return {"status": "no_change", "message": "Balance is already correct"}
        
    # 2. Create Adjustment Transaction
    is_increase = diff > 0
    txn_type = TransactionType.INCOME if is_increase else TransactionType.EXPENSE
    amount = abs(diff)
    
    adj_txn = Transaction(
        user_id=user.id,
        date=date.today().strftime("%Y-%m-%d"),
        amount=amount,
        type=txn_type,
        category="Balance Adjustment",
        description="Manual Balance Correction",
        is_recurring=False
    )
    await adj_txn.insert()
    
    return {
        "status": "success", 
        "message": f"Balance adjusted by {diff:+.2f}",
        "new_balance": str(update.target_balance)
    }

class TransactionUpdate(BaseModel):
    date: Optional[str] = None
    amount: Optional[float] = Field(None, gt=0)
    type: Optional[TransactionType] = None
    category: Optional[str] = None
    description: Optional[str] = None
    merchant: Optional[str] = None
    tags: Optional[List[str]] = None
    is_recurring: Optional[bool] = None

@router.put("/transactions/{transaction_id}", response_model=Dict[str, str])
async def update_transaction(
    transaction_id: str,
    update: TransactionUpdate,
    user: User = Depends(get_current_user)
):
    """Update an existing transaction."""
    from utils.security import validate_object_id
    tid = validate_object_id(transaction_id)
    
    txn = await Transaction.find_one(
        Transaction.id == tid,
        Transaction.user_id == user.id
    )
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    # Update fields if provided
    update_data = update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(txn, key, value)
        
    await txn.save()
    log.info(f"Transaction updated: id={tid}, user={user.id}")
    return {"id": str(txn.id), "status": "updated"}

@router.delete("/transactions/{transaction_id}", response_model=Dict[str, str])
async def delete_transaction(
    transaction_id: str,
    user: User = Depends(get_current_user)
):
    """Delete a transaction."""
    from utils.security import validate_object_id
    tid = validate_object_id(transaction_id)
    
    txn = await Transaction.find_one(
        Transaction.id == tid,
        Transaction.user_id == user.id
    )
    if not txn:
        raise HTTPException(status_code=404, detail="Transaction not found")
        
    await txn.delete()
    log.info(f"Transaction deleted: id={tid}, user={user.id}")
    return {"id": str(tid), "status": "deleted"}
