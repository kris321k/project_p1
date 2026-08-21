from datetime import date

from sqlalchemy.exc import SQLAlchemyError

from config.database import db
from models.employee import Employee
from models.travel_request import TravelRequest


class TravelRequestDao:

    def create_travel_request(self, travel_request: TravelRequest) -> TravelRequest | None:
        try:
            db.session.add(travel_request)
            db.session.commit()
            return travel_request
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def get_travel_request_by_id(self, request_id: int) -> TravelRequest | None:
        return db.session.get(TravelRequest, request_id)

    def get_all_requests(self) -> list[TravelRequest]:
        return list(
            db.session.scalars(
                db.select(TravelRequest).order_by(TravelRequest.created_at.desc())
            )
        )

    def get_employee_requests(self, employee_id: int) -> list[TravelRequest]:
        return list(
            db.session.scalars(
                db.select(TravelRequest)
                .where(TravelRequest.employee_id == employee_id)
                .order_by(TravelRequest.created_at.desc())
            )
        )

    def get_requests_for_manager(self, manager_id: int, status: str | None = None) -> list[TravelRequest]:
        statement = (
            db.select(TravelRequest)
            .join(Employee, TravelRequest.employee_id == Employee.id)
            .where(Employee.manager_id == manager_id)
        )
        if status:
            statement = statement.where(TravelRequest.status == status)
        return list(db.session.scalars(statement.order_by(TravelRequest.created_at.desc())))

    def get_requests_by_status(self, status: str) -> list[TravelRequest]:
        return list(
            db.session.scalars(
                db.select(TravelRequest)
                .where(TravelRequest.status == status)
                .order_by(TravelRequest.created_at.asc())
            )
        )

    def get_upcoming_requests(self, employee_id: int, from_date: date | None = None) -> list[TravelRequest]:
        from_date = from_date or date.today()
        return list(
            db.session.scalars(
                db.select(TravelRequest)
                .where(
                    TravelRequest.employee_id == employee_id,
                    TravelRequest.end_date >= from_date,
                )
                .order_by(TravelRequest.start_date.asc())
            )
        )

    def update_travel_request(self, travel_request: TravelRequest) -> TravelRequest | None:
        try:
            db.session.commit()
            return travel_request
        except SQLAlchemyError:
            db.session.rollback()
            return None

    def update_status(self, request_id: int, status: str, manager_comment: str | None = None) -> TravelRequest | None:
        request = self.get_travel_request_by_id(request_id)
        if request is None:
            return None
        request.status = status
        request.manager_comment = manager_comment
        return self.update_travel_request(request)

    def delete_travel_request(self, travel_request: TravelRequest) -> bool:
        try:
            db.session.delete(travel_request)
            db.session.commit()
            return True
        except SQLAlchemyError:
            db.session.rollback()
            return False
