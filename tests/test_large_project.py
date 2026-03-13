"""Large multi-file integration tests demonstrating AutoDocGen on a realistic codebase."""
import pytest
from pathlib import Path
from unittest.mock import patch
from click.testing import CliRunner
from autodocgen.cli import main
from autodocgen.generator import AIDocGenerator
from autodocgen.parser import parse_file, CodeModule


# ---------------------------------------------------------------------------
# Shared fixture: a synthetic "large" project with 6 modules across packages
# ---------------------------------------------------------------------------

@pytest.fixture
def large_project(tmp_path):
    """Create a realistic multi-module Python project for stress testing."""

    # ---- models/user.py ----
    models_dir = tmp_path / "models"
    models_dir.mkdir()
    (models_dir / "__init__.py").write_text('"""Models package."""\n')
    (models_dir / "user.py").write_text('''"""User domain models."""
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime


@dataclass
class Address:
    """Represents a physical mailing address."""
    street: str
    city: str
    country: str
    postal_code: str

    def format(self) -> str:
        """Return a formatted single-line address."""
        return f"{self.street}, {self.city}, {self.postal_code}, {self.country}"


@dataclass
class User:
    """Represents an application user account.

    Stores profile information, authentication state,
    and a history of login timestamps.
    """
    id: int
    username: str
    email: str
    is_active: bool = True
    addresses: List[Address] = field(default_factory=list)
    created_at: Optional[datetime] = None
    last_login: Optional[datetime] = None

    def display_name(self) -> str:
        """Return the formatted display name for UI rendering."""
        return f"@{self.username}"

    def deactivate(self):
        """Deactivate this user account."""
        self.is_active = False

    def add_address(self, address: Address):
        """Append a new address to this user's address book."""
        self.addresses.append(address)

    def primary_address(self) -> Optional[Address]:
        """Return the first address if available, else None."""
        return self.addresses[0] if self.addresses else None


def create_guest_user(session_id: str) -> User:
    """Factory function to create an anonymous guest user.

    Args:
        session_id: A unique session identifier used as the username.

    Returns:
        A new User instance with is_active=True and no email.
    """
    return User(id=-1, username=f"guest_{session_id}", email="")
''')

    # ---- models/product.py ----
    (models_dir / "product.py").write_text('''"""Product catalog models."""
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class Category(Enum):
    """Product category classification."""
    ELECTRONICS = "electronics"
    CLOTHING = "clothing"
    FOOD = "food"
    BOOKS = "books"
    OTHER = "other"


@dataclass
class Review:
    """A customer review for a product."""
    author: str
    rating: int
    comment: str

    def is_positive(self) -> bool:
        """Return True if the rating is 4 or above."""
        return self.rating >= 4


@dataclass
class Product:
    """Represents a product in the catalog.

    Includes pricing, inventory, categorization,
    and an accumulated list of customer reviews.
    """
    id: int
    name: str
    price: float
    category: Category
    stock: int = 0
    description: str = ""
    reviews: List[Review] = field(default_factory=list)

    def is_available(self) -> bool:
        """Return True if the product is in stock."""
        return self.stock > 0

    def average_rating(self) -> Optional[float]:
        """Calculate the mean rating from all reviews.

        Returns None if no reviews exist.
        """
        if not self.reviews:
            return None
        return sum(r.rating for r in self.reviews) / len(self.reviews)

    def add_review(self, review: Review):
        """Append a customer review to this product."""
        self.reviews.append(review)

    def apply_discount(self, percent: float) -> float:
        """Return the discounted price without modifying the product.

        Args:
            percent: Discount percentage (0-100).

        Returns:
            The new price after discount.
        """
        return self.price * (1 - percent / 100)


def search_by_category(products: List[Product], category: Category) -> List[Product]:
    """Filter a list of products by category.

    Args:
        products: The full catalog list.
        category: The category to filter on.

    Returns:
        A list of matching Product instances.
    """
    return [p for p in products if p.category == category]
''')

    # ---- services/order_service.py ----
    services_dir = tmp_path / "services"
    services_dir.mkdir()
    (services_dir / "__init__.py").write_text('"""Services package."""\n')
    (services_dir / "order_service.py").write_text('''"""Order processing service."""
from typing import List, Optional, Dict
from models.user import User
from models.product import Product


class OrderItem:
    """A line item within an order."""

    def __init__(self, product: Product, quantity: int):
        """Initialise an order item.

        Args:
            product: The product being ordered.
            quantity: Number of units.
        """
        self.product = product
        self.quantity = quantity

    def subtotal(self) -> float:
        """Return price * quantity for this line item."""
        return self.product.price * self.quantity


class Order:
    """Represents a customer purchase order.

    Tracks the buyer, a collection of line items,
    fulfilment status, and total cost.
    """

    STATUSES = ("pending", "confirmed", "shipped", "delivered", "cancelled")

    def __init__(self, order_id: int, user: User):
        self.order_id = order_id
        self.user = user
        self.items: List[OrderItem] = []
        self.status: str = "pending"
        self.discount_percent: float = 0.0

    def add_item(self, product: Product, quantity: int = 1):
        """Add a product to this order.

        Args:
            product: Product to add.
            quantity: Units to order (default 1).

        Raises:
            ValueError: If quantity is less than 1.
        """
        if quantity < 1:
            raise ValueError("Quantity must be at least 1")
        self.items.append(OrderItem(product, quantity))

    def total(self) -> float:
        """Compute the order total after applying any discount."""
        raw = sum(item.subtotal() for item in self.items)
        return raw * (1 - self.discount_percent / 100)

    def cancel(self):
        """Cancel this order if it has not already shipped."""
        if self.status in ("shipped", "delivered"):
            raise RuntimeError("Cannot cancel a shipped or delivered order.")
        self.status = "cancelled"

    def item_count(self) -> int:
        """Return the total number of individual units across all line items."""
        return sum(item.quantity for item in self.items)


class OrderService:
    """Manages the lifecycle of customer orders.

    Provides creation, retrieval, and status-update operations.
    All orders are kept in-memory for this implementation.
    """

    def __init__(self):
        self._orders: Dict[int, Order] = {}
        self._next_id: int = 1

    def create_order(self, user: User) -> Order:
        """Create and persist a new empty order for the given user.

        Args:
            user: The buyer.

        Returns:
            A newly created Order instance.
        """
        order = Order(self._next_id, user)
        self._orders[self._next_id] = order
        self._next_id += 1
        return order

    def get_order(self, order_id: int) -> Optional[Order]:
        """Retrieve an order by its ID.

        Returns None if not found.
        """
        return self._orders.get(order_id)

    def update_status(self, order_id: int, status: str):
        """Update the status of an existing order.

        Args:
            order_id: ID of the order to update.
            status: New status string; must be one of Order.STATUSES.

        Raises:
            KeyError: If the order_id does not exist.
            ValueError: If the status string is invalid.
        """
        if order_id not in self._orders:
            raise KeyError(f"Order {order_id} not found")
        if status not in Order.STATUSES:
            raise ValueError(f"Invalid status: {status}")
        self._orders[order_id].status = status

    def list_orders_for_user(self, user: User) -> List[Order]:
        """Return all orders belonging to the given user."""
        return [o for o in self._orders.values() if o.user.id == user.id]
''')

    # ---- services/inventory_service.py ----
    (services_dir / "inventory_service.py").write_text('''"""Inventory management service."""
from typing import Dict, List
from models.product import Product


class StockAlert:
    """Represents a low-stock alert for a product."""

    def __init__(self, product: Product, threshold: int):
        self.product = product
        self.threshold = threshold

    def is_triggered(self) -> bool:
        """Return True if current stock is at or below threshold."""
        return self.product.stock <= self.threshold

    def message(self) -> str:
        """Return a human-readable alert description."""
        return (
            f"LOW STOCK: {self.product.name} has {self.product.stock} units "
            f"(threshold: {self.threshold})"
        )


class InventoryService:
    """Tracks and manages product stock levels.

    Supports stock adjustments, reservation, and low-stock alerting.
    """

    DEFAULT_THRESHOLD = 10

    def __init__(self, products: List[Product] = None):
        self._products: Dict[int, Product] = {p.id: p for p in (products or [])}
        self._alerts: Dict[int, StockAlert] = {}

    def register(self, product: Product, alert_threshold: int = None):
        """Register a product with the inventory system.

        Args:
            product: The product to track.
            alert_threshold: Minimum stock level before an alert fires.
                             Defaults to InventoryService.DEFAULT_THRESHOLD.
        """
        self._products[product.id] = product
        threshold = alert_threshold if alert_threshold is not None else self.DEFAULT_THRESHOLD
        self._alerts[product.id] = StockAlert(product, threshold)

    def restock(self, product_id: int, quantity: int):
        """Increase the stock level of a product.

        Args:
            product_id: The ID of the product to restock.
            quantity: Units to add.

        Raises:
            KeyError: If the product is not registered.
            ValueError: If quantity is not positive.
        """
        if product_id not in self._products:
            raise KeyError(f"Product {product_id} is not registered")
        if quantity <= 0:
            raise ValueError("Restock quantity must be positive")
        self._products[product_id].stock += quantity

    def reserve(self, product_id: int, quantity: int) -> bool:
        """Attempt to reserve stock for a purchase.

        Args:
            product_id: The product to reserve.
            quantity: Units requested.

        Returns:
            True if reservation succeeded, False if insufficient stock.
        """
        product = self._products.get(product_id)
        if product is None or product.stock < quantity:
            return False
        product.stock -= quantity
        return True

    def get_low_stock_alerts(self) -> List[StockAlert]:
        """Return all currently triggered low-stock alerts."""
        return [a for a in self._alerts.values() if a.is_triggered()]

    def stock_level(self, product_id: int) -> int:
        """Return the current stock level for a given product.

        Raises:
            KeyError: If the product is not registered.
        """
        if product_id not in self._products:
            raise KeyError(f"Product {product_id} not registered")
        return self._products[product_id].stock
''')

    # ---- utils/validators.py ----
    utils_dir = tmp_path / "utils"
    utils_dir.mkdir()
    (utils_dir / "__init__.py").write_text('"""Utility package."""\n')
    (utils_dir / "validators.py").write_text('''"""Input validation utilities."""
import re
from typing import List


EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\\+?[1-9]\\d{7,14}$")


class ValidationError(Exception):
    """Raised when input validation fails."""

    def __init__(self, field: str, message: str):
        self.field = field
        self.message = message
        super().__init__(f"{field}: {message}")


def validate_email(email: str) -> bool:
    """Check whether an email address is syntactically valid.

    Args:
        email: The email address string to validate.

    Returns:
        True if valid, False otherwise.
    """
    return bool(EMAIL_REGEX.match(email.strip()))


def validate_phone(phone: str) -> bool:
    """Check whether a phone number follows E.164 format.

    Args:
        phone: The phone number string (may start with +).

    Returns:
        True if valid, False otherwise.
    """
    return bool(PHONE_REGEX.match(phone.strip()))


def require_non_empty(value: str, field_name: str) -> str:
    """Assert that a string value is not empty.

    Args:
        value: The string to check.
        field_name: The field label used in the ValidationError message.

    Returns:
        The stripped value if non-empty.

    Raises:
        ValidationError: If the value is empty after stripping.
    """
    stripped = value.strip()
    if not stripped:
        raise ValidationError(field_name, "must not be empty")
    return stripped


def validate_price(price: float) -> float:
    """Validate that a price value is positive and finite.

    Args:
        price: The price to validate.

    Returns:
        The price if valid.

    Raises:
        ValidationError: If the price is non-positive or not finite.
    """
    import math
    if not math.isfinite(price) or price <= 0:
        raise ValidationError("price", f"must be a positive finite number, got {price}")
    return price


def batch_validate_emails(emails: List[str]) -> dict:
    """Validate a list of email addresses in one call.

    Args:
        emails: A list of email strings.

    Returns:
        A dict mapping each email to True (valid) or False (invalid).
    """
    return {email: validate_email(email) for email in emails}
''')

    # ---- utils/formatters.py ----
    (utils_dir / "formatters.py").write_text('''"""Output formatting helpers."""
from typing import Any, List


def currency(amount: float, symbol: str = "$", decimals: int = 2) -> str:
    """Format a numeric amount as a currency string.

    Args:
        amount: The monetary value.
        symbol: Currency prefix symbol (default "$").
        decimals: Number of decimal places (default 2).

    Returns:
        Formatted string, e.g. "$12.50".
    """
    return f"{symbol}{amount:.{decimals}f}"


def truncate(text: str, max_length: int = 80, suffix: str = "...") -> str:
    """Truncate a string to max_length characters, appending suffix if cut.

    Args:
        text: The input string.
        max_length: Maximum character count including the suffix.
        suffix: The suffix appended when truncation occurs.

    Returns:
        The original string if short enough, otherwise truncated + suffix.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix


def table(headers: List[str], rows: List[List[Any]], col_width: int = 20) -> str:
    """Render a simple fixed-width text table.

    Args:
        headers: Column header labels.
        rows: List of row data lists (each matched to headers by index).
        col_width: Character width of each column.

    Returns:
        A multi-line string with a header row, separator, and data rows.
    """
    sep = "+" + (("-" * col_width + "+") * len(headers))
    fmt_row = lambda cells: "|" + "".join(str(c).ljust(col_width) + "|" for c in cells)
    lines = [sep, fmt_row(headers), sep]
    for row in rows:
        lines.append(fmt_row(row))
    lines.append(sep)
    return "\\n".join(lines)


async def async_format_report(items: List[dict], title: str = "Report") -> str:
    """Asynchronously assemble a formatted report string.

    This is an async function to demonstrate async parsing support.

    Args:
        items: List of dicts with at least a 'name' and 'value' key.
        title: Report heading.

    Returns:
        A multi-line report string.
    """
    lines = [f"# {title}", ""]
    for item in items:
        lines.append(f"- {item.get('name', 'N/A')}: {item.get('value', '')}")
    return "\\n".join(lines)
''')

    return tmp_path


