from dao.reimbursement_dao import ReimbursementDao
from models.reimbursement import Reimbursement


class ReimbursementService:
    """Thin application service for Reimbursement persistence."""

    def __init__(self, reimbursement_dao: ReimbursementDao):
        self.reimbursement_dao = reimbursement_dao

    def get_by_id(self, reimbursement_id: int) -> Reimbursement:
        reimbursement = self.reimbursement_dao.get_reimbursement_by_id(reimbursement_id)
        if reimbursement is None:
            raise ValueError("Reimbursement not found")
        return reimbursement
    
    def get_by_claim(self, claim_id: int) -> Reimbursement | None:
        return self.reimbursement_dao.get_by_claim_id(claim_id)

    def get_by_status(self, status: str) -> list[Reimbursement]:
        return self.reimbursement_dao.get_by_status(status)

    def get_processed_by(self, user_id: int) -> list[Reimbursement]:
        return self.reimbursement_dao.get_processed_by_user(user_id)

    def save(self, data: dict) -> Reimbursement:
        reimbursement = Reimbursement(
            claim_id=data["claim_id"],
            amount=data["amount"],
            payment_method=data.get("payment_method"),
            transaction_reference=data.get("transaction_reference"),
            status=data.get("status", "PENDING"),
            processed_by=data.get("processed_by"),
            processed_at=data.get("processed_at"),
        )
        return self.reimbursement_dao.create_reimbursement(reimbursement)
    
    def update(self, reimbursement: Reimbursement) -> Reimbursement | None:
        return self.reimbursement_dao.update_reimbursement(reimbursement)
    
    def mark_as_processed(self, reimbursement_id: int, processed_by: int,
                          payment_method: str, transaction_reference: str) -> Reimbursement | None:
        return self.reimbursement_dao.mark_as_processed(
            reimbursement_id,
            processed_by,
            payment_method,
            transaction_reference,
        )
    