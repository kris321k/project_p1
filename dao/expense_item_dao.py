from sqlalchemy.exc import SQLAlchemyError

from config.database import db
from models.expense_item import ExpenseItem


class ExpenseItemDao:
    """Persistence operations for line items belonging to an expense claim."""

    def create_item(self, item: ExpenseItem) -> ExpenseItem | None:
        try:
            db.session.add(item)
            db.session.commit()
            return item
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def get_item_by_id(self, item_id: int) -> ExpenseItem | None:
        return db.session.get(ExpenseItem, item_id)

    def get_items_by_claim(self, claim_id: int) -> list[ExpenseItem]:
        return list(
            db.session.scalars(
                db.select(ExpenseItem)
                .where(ExpenseItem.claim_id == claim_id)
                .order_by(ExpenseItem.expense_date.desc(), ExpenseItem.id.desc())
            )
        )

    def get_items_by_category(self, category_id: int) -> list[ExpenseItem]:
        return list(
            db.session.scalars(
                db.select(ExpenseItem)
                .where(ExpenseItem.category_id == category_id)
                .order_by(ExpenseItem.expense_date.desc())
            )
        )

    def update_item(self, item: ExpenseItem) -> ExpenseItem | None:
        try:
            db.session.commit()
            return item
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def delete_item(self, item: ExpenseItem) -> bool:
        try:
            db.session.delete(item)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False