# ---------------------------------------------------------------------------
# Parser-level tests on the large project
# ---------------------------------------------------------------------------

class TestParserOnLargeProject:
    """Verify the parser extracts the correct structure from each module."""

    def test_user_module(self, large_project):
        mod = parse_file(large_project / "models" / "user.py")
        assert mod.module_name == "user"
        assert mod.docstring == "User domain models."
        class_names = {c.name for c in mod.classes}
        assert "User" in class_names
        assert "Address" in class_names
        user_cls = next(c for c in mod.classes if c.name == "User")
        method_names = {m.name for m in user_cls.methods}
        assert {"display_name", "deactivate", "add_address", "primary_address"}.issubset(method_names)
        func_names = {f.name for f in mod.functions}
        assert "create_guest_user" in func_names

    def test_product_module(self, large_project):
        mod = parse_file(large_project / "models" / "product.py")
        class_names = {c.name for c in mod.classes}
        assert "Product" in class_names
        assert "Review" in class_names
        assert "Category" in class_names
        product_cls = next(c for c in mod.classes if c.name == "Product")
        method_names = {m.name for m in product_cls.methods}
        assert {"is_available", "average_rating", "add_review", "apply_discount"}.issubset(method_names)
        func_names = {f.name for f in mod.functions}
        assert "search_by_category" in func_names

    def test_order_service_module(self, large_project):
        mod = parse_file(large_project / "services" / "order_service.py")
        class_names = {c.name for c in mod.classes}
        assert {"Order", "OrderItem", "OrderService"}.issubset(class_names)
        order_svc = next(c for c in mod.classes if c.name == "OrderService")
        method_names = {m.name for m in order_svc.methods}
        assert {"create_order", "get_order", "update_status", "list_orders_for_user"}.issubset(method_names)

    def test_inventory_service_module(self, large_project):
        mod = parse_file(large_project / "services" / "inventory_service.py")
        inv = next(c for c in mod.classes if c.name == "InventoryService")
        method_names = {m.name for m in inv.methods}
        assert {"register", "restock", "reserve", "get_low_stock_alerts", "stock_level"}.issubset(method_names)

    def test_validators_module(self, large_project):
        mod = parse_file(large_project / "utils" / "validators.py")
        func_names = {f.name for f in mod.functions}
        assert {"validate_email", "validate_phone", "require_non_empty", "validate_price", "batch_validate_emails"}.issubset(func_names)
        class_names = {c.name for c in mod.classes}
        assert "ValidationError" in class_names

    def test_formatters_async_function(self, large_project):
        """The async function in formatters.py must be detected correctly."""
        mod = parse_file(large_project / "utils" / "formatters.py")
        func_names = {f.name for f in mod.functions}
        assert {"currency", "truncate", "table", "async_format_report"}.issubset(func_names)
        async_fn = next(f for f in mod.functions if f.name == "async_format_report")
        assert async_fn.is_async is True


