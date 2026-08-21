from sqlalchemy.exc import SQLAlchemyError

from config.database import db
from models.expense_receipt import ExpenseReceipt


class ExpenseReceiptDao:

    def create_receipt(self, receipt: ExpenseReceipt) -> ExpenseReceipt | None:
        try:
            db.session.add(receipt)
            db.session.commit()
            return receipt
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def get_receipt_by_id(self, receipt_id: int) -> ExpenseReceipt | None:
        return db.session.get(ExpenseReceipt, receipt_id)

    def get_receipts_by_item(self, expense_item_id: int) -> list[ExpenseReceipt]:
        return list(
            db.session.scalars(
                db.select(ExpenseReceipt)
                .where(ExpenseReceipt.expense_item_id == expense_item_id)
                .order_by(ExpenseReceipt.uploaded_at.desc())
            )
        )

    def get_receipts_uploaded_by(self, user_id: int) -> list[ExpenseReceipt]:
        return list(
            db.session.scalars(
                db.select(ExpenseReceipt)
                .where(ExpenseReceipt.uploaded_by == user_id)
                .order_by(ExpenseReceipt.uploaded_at.desc())
            )
        )

    def delete_receipt(self, receipt: ExpenseReceipt) -> bool:
        try:
            db.session.delete(receipt)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False
