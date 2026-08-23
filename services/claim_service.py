from dao.expense_claim_dao import ExpenseClaimDao
from models.expense_claim import ExpenseClaim
from datetime import datetime
from decimal import Decimal
import uuid
from dao.expense_policy_dao import ExpensePolicyDao


class ClaimService:

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

    def get_by_travel_request(self, travel_request_id: int) -> ExpenseClaim | None:
        return self.claim_dao.get_claim_by_travel_request(travel_request_id)

    def get_by_employee(self, employee_id: int, status: str | None = None) -> list[ExpenseClaim]:
        return self.claim_dao.get_employee_claims(employee_id, status)

    def get_by_status(self, status: str) -> list[ExpenseClaim]:
        return self.claim_dao.get_claims_by_status(status)

    def get_for_manager(self, manager_id: int, status: str | None = None) -> list[ExpenseClaim]:
        return self.claim_dao.get_claims_for_manager(manager_id, status)

    def search(self, search_term: str, employee_id: int | None = None) -> list[ExpenseClaim]:
        return self.claim_dao.search_claims(search_term, employee_id)

    def save(self, data: dict) -> ExpenseClaim:
        travel_request_id = data.get("travel_request_id")
        if travel_request_id is not None and self.get_by_travel_request(travel_request_id):
            raise ValueError("A claim already exists for this travel request")
        claim = ExpenseClaim(
            employee_id=data["employee_id"],
            travel_request_id=travel_request_id,
            claim_number=f"CLM-{datetime.utcnow():%Y%m%d}-{uuid.uuid4().hex[:12].upper()}",
            total_amount=data.get("total_amount", 0),
            status=data.get("status", "DRAFT"),
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

    def finance_validation(self, claim: ExpenseClaim) -> dict:
        invalid_items = []
        valid_amount = Decimal("0")
        daily_totals = {}
        for item in claim.expense_items:
            policy = ExpensePolicyDao().get_active_policy_for_category(item.category_id)
            amount = Decimal(str(item.amount))
            reasons = []
            if policy and policy.max_amount is not None and amount > Decimal(str(policy.max_amount)):
                reasons.append(f"exceeds item limit of {policy.max_amount}")
            if policy and policy.requires_receipt and not item.receipts:
                reasons.append("required receipt is missing")
            daily_key = (item.category_id, item.expense_date)
            daily_totals[daily_key] = daily_totals.get(daily_key, Decimal("0")) + amount
            if policy and policy.daily_limit is not None and daily_totals[daily_key] > Decimal(str(policy.daily_limit)):
                reasons.append(f"exceeds daily limit of {policy.daily_limit}")
            if reasons:
                invalid_items.append({"item_id": item.id, "description": item.description, "amount": str(amount), "reasons": reasons})
            else:
                valid_amount += amount
        return {"valid": not invalid_items, "valid_amount": str(valid_amount), "invalid_items": invalid_items}

    def submit(self, claim: ExpenseClaim) -> ExpenseClaim:
        if claim.status not in {"DRAFT", "REJECTED"}:
            raise ValueError("Only draft or rejected claims can be submitted")
        if not claim.expense_items:
            raise ValueError("Add at least one expense item before submitting")
        for item in claim.expense_items:
            policy = ExpensePolicyDao().get_active_policy_for_category(item.category_id)
            if policy and policy.is_active and policy.requires_receipt and not item.receipts:
                raise ValueError(f"A receipt is required for {item.category.name}")
        claim.status = "SUBMITTED"
        claim.submitted_at = datetime.utcnow()
        return self.claim_dao.update_claim(claim)

    def delete(self, claim: ExpenseClaim) -> bool:
        return self.claim_dao.delete_claim(claim)
