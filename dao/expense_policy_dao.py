from sqlalchemy.exc import SQLAlchemyError

from config.database import db
from models.expense_policy import ExpensePolicy


class ExpensePolicyDao:
    """Persistence operations for category-level expense policy rules."""

    def create_policy(self, policy: ExpensePolicy) -> ExpensePolicy | None:
        try:
            db.session.add(policy)
            db.session.commit()
            return policy
        except SQLAlchemyError:
            db.session.rollback()
            return None
        
    def get_policy_by_id(self, policy_id: int) -> ExpensePolicy | None:
        return db.session.get(ExpensePolicy, policy_id)
    
    def get_active_policy_for_category(self, category_id: int) -> ExpensePolicy | None:
        return db.session.scalar(
            db.select(ExpensePolicy)
            .where(
                ExpensePolicy.category_id == category_id,
                ExpensePolicy.is_active.is_(True),
            )
            .order_by(ExpensePolicy.updated_at.desc())
        )

    def get_policies_for_category(self, category_id: int) -> list[ExpensePolicy]:
        return list(
            db.session.scalars(
                db.select(ExpensePolicy)
                .where(ExpensePolicy.category_id == category_id)
                .order_by(ExpensePolicy.created_at.desc())
            )
        )
    
    def get_all_active_policies(self) -> list[ExpensePolicy]:
        return list(
            db.session.scalars(
                db.select(ExpensePolicy)
                .where(ExpensePolicy.is_active.is_(True))
                .order_by(ExpensePolicy.category_id)
            )
        )
    
    def update_policy(self, policy: ExpensePolicy) -> ExpensePolicy | None:
        try:
            db.session.commit()
            return policy
        except SQLAlchemyError:
            db.session.rollback()
            return None
        
    def deactivate_policy(self, policy_id: int) -> ExpensePolicy | None:
        policy = self.get_policy_by_id(policy_id)
        if policy is None:
            return None
        policy.is_active = False
        return self.update_policy(policy)
