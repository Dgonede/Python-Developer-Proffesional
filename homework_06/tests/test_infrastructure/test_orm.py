import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from infrastructure.orm import Base, ProductORM, OrderORM
from infrastructure.repositories import SqlAlchemyProductRepository, SqlAlchemyOrderRepository
from domain.models import Product, Order

@pytest.fixture(scope='module')
def test_db():
    engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(engine)
    SessionFactory = sessionmaker(bind=engine)
    yield SessionFactory
    Base.metadata.drop_all(engine)

@pytest.fixture
def session(test_db):
    session = test_db()
    yield session
    session.close()

def test_product_crud(session):
    product_repo = SqlAlchemyProductRepository(session)
    product = Product(id=None, name="test_product", quantity=10, price=100.0)
    
    product_repo.add(product)
    session.commit()

    # Проверка, что продукт был добавлен
    retrieved_product = product_repo.get(1)
    assert retrieved_product.name == "test_product"
    assert retrieved_product.quantity == 10
    assert retrieved_product.price == 100.0

    # Проверка списка продуктов
    products = product_repo.list()
    assert len(products) == 1
