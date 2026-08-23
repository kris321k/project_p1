from sqlalchemy import or_
from sqlalchemy.exc import SQLAlchemyError

from config.database import db
from models.employee import Employee
from models.expense_claim import ExpenseClaim


class ExpenseClaimDao:
    """Persistence and approval-queue queries for expense claims."""

    def create_claim(self, claim: ExpenseClaim) -> ExpenseClaim | None:
        try:
            db.session.add(claim)
            db.session.commit()
            return claim
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def get_claim_by_id(self, claim_id: int) -> ExpenseClaim | None:
        return db.session.get(ExpenseClaim, claim_id)

    def get_all_claims(self) -> list[ExpenseClaim]:
        return list(
            db.session.scalars(
                db.select(ExpenseClaim).order_by(ExpenseClaim.created_at.desc())
            )
        )
    db

    def get_claim_by_number(self, claim_number: str) -> ExpenseClaim | None:
        return db.session.scalar(
            db.select(ExpenseClaim).where(ExpenseClaim.claim_number == claim_number)
        )

    def get_claim_by_travel_request(self, travel_request_id: int) -> ExpenseClaim | None:
        return db.session.scalar(
            db.select(ExpenseClaim).where(ExpenseClaim.travel_request_id == travel_request_id)
        )

    def get_employee_claims(self, employee_id: int, status: str | None = None) -> list[ExpenseClaim]:
        statement = db.select(ExpenseClaim).where(ExpenseClaim.employee_id == employee_id)
        if status:
            statement = statement.where(ExpenseClaim.status == status)
        return list(db.session.scalars(statement.order_by(ExpenseClaim.created_at.desc())))

    def get_claims_by_status(self, status: str) -> list[ExpenseClaim]:
        return list(
            db.session.scalars(
                db.select(ExpenseClaim)
                .where(ExpenseClaim.status == status)
                .order_by(ExpenseClaim.created_at.asc())
            )
        )
    
    def get_claims_for_manager(self, manager_id: int, status: str | None = None) -> list[ExpenseClaim]:
        statement = (
            db.select(ExpenseClaim)
            .join(Employee, ExpenseClaim.employee_id == Employee.id)
            .where(Employee.manager_id == manager_id)
        )
        if status:
            statement = statement.where(ExpenseClaim.status == status)
        return list(db.session.scalars(statement.order_by(ExpenseClaim.created_at.asc())))

    def search_claims(self, search_term: str, employee_id: int | None = None) -> list[ExpenseClaim]:
        pattern = f"%{search_term.strip()}%"
        statement = db.select(ExpenseClaim).where(
            ExpenseClaim.claim_number.ilike(pattern)
        )
        if employee_id is not None:
            statement = statement.where(ExpenseClaim.employee_id == employee_id)
        return list(db.session.scalars(statement.order_by(ExpenseClaim.created_at.desc())))

    def update_claim(self, claim: ExpenseClaim) -> ExpenseClaim | None:
        try:
            db.session.commit()
            return claim
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def update_status(self, claim_id: int, status: str) -> ExpenseClaim | None:
        claim = self.get_claim_by_id(claim_id)
        if claim is None:
            return None
        claim.status = status
        return self.update_claim(claim)

    def delete_claim(self, claim: ExpenseClaim) -> bool:
        try:
            db.session.delete(claim)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False