# ---------------------------------------------------------------------------
# End-to-end CLI test on the large project
# ---------------------------------------------------------------------------

def _make_ai_response(content="AI-generated docs for this element."):
    from unittest.mock import MagicMock
    choice = MagicMock()
    choice.message.content = content
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def test_cli_large_project_end_to_end(large_project, tmp_path, monkeypatch):
    """Full pipeline test on a 6-module project with mocked AI."""
    output_dir = tmp_path / "docs_output"
    output_dir.mkdir()
    monkeypatch.setenv("OPENAI_API_KEY", "dummy-key")

    call_log = []

    def mock_class_docs(self, class_name, bases, methods, existing_doc):
        call_log.append(("class", class_name))
        return f"**{class_name}** — AI generated class documentation."

    def mock_function_docs(self, func_name, args, returns, existing_doc):
        call_log.append(("function", func_name))
        return f"**{func_name}** — AI generated function documentation."

    monkeypatch.setattr(AIDocGenerator, "generate_class_docs", mock_class_docs)
    monkeypatch.setattr(AIDocGenerator, "generate_function_docs", mock_function_docs)

    runner = CliRunner()
    result = runner.invoke(main, [
        str(large_project),
        "--output", str(output_dir),
        "--verbose",
    ], catch_exceptions=False)

    assert result.exit_code == 0, f"CLI failed:\n{result.output}"
    assert "Documentation generated in" in result.output

    # All six modules should produce output files
    expected_files = [
        "user.md", "product.md",
        "order_service.md", "inventory_service.md",
        "validators.md", "formatters.md",
        "index.md",
    ]
    for fname in expected_files:
        assert (output_dir / fname).exists(), f"Missing output file: {fname}"

    # Spot-check content quality
    user_md = (output_dir / "user.md").read_text()
    assert "User" in user_md
    assert "Address" in user_md
    assert "create_guest_user" in user_md
    assert "AI generated" in user_md

    product_md = (output_dir / "product.md").read_text()
    assert "Product" in product_md
    assert "apply_discount" in product_md

    order_md = (output_dir / "order_service.md").read_text()
    assert "OrderService" in order_md
    assert "OrderItem" in order_md

    formatters_md = (output_dir / "formatters.md").read_text()
    assert "async_format_report" in formatters_md
    assert "async" in formatters_md  # async prefix should appear

    index_md = (output_dir / "index.md").read_text()
    assert "user" in index_md
    assert "order_service" in index_md
    assert "validators" in index_md

    # Verify AI was called for a representative set
    called_classes = {name for kind, name in call_log if kind == "class"}
    called_functions = {name for kind, name in call_log if kind == "function"}
    assert "User" in called_classes
    assert "Product" in called_classes
    assert "OrderService" in called_classes
    assert "InventoryService" in called_classes
    assert "ValidationError" in called_classes
    assert "create_guest_user" in called_functions
    assert "search_by_category" in called_functions
    assert "validate_email" in called_functions
    assert "currency" in called_functions
    assert "async_format_report" in called_functions

    total_ai_calls = len(call_log)
    # We have 11 classes + 14 functions across 6 modules = 25 calls minimum
    assert total_ai_calls >= 20, f"Expected at least 20 AI calls, got {total_ai_calls}"


