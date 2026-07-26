"""记账本 CRUD API"""
import logging
from typing import Optional
from datetime import datetime
from zoneinfo import ZoneInfo
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from db.database import get_connection

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/expenses", tags=["expenses"])


class ExpenseCreate(BaseModel):
    amount: float = Field(..., description="金额")
    category: str = Field(..., description="分类：餐饮/交通/购物/娱乐/其他")
    description: str = ""
    date: str = Field("", description="日期 YYYY-MM-DD，默认今天")


class ExpenseQuery(BaseModel):
    days: int = 7
    category: Optional[str] = None
    limit: int = 50


@router.get("")
async def list_expenses(
    days: int = Query(7, description="查询最近多少天"),
    category: Optional[str] = Query(None, description="分类筛选"),
    limit: int = Query(50, description="最大返回条数"),
):
    """获取账单列表"""
    conn = get_connection()
    from datetime import timedelta
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    cutoff = (now - timedelta(days=days)).strftime("%Y-%m-%d")

    if category:
        rows = conn.execute(
            """SELECT * FROM expenses
               WHERE date >= ? AND category = ?
               ORDER BY date DESC, created_at DESC LIMIT ?""",
            (cutoff, category, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM expenses WHERE date >= ? ORDER BY date DESC, created_at DESC LIMIT ?",
            (cutoff, limit),
        ).fetchall()

    expenses = [dict(r) for r in rows]

    # 统计
    total = sum(e["amount"] for e in expenses)
    by_category = {}
    for e in expenses:
        by_category[e["category"]] = by_category.get(e["category"], 0) + e["amount"]

    return {
        "expenses": expenses,
        "count": len(expenses),
        "total": round(total, 2),
        "by_category": by_category,
        "period": f"最近{days}天",
    }


@router.post("")
async def create_expense(expense: ExpenseCreate):
    """记一笔账"""
    conn = get_connection()
    date = expense.date or datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d")

    cur = conn.execute(
        "INSERT INTO expenses (amount, category, description, date) VALUES (?, ?, ?, ?)",
        (expense.amount, expense.category, expense.description, date),
    )
    conn.commit()
    expense_id = cur.lastrowid
    logger.info(f"记账 #{expense_id}: {expense.category} {expense.amount}元")
    return {"success": True, "id": expense_id}


@router.get("/summary")
async def expense_summary(
    month: Optional[str] = Query(None, description="月份 YYYY-MM，默认本月"),
):
    """月度账单汇总"""
    conn = get_connection()
    now = datetime.now(ZoneInfo("Asia/Shanghai"))
    month = month or now.strftime("%Y-%m")

    rows = conn.execute(
        """SELECT category, SUM(amount) as total, COUNT(*) as count
           FROM expenses
           WHERE date LIKE ?
           GROUP BY category
           ORDER BY total DESC""",
        (f"{month}%",),
    ).fetchall()

    grand_total = conn.execute(
        "SELECT SUM(amount) as total FROM expenses WHERE date LIKE ?",
        (f"{month}%",),
    ).fetchone()

    return {
        "month": month,
        "categories": [dict(r) for r in rows],
        "grand_total": round(grand_total["total"] or 0, 2),
    }


@router.delete("/{expense_id}")
async def delete_expense(expense_id: int):
    """删除一笔账"""
    conn = get_connection()
    cur = conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="账单不存在")
    return {"success": True}
