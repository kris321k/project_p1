from dao.expense_category_dao import ExpenseCategoryDao
from models.expense_category import ExpenseCategory


class CategoryService:
    """Thin application service for ExpenseCategory persistence."""

    def __init__(self, category_dao: ExpenseCategoryDao):
        self.category_dao = category_dao

    def get_all(self) -> list[ExpenseCategory]:
        return self.category_dao.get_all_categories()

    def get_active(self) -> list[ExpenseCategory]:
        return self.category_dao.get_active_categories()

    def get_by_id(self, category_id: int) -> ExpenseCategory:
        category = self.category_dao.get_category_by_id(category_id)
        if category is None:
            raise ValueError("Expense category not found")
        return category

    def get_by_name(self, name: str) -> ExpenseCategory | None:
        return self.category_dao.get_category_by_name(name)

    def save(self, data: dict) -> ExpenseCategory:
        category = ExpenseCategory(
            name=data["name"],
            description=data.get("description"),
            is_active=data.get("is_active", True),
        )
        return self.category_dao.create_category(category)

    def update(self, category: ExpenseCategory) -> ExpenseCategory | None:
        return self.category_dao.update_category(category)

    def deactivate(self, category_id: int) -> ExpenseCategory | None:
        return self.category_dao.deactivate_category(category_id)