# ---------------------------------------------------------------------------
# Negative / edge-case tests
# ---------------------------------------------------------------------------

def test_cli_syntax_error_file(tmp_path, monkeypatch):
    """A file with a syntax error should be skipped but others succeed."""
    (tmp_path / "good.py").write_text('"""Good module."""\ndef hello(): pass\n')
    (tmp_path / "bad.py").write_text('def broken syntax !!! ==\n')
    output_dir = tmp_path / "docs"
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    def mock_fn(self, func_name, args, returns, existing_doc):
        return "OK"

    monkeypatch.setattr(AIDocGenerator, "generate_function_docs", mock_fn)

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--output", str(output_dir)], catch_exceptions=False)
    # Exit code 1 because of parse errors, but good.md should still exist
    assert (output_dir / "good.md").exists()


def test_cli_empty_module(tmp_path, monkeypatch):
    """A .py file with no classes or functions should still produce a .md file."""
    (tmp_path / "constants.py").write_text('"""Just constants."""\nTIMEOUT = 30\nMAX_RETRIES = 3\n')
    output_dir = tmp_path / "docs"
    monkeypatch.setenv("OPENAI_API_KEY", "dummy")

    runner = CliRunner()
    result = runner.invoke(main, [str(tmp_path), "--output", str(output_dir)], catch_exceptions=False)
    assert result.exit_code == 0
    assert (output_dir / "constants.md").exists()
    content = (output_dir / "constants.md").read_text()
    assert "Just constants." in content


