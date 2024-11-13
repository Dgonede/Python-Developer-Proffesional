import pytest
from unittest.mock import MagicMock
from domain.models import Product, Order
from domain.services import WarehouseService

@pytest.fixture
def warehouse_service():
    product_repo = MagicMock()
    order_repo = MagicMock()
    return WarehouseService(product_repo, order_repo)

def test_create_product(warehouse_service):
    product_name = "test_product"
    product_quantity = 10
    product_price = 100.0

    new_product = warehouse_service.create_product(product_name, product_quantity, product_price)

    warehouse_service.product_repo.add.assert_called_once()
    assert isinstance(new_product, Product)
    assert new_product.name == product_name
    assert new_product.quantity == product_quantity
    assert new_product.price == product_price

def test_create_order(warehouse_service):
    product1 = Product(id=1, name="test_product1", quantity=10, price=100.0)
    product2 = Product(id=2, name="test_product2", quantity=5, price=50.0)

    order = warehouse_service.create_order(products=[product1, product2])

    warehouse_service.order_repo.add.assert_called_once()
    assert isinstance(order, Order)
    assert len(order.products) == 2
    assert product1 in order.products
    assert product2 in order.products