from dao.expense_receipt_dao import ExpenseReceiptDao
from models.expense_receipt import ExpenseReceipt


class ReceiptService:

    def __init__(self, receipt_dao: ExpenseReceiptDao):
        self.receipt_dao = receipt_dao

    def get_by_id(self, receipt_id: int) -> ExpenseReceipt:
        receipt = self.receipt_dao.get_receipt_by_id(receipt_id)
        if receipt is None:
            raise ValueError("Receipt not found")
        return receipt
    
    def get_by_item(self, expense_item_id: int) -> list[ExpenseReceipt]:
        return self.receipt_dao.get_receipts_by_item(expense_item_id)

    def get_by_uploader(self, user_id: int) -> list[ExpenseReceipt]:
        return self.receipt_dao.get_receipts_uploaded_by(user_id)
    
    def save(self, data: dict) -> ExpenseReceipt:
        receipt = ExpenseReceipt(
            expense_item_id=data["expense_item_id"],
            file_name=data["file_name"],
            file_path=data["file_path"],
            file_type=data["file_type"],
            file_size=data["file_size"],
            uploaded_by=data["uploaded_by"],
        )
        return self.receipt_dao.create_receipt(receipt)
    
    def delete(self, receipt: ExpenseReceipt) -> bool:
        return self.receipt_dao.delete_receipt(receipt)
