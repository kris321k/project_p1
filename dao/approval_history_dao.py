from sqlalchemy.exc import SQLAlchemyError

from config.database import db
from models.approval_history import ApprovalHistory


class ApprovalHistoryDao:
    """Append-only audit trail queries for claim approval actions."""

    def create_approval_record(self, record: ApprovalHistory) -> ApprovalHistory | None:
        try:
            db.session.add(record)
            db.session.commit()
            return record
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def get_record_by_id(self, record_id: int) -> ApprovalHistory | None:
        return db.session.get(ApprovalHistory, record_id)

    def get_claim_history(self, claim_id: int) -> list[ApprovalHistory]:
        return list(
            db.session.scalars(
                db.select(ApprovalHistory)
                .where(ApprovalHistory.claim_id == claim_id)
                .order_by(ApprovalHistory.created_at.asc(), ApprovalHistory.id.asc())
            )
        )

    def get_history_by_approver(self, approver_id: int) -> list[ApprovalHistory]:
        return list(
            db.session.scalars(
                db.select(ApprovalHistory)
                .where(ApprovalHistory.approver_id == approver_id)
                .order_by(ApprovalHistory.created_at.desc())
            )
        )

    def get_latest_for_claim(self, claim_id: int) -> ApprovalHistory | None:
        return db.session.scalar(
            db.select(ApprovalHistory)
            .where(ApprovalHistory.claim_id == claim_id)
            .order_by(ApprovalHistory.created_at.desc(), ApprovalHistory.id.desc())
            .limit(1)
        )
