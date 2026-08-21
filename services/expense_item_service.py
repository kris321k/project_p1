from dao.expense_item_dao import ExpenseItemDao
from dao.expense_claim_dao import ExpenseClaimDao
from dao.expense_policy_dao import ExpensePolicyDao
from config.database import db
from models.expense_item import ExpenseItem


class ExpenseItemService:
    """Thin application service for ExpenseItem persistence."""

    def __init__(self, expense_item_dao: ExpenseItemDao):
        self.expense_item_dao = expense_item_dao

    def get_by_id(self, item_id: int) -> ExpenseItem:
        item = self.expense_item_dao.get_item_by_id(item_id)
        if item is None:
            raise ValueError("Expense item not found")
        return item

    def get_by_claim(self, claim_id: int) -> list[ExpenseItem]:
        return self.expense_item_dao.get_items_by_claim(claim_id)

    def get_by_category(self, category_id: int) -> list[ExpenseItem]:
        return self.expense_item_dao.get_items_by_category(category_id)

    def save(self, data: dict) -> ExpenseItem:
        claim = ExpenseClaimDao().get_claim_by_id(data["claim_id"])
        if claim is None:
            raise ValueError("Expense claim not found")
        policy = ExpensePolicyDao().get_active_policy_for_category(data["category_id"])
        amount = float(data["amount"])
        if policy and policy.max_amount is not None and amount > float(policy.max_amount):
            raise ValueError("Expense amount exceeds the category policy limit")
        if policy and policy.daily_limit is not None:
            existing = db.session.scalars(
                db.select(ExpenseItem).where(
                    ExpenseItem.category_id == data["category_id"],
                    ExpenseItem.expense_date == data["expense_date"],
                )
            )
            daily_total = sum(float(item.amount) for item in existing)
            if daily_total + amount > float(policy.daily_limit):
                raise ValueError("Expense exceeds the daily category policy limit")
        item = ExpenseItem(
            claim_id=data["claim_id"],
            category_id=data["category_id"],
            description=data["description"],
            amount=data["amount"],
            expense_date=data["expense_date"],
            merchant=data.get("merchant"),
        )
        saved = self.expense_item_dao.create_item(item)
        if saved is not None:
            claim.total_amount = sum(float(expense.amount) for expense in claim.expense_items)
            ExpenseClaimDao().update_claim(claim)
        return saved

    def update(self, item: ExpenseItem) -> ExpenseItem | None:
        saved = self.expense_item_dao.update_item(item)
        if saved is not None:
            self._refresh_claim_total(saved.claim_id)
        return saved

    def delete(self, item: ExpenseItem) -> bool:
        claim_id = item.claim_id
        deleted = self.expense_item_dao.delete_item(item)
        if deleted:
            self._refresh_claim_total(claim_id)
        return deleted

    def _refresh_claim_total(self, claim_id: int) -> None:
        claim = ExpenseClaimDao().get_claim_by_id(claim_id)
        if claim is not None:
            claim.total_amount = sum(float(expense.amount) for expense in claim.expense_items)
            ExpenseClaimDao().update_claim(claim)