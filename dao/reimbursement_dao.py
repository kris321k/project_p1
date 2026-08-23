from datetime import datetime

from sqlalchemy.exc import SQLAlchemyError

from config.database import db
from models.reimbursement import Reimbursement
from models.expense_claim import ExpenseClaim


class ReimbursementDao:
    """Persistence and finance workflow operations for reimbursements."""

    def create_reimbursement(self, reimbursement: Reimbursement) -> Reimbursement | None:
        try:
            db.session.add(reimbursement)
            db.session.commit()
            return reimbursement
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def get_reimbursement_by_id(self, reimbursement_id: int) -> Reimbursement | None:
        return db.session.get(Reimbursement, reimbursement_id)

    def get_by_claim_id(self, claim_id: int) -> Reimbursement | None:
        return db.session.scalar(
            db.select(Reimbursement).where(Reimbursement.claim_id == claim_id)
        )

    def get_by_employee_id(self, employee_id: int) -> list[Reimbursement]:
        return list(
            db.session.scalars(
                db.select(Reimbursement)
                .join(ExpenseClaim, Reimbursement.claim_id == ExpenseClaim.id)
                .where(ExpenseClaim.employee_id == employee_id)
                .order_by(Reimbursement.created_at.desc())
            )
        )

    def get_by_status(self, status: str) -> list[Reimbursement]:
        return list(
            db.session.scalars(
                db.select(Reimbursement)
                .where(Reimbursement.status == status)
                .order_by(Reimbursement.created_at.asc())
            )
        )

    def get_processed_by_user(self, user_id: int) -> list[Reimbursement]:
        return list(
            db.session.scalars(
                db.select(Reimbursement)
                .where(Reimbursement.processed_by == user_id)
                .order_by(Reimbursement.processed_at.desc())
            )
        )

    def update_reimbursement(self, reimbursement: Reimbursement) -> Reimbursement | None:
        try:
            db.session.commit()
            return reimbursement
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def mark_as_processed(
        self,
        reimbursement_id: int,
        processed_by: int,
        payment_method: str,
        transaction_reference: str,
    ) -> Reimbursement | None:
        reimbursement = self.get_reimbursement_by_id(reimbursement_id)
        if reimbursement is None:
            return None
        reimbursement.status = "PROCESSED"
        reimbursement.processed_by = processed_by
        reimbursement.payment_method = payment_method
        reimbursement.transaction_reference = transaction_reference
        reimbursement.processed_at = datetime.utcnow()
        return self.update_reimbursement(reimbursement)
