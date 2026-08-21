from dao.travel_request_dao import TravelRequestDao
from models.travel_request import TravelRequest


class TravelRequestService:

    def __init__(self, travel_request_dao: TravelRequestDao):
        self.travel_request_dao = travel_request_dao

    def get_all(self) -> list[TravelRequest]:
        return self.travel_request_dao.get_all_requests()

    def get_by_id(self, request_id: int) -> TravelRequest:
        request = self.travel_request_dao.get_travel_request_by_id(request_id)
        if request is None:
            raise ValueError("Travel request not found")
        return request
    
    def get_by_employee(self, employee_id: int) -> list[TravelRequest]:
        return self.travel_request_dao.get_employee_requests(employee_id)

    def get_for_manager(self, manager_id: int, status: str | None = None) -> list[TravelRequest]:
        return self.travel_request_dao.get_requests_for_manager(manager_id, status)
    
    def get_by_status(self, status: str) -> list[TravelRequest]:
        return self.travel_request_dao.get_requests_by_status(status)
    
    def save(self, data: dict) -> TravelRequest:
        request = TravelRequest(
            employee_id=data["employee_id"],
            destination=data["destination"],
            purpose=data["purpose"],
            start_date=data["start_date"],
            end_date=data["end_date"],
            estimated_cost=data["estimated_cost"],
            status=data.get("status", "PENDING"),
            manager_comment=data.get("manager_comment"),
        )

        return self.travel_request_dao.create_travel_request(request)

    def update(self, request: TravelRequest) -> TravelRequest | None:
        return self.travel_request_dao.update_travel_request(request)
    
    def delete(self, request: TravelRequest) -> bool:
        return self.travel_request_dao.delete_travel_request(request)

    def update_status(self, request_id: int, status: str, comment: str | None = None) -> TravelRequest | None:
        return self.travel_request_dao.update_status(request_id, status, comment)
