# Models package - Import all models to register them with SQLAlchemy
from .user import User, UserRole
from .customer import Customer, Contact
from .product import Product
from .sales import Quote, SalesOrder, QuoteLine, SalesOrderLine
from .invoice import Invoice, InvoiceLine, Payment
from .deposit import Deposit, DepositApplication, CustomerDepositSummary, DepositType, DepositStatus
from .company import CompanySettings, CurrencyType, PrintFormat

# Export all models for easy imports
__all__ = [
    "User", "UserRole",
    "Customer", "Contact", 
    "Product",
    "Quote", "SalesOrder", "QuoteLine", "SalesOrderLine",
    "Invoice", "InvoiceLine", "Payment",
    "Deposit", "DepositApplication", "CustomerDepositSummary", "DepositType", "DepositStatus",
    "CompanySettings", "CurrencyType", "PrintFormat"
]