def test_parser_handles_missing_file():
    """parse_file should raise FileNotFoundError for a non-existent path."""
    from autodocgen.parser import parse_file
    with pytest.raises(FileNotFoundError):
        parse_file("/nonexistent/path/to/file.py")


def test_parser_handles_syntax_error(tmp_path):
    """parse_file should raise ValueError for a file with a syntax error."""
    from autodocgen.parser import parse_file
    broken = tmp_path / "broken.py"
    broken.write_text("def foo(:\n    pass\n")
    with pytest.raises(ValueError, match="Syntax error"):
        parse_file(broken)


def test_parser_no_docstring_module(tmp_path):
    """Modules without a module docstring should have docstring=None."""
    from autodocgen.parser import parse_file
    f = tmp_path / "nodoc.py"
    f.write_text("x = 1\n")
    mod = parse_file(f)
    assert mod.docstring is None


def test_writer_index_uses_project_name(tmp_path):
    """write_index should use the supplied project_name in the heading."""
    from autodocgen.writer import write_index
    from autodocgen.parser import CodeModule
    modules = [CodeModule(filepath=tmp_path / "a.py", module_name="a", docstring="", imports=[])]
    idx = write_index(modules, tmp_path / "docs", project_name="MyAwesomeLib")
    content = idx.read_text()
    assert "MyAwesomeLib" in content
    assert "AutoDocGen" not in content  # old hardcoded title must NOT appear
