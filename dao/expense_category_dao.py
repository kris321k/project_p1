from sqlalchemy.exc import SQLAlchemyError

from config.database import db
from models.expense_category import ExpenseCategory


class ExpenseCategoryDao:
    """Persistence operations for administrator-managed expense categories."""

    def create_category(self, category: ExpenseCategory) -> ExpenseCategory | None:
        try:
            db.session.add(category)
            db.session.commit()
            return category
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def get_category_by_id(self, category_id: int) -> ExpenseCategory | None:
        return db.session.get(ExpenseCategory, category_id)

    def get_category_by_name(self, name: str) -> ExpenseCategory | None:
        return db.session.scalar(
            db.select(ExpenseCategory).where(ExpenseCategory.name == name)
        )

    def get_active_categories(self) -> list[ExpenseCategory]:
        return list(
            db.session.scalars(
                db.select(ExpenseCategory)
                .where(ExpenseCategory.is_active.is_(True))
                .order_by(ExpenseCategory.name)
            )
        )

    def get_all_categories(self) -> list[ExpenseCategory]:
        return list(db.session.scalars(db.select(ExpenseCategory).order_by(ExpenseCategory.name)))

    
    def update_category(self, category: ExpenseCategory) -> ExpenseCategory | None:
        try:
            db.session.commit()
            return category
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def deactivate_category(self, category_id: int) -> ExpenseCategory | None:
        category = self.get_category_by_id(category_id)
        if category is None:
            return None
        category.is_active = False
        return self.update_category(category)
