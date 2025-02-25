from person_pb2 import Person  # Импортируем сгенерированную библиотеку Protobuf
import io  # Используем стандартный модуль для работы с файлами

# Функция для записи данных в файл
def write_to_file(str filename, str name, int id, str email):
    # Создаем объект Person и заполняем его данными
    person = Person()  
    person.name = name
    person.id = id
    person.email = email

    # Сериализация объекта в строку байт
    data = person.SerializeToString()

    # Записываем данные в файл с использованием Python I/O
    with open(filename, "wb") as f:
        f.write(data)

# Python-обертка для использования функции
def write_protobuf_file(filename, name, id, email):
    write_to_file(filename, name, id, email)