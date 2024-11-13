from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from domain.models import Product
from domain.services import WarehouseService
from infrastructure.orm import Base, ProductORM, OrderORM
from infrastructure.repositories import SqlAlchemyProductRepository, SqlAlchemyOrderRepository
from infrastructure.unit_of_work import SqlAlchemyUnitOfWork
from infrastructure.database import DATABASE_URL

engine= create_engine(DATABASE_URL)
SessionFactory=sessionmaker(bind=engine)
Base.metadata.create_all(engine)

def main():
    session = SessionFactory()
    product_repo = SqlAlchemyProductRepository(session)
    order_repo = SqlAlchemyOrderRepository(session)

    uow = SqlAlchemyUnitOfWork(session)

    warehouse_service = WarehouseService(product_repo, order_repo)
    
    with uow:
        # Создание нового продукта
        new_product = warehouse_service.create_product(name="test1", quantity=10, price=100)
        uow.commit()
        print(f"Создан продукт: {new_product}")

        # Создание еще одного продукта
        another_product = warehouse_service.create_product(name="test2", quantity=5, price=50)
        uow.commit()
        print(f"Создан продукт: {another_product}")

        # Получение списка продуктов
        products = product_repo.list()
        print("Список продуктов:")
        for product in products:
            print(product)

        # Создание заказа
        order = warehouse_service.create_order(products=[new_product, another_product])
        uow.commit()
        print(f"Создан заказ: {order}")

        # Получение списка заказов
        orders = order_repo.list()
        print("Список заказов:")
        for order in orders:
            print(order)

if __name__ == "__main__":
    main()