import io
import os
import tempfile
import unittest
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

class ClaimServiceTests(unittest.TestCase):
    def setUp(self):
        from services.claim_service import ClaimService

        self.dao = MagicMock()
        self.service = ClaimService(self.dao)

    def test_claim_number_is_generated_by_backend(self):
        self.dao.get_claim_by_travel_request.return_value = None
        self.dao.create_claim.side_effect = lambda claim: claim

        claim = self.service.save({"employee_id": 7, "travel_request_id": 12})

        self.assertRegex(claim.claim_number, r"^CLM-\d{8}-[A-F0-9]{12}$")
        self.assertEqual(claim.travel_request_id, 12)

    def test_only_one_claim_is_allowed_for_a_travel_request(self):
        self.dao.get_claim_by_travel_request.return_value = SimpleNamespace(id=4)

        with self.assertRaisesRegex(ValueError, "already exists"):
            self.service.save({"employee_id": 7, "travel_request_id": 12})

    def test_finance_validation_reports_limit_and_missing_receipt(self):
        item = SimpleNamespace(
            id=8,
            category_id=3,
            amount=Decimal("2500.00"),
            description="Dinner",
            expense_date="2026-08-22",
            receipts=[],
        )
        claim = SimpleNamespace(expense_items=[item])
        policy = SimpleNamespace(max_amount=Decimal("2000.00"), daily_limit=Decimal("3000.00"), requires_receipt=True)

        with patch("services.claim_service.ExpensePolicyDao") as policy_dao:
            policy_dao.return_value.get_active_policy_for_category.return_value = policy
            result = self.service.finance_validation(claim)

        self.assertFalse(result["valid"])
        self.assertEqual(result["valid_amount"], "0")
        self.assertIn("required receipt is missing", result["invalid_items"][0]["reasons"])
        self.assertTrue(any(reason.startswith("exceeds item limit") for reason in result["invalid_items"][0]["reasons"]))

    def test_finance_validation_calculates_valid_reimbursable_amount(self):
        items = [
            SimpleNamespace(id=1, category_id=1, amount=Decimal("800"), description="Hotel", expense_date="2026-08-22", receipts=[object()]),
            SimpleNamespace(id=2, category_id=2, amount=Decimal("300"), description="Taxi", expense_date="2026-08-22", receipts=[object()]),
        ]
        policy = SimpleNamespace(max_amount=Decimal("1000"), daily_limit=Decimal("2000"), requires_receipt=True)

        with patch("services.claim_service.ExpensePolicyDao") as policy_dao:
            policy_dao.return_value.get_active_policy_for_category.return_value = policy
            result = self.service.finance_validation(SimpleNamespace(expense_items=items))

        self.assertTrue(result["valid"])
        self.assertEqual(result["valid_amount"], "1100")


class ExpenseItemServiceTests(unittest.TestCase):
    def test_expense_over_policy_limit_is_rejected(self):
        from services.expense_item_service import ExpenseItemService

        claim = SimpleNamespace(expense_items=[])
        policy = SimpleNamespace(max_amount=Decimal("1000.00"), daily_limit=None)
        claim_dao = MagicMock()
        claim_dao.return_value.get_claim_by_id.return_value = claim
        policy_dao = MagicMock()
        policy_dao.return_value.get_active_policy_for_category.return_value = policy
        item_dao = MagicMock()

        with patch("services.expense_item_service.ExpenseClaimDao", claim_dao), patch(
            "services.expense_item_service.ExpensePolicyDao", policy_dao
        ):
            service = ExpenseItemService(item_dao)
            with self.assertRaisesRegex(ValueError, "policy limit"):
                service.save({
                    "claim_id": 1,
                    "category_id": 2,
                    "description": "Hotel",
                    "amount": 1001,
                    "expense_date": "2026-08-22",
                })

        item_dao.create_item.assert_not_called()

    def test_expense_create_recalculates_claim_total(self):
        from services.expense_item_service import ExpenseItemService

        existing = SimpleNamespace(amount=Decimal("100.00"))
        claim = SimpleNamespace(expense_items=[existing], total_amount=Decimal("0"))
        saved = SimpleNamespace(amount=Decimal("250.00"))
        claim_dao = MagicMock()
        claim_dao.return_value.get_claim_by_id.return_value = claim
        policy_dao = MagicMock()
        policy_dao.return_value.get_active_policy_for_category.return_value = None
        item_dao = MagicMock()
        item_dao.create_item.return_value = saved
        claim.expense_items = [existing, saved]

        with patch("services.expense_item_service.ExpenseClaimDao", claim_dao), patch(
            "services.expense_item_service.ExpensePolicyDao", policy_dao
        ):
            service = ExpenseItemService(item_dao)
            with patch("services.expense_item_service.db"):
                result = service.save({
                    "claim_id": 1,
                    "category_id": 2,
                    "description": "Hotel",
                    "amount": 250,
                    "expense_date": "2026-08-22",
                })

        self.assertIs(result, saved)
        self.assertEqual(claim.total_amount, 350.0)
        claim_dao.return_value.update_claim.assert_called_once_with(claim)


class AuthenticationAndApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from app import app

        cls.app = app
        cls.app.config["TESTING"] = True

    def token(self, role="EMPLOYEE", employee_id=1, user_id=1):
        from controllers.base_controller import create_access_token

        with self.app.app_context():
            user = SimpleNamespace(
                id=user_id,
                email=f"{role.lower()}@test.local",
                role=role,
                employee=SimpleNamespace(id=employee_id),
            )
            return create_access_token(user)

    def test_login_returns_access_token(self):
        from controllers import user_controller

        user = SimpleNamespace(
            id=1,
            email="employee@test.local",
            username="employee",
            role="EMPLOYEE",
            is_active=True,
            employee=SimpleNamespace(id=1),
        )
        with patch.object(user_controller.user_service, "authenticate", return_value=user):
            response = self.app.test_client().post(
                "/api/users/sigin",
                json={"email": "employee@test.local", "password": "secret"},
            )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["access_token"])

    def test_missing_login_fields_returns_bad_request(self):
        response = self.app.test_client().post("/api/users/sigin", json={"email": ""})
        self.assertEqual(response.status_code, 400)
        self.assertIn("required fields", response.get_json()["error"])

    def test_role_protection_returns_forbidden(self):
        token = self.token("EMPLOYEE")
        response = self.app.test_client().get(
            "/api/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        self.assertEqual(response.status_code, 403)

    def test_expired_or_missing_token_returns_unauthorized(self):
        response = self.app.test_client().get("/api/employees/me")
        self.assertEqual(response.status_code, 401)

    def test_employee_can_read_only_their_own_employee_profile(self):
        from controllers import employee_controller
        from models.employee import Employee

        employee = Employee(
            id=1,
            user_id=1,
            employee_code="EMP-000001",
            first_name="Test",
            last_name="Employee",
            department="Engineering",
            designation="Developer",
        )
        with patch.object(employee_controller.employee_service, "get_by_id", return_value=employee):
            token = self.token("EMPLOYEE", employee_id=1)
            allowed = self.app.test_client().get(
                "/api/employees/1",
                headers={"Authorization": f"Bearer {token}"},
            )
            denied = self.app.test_client().get(
                "/api/employees/2",
                headers={"Authorization": f"Bearer {token}"},
            )

        self.assertEqual(allowed.status_code, 200)
        self.assertEqual(denied.status_code, 403)

    def test_receipt_upload_rejects_unauthorized_employee_claim(self):
        from controllers import receipt_controller

        item = SimpleNamespace(claim=SimpleNamespace(employee_id=99))
        with patch.object(receipt_controller.expense_item_service, "get_by_id", return_value=item):
            token = self.token("EMPLOYEE", employee_id=1)
            response = self.app.test_client().post(
                "/api/receipts/upload",
                headers={"Authorization": f"Bearer {token}"},
                data={"expense_item_id": "5", "file": (io.BytesIO(b"file"), "receipt.pdf")},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 403)

    def test_receipt_upload_accepts_supported_pdf_for_claim_owner(self):
        from controllers import receipt_controller
        from models.expense_receipt import ExpenseReceipt

        item = SimpleNamespace(claim=SimpleNamespace(employee_id=1))
        receipt = ExpenseReceipt(id=10, expense_item_id=5, file_name="receipt.pdf", file_path="stored.pdf", file_type="application/pdf", file_size=4, uploaded_by=1)
        with tempfile.TemporaryDirectory() as upload_dir, patch.object(receipt_controller.expense_item_service, "get_by_id", return_value=item), patch.object(receipt_controller.receipt_service, "save", return_value=receipt), patch.object(receipt_controller.current_app, "config", {"RECEIPT_UPLOAD_FOLDER": upload_dir}):
            token = self.token("EMPLOYEE", employee_id=1)
            response = self.app.test_client().post(
                "/api/receipts/upload",
                headers={"Authorization": f"Bearer {token}"},
                data={"expense_item_id": "5", "file": (io.BytesIO(b"file"), "receipt.pdf")},
                content_type="multipart/form-data",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.get_json()["receipt"]["file_name"], "receipt.pdf")


class ApprovalAndDatabaseTests(AuthenticationAndApiTests):
    def test_manager_approval_creates_audit_record(self):
        from controllers import approval_controller
        from models.approval_history import ApprovalHistory

        claim = SimpleNamespace(status="SUBMITTED", id=9, employee=SimpleNamespace(manager_id=1))
        record = ApprovalHistory(id=3, claim_id=9, approver_id=1, action="APPROVE", comment=None)
        with patch.object(approval_controller.claim_service, "get_by_id", return_value=claim), patch.object(approval_controller.approval_service, "save", return_value=record), patch.object(approval_controller.claim_service, "update_status", return_value=claim) as update_status:
            token = self.token("MANAGER", employee_id=1, user_id=1)
            response = self.app.test_client().post(
                "/api/approvals",
                headers={"Authorization": f"Bearer {token}"},
                json={"claim_id": 9, "action": "APPROVE"},
            )

        self.assertEqual(response.status_code, 201)
        update_status.assert_called_once_with(9, "APPROVED")

    def test_finance_rejection_requires_a_comment(self):
        from controllers import approval_controller

        claim = SimpleNamespace(status="APPROVED", id=9)
        with patch.object(approval_controller.claim_service, "get_by_id", return_value=claim):
            token = self.token("FINANCE_ADMIN", employee_id=1)
            response = self.app.test_client().post(
                "/api/approvals",
                headers={"Authorization": f"Bearer {token}"},
                json={"claim_id": 9, "action": "REJECT"},
            )

        self.assertEqual(response.status_code, 400)
        self.assertIn("reason is required", response.get_json()["error"])

    def test_claim_dao_commits_database_create(self):
        from dao.expense_claim_dao import ExpenseClaimDao

        session = MagicMock()
        with patch("dao.expense_claim_dao.db") as database:
            database.session = session
            claim = object()
            self.assertIs(ExpenseClaimDao().create_claim(claim), claim)

        session.add.assert_called_once_with(claim)
        session.commit.assert_called_once_with()


class ApprovalAndReimbursementTests(unittest.TestCase):
    def test_reimbursement_transition_requires_valid_next_state(self):
        from services.reimbursement_service import ReimbursementService

        reimbursement = SimpleNamespace(status="PENDING")
        dao = MagicMock()
        dao.get_reimbursement_by_id.return_value = reimbursement
        service = ReimbursementService(dao)

        with self.assertRaisesRegex(ValueError, "Invalid reimbursement transition"):
            service.update_status(1, "PAID", {"processed_by": 2})

    def test_processing_then_paid_stores_processor_and_timestamp(self):
        from services.reimbursement_service import ReimbursementService

        reimbursement = SimpleNamespace(
            status="PENDING", payment_method=None, transaction_reference=None,
            processed_by=None, processed_at=None,
        )
        dao = MagicMock()
        dao.get_reimbursement_by_id.return_value = reimbursement
        dao.update_reimbursement.side_effect = lambda value: value
        service = ReimbursementService(dao)

        service.update_status(1, "PROCESSING", {"processed_by": 4})
        self.assertEqual(reimbursement.status, "PROCESSING")
        service.update_status(1, "PAID", {"processed_by": 4, "payment_method": "BANK", "transaction_reference": "TX-1"})

        self.assertEqual(reimbursement.status, "PAID")
        self.assertEqual(reimbursement.processed_by, 4)
        self.assertEqual(reimbursement.payment_method, "BANK")
        self.assertIsNotNone(reimbursement.processed_at)


if __name__ == "__main__":
    unittest.main()
