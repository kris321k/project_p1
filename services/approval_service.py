from dao.approval_history_dao import ApprovalHistoryDao
from models.approval_history import ApprovalHistory


class ApprovalService:
    """Thin application service for ApprovalHistory persistence."""

    def __init__(self, approval_history_dao: ApprovalHistoryDao):
        self.approval_history_dao = approval_history_dao

    def get_by_id(self, record_id: int) -> ApprovalHistory:
        record = self.approval_history_dao.get_record_by_id(record_id)
        if record is None:
            raise ValueError("Approval record not found")
        return record

    def get_by_claim(self, claim_id: int) -> list[ApprovalHistory]:
        return self.approval_history_dao.get_claim_history(claim_id)

    def get_by_approver(self, approver_id: int) -> list[ApprovalHistory]:
        return self.approval_history_dao.get_history_by_approver(approver_id)

    def get_latest_by_claim(self, claim_id: int) -> ApprovalHistory | None:
        return self.approval_history_dao.get_latest_for_claim(claim_id)

    def save(self, data: dict) -> ApprovalHistory:
        record = ApprovalHistory(
            claim_id=data["claim_id"],
            approver_id=data["approver_id"],
            action=data["action"],
            comment=data.get("comment"),
        )
        return self.approval_history_dao.create_approval_record(record)
