from dao.expense_policy_dao import ExpensePolicyDao
from models.expense_policy import ExpensePolicy


class PolicyService:
    """Thin application service for ExpensePolicy persistence."""

    def __init__(self, policy_dao: ExpensePolicyDao):
        self.policy_dao = policy_dao

    def get_by_id(self, policy_id: int) -> ExpensePolicy:
        policy = self.policy_dao.get_policy_by_id(policy_id)
        if policy is None:
            raise ValueError("Expense policy not found")
        return policy
    
    def get_by_category(self, category_id: int) -> list[ExpensePolicy]:
        return self.policy_dao.get_policies_for_category(category_id)

    def get_active_by_category(self, category_id: int) -> ExpensePolicy | None:
        return self.policy_dao.get_active_policy_for_category(category_id)

    def get_active(self) -> list[ExpensePolicy]:
        return self.policy_dao.get_all_active_policies()

    def save(self, data: dict) -> ExpensePolicy:
        policy = ExpensePolicy(
            category_id=data["category_id"],
            max_amount=data.get("max_amount"),
            daily_limit=data.get("daily_limit"),
            requires_receipt=data.get("requires_receipt", True),
            is_active=data.get("is_active", True),
        )
        return self.policy_dao.create_policy(policy)

    def update(self, policy: ExpensePolicy) -> ExpensePolicy | None:
        return self.policy_dao.update_policy(policy)

    def deactivate(self, policy_id: int) -> ExpensePolicy | None:
        return self.policy_dao.deactivate_policy(policy_id)
