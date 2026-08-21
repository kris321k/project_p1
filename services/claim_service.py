from dao.expense_claim_dao import ExpenseClaimDao
from models.expense_claim import ExpenseClaim
from datetime import datetime


class ClaimService:
    """Thin application service for ExpenseClaim persistence."""

    def __init__(self, claim_dao: ExpenseClaimDao):
        self.claim_dao = claim_dao

    def get_all(self) -> list[ExpenseClaim]:
        return self.claim_dao.get_all_claims()

    def get_by_id(self, claim_id: int) -> ExpenseClaim:
        claim = self.claim_dao.get_claim_by_id(claim_id)
        if claim is None:
            raise ValueError("Expense claim not found")
        return claim

    def get_by_number(self, claim_number: str) -> ExpenseClaim | None:
        return self.claim_dao.get_claim_by_number(claim_number)

    def get_by_employee(self, employee_id: int, status: str | None = None) -> list[ExpenseClaim]:
        return self.claim_dao.get_employee_claims(employee_id, status)

    def get_by_status(self, status: str) -> list[ExpenseClaim]:
        return self.claim_dao.get_claims_by_status(status)

    def get_for_manager(self, manager_id: int, status: str | None = None) -> list[ExpenseClaim]:
        return self.claim_dao.get_claims_for_manager(manager_id, status)

    def search(self, search_term: str, employee_id: int | None = None) -> list[ExpenseClaim]:
        return self.claim_dao.search_claims(search_term, employee_id)

    def save(self, data: dict) -> ExpenseClaim:
        claim = ExpenseClaim(
            employee_id=data["employee_id"],
            travel_request_id=data.get("travel_request_id"),
            claim_number=data["claim_number"],
            total_amount=data.get("total_amount", 0),
            status=data.get("status", "DRAFT"),
            description=data.get("description"),
            submitted_at=data.get("submitted_at"),
        )
        return self.claim_dao.create_claim(claim)

    def update(self, claim: ExpenseClaim) -> ExpenseClaim | None:
        return self.claim_dao.update_claim(claim)

    def update_status(self, claim_id: int, status: str) -> ExpenseClaim | None:
        allowed_statuses = {"DRAFT", "SUBMITTED", "PENDING", "APPROVED", "REJECTED", "VERIFIED", "REIMBURSED"}
        status = status.upper()
        if status not in allowed_statuses:
            raise ValueError("Invalid claim status")
        return self.claim_dao.update_status(claim_id, status)

    def submit(self, claim: ExpenseClaim) -> ExpenseClaim:
        if claim.status not in {"DRAFT", "REJECTED"}:
            raise ValueError("Only draft or rejected claims can be submitted")
        if not claim.expense_items:
            raise ValueError("Add at least one expense item before submitting")
        for item in claim.expense_items:
            policy = item.category.policies[0] if item.category and item.category.policies else None
            if policy and policy.is_active and policy.requires_receipt and not item.receipts:
                raise ValueError(f"A receipt is required for {item.category.name}")
        claim.status = "SUBMITTED"
        claim.submitted_at = datetime.utcnow()
        return self.claim_dao.update_claim(claim)

    def delete(self, claim: ExpenseClaim) -> bool:
        return self.claim_dao.delete_claim(claim)
