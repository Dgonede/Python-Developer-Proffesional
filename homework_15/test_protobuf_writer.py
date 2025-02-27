# test_protobuf_writer.py
from protobuf_writer import write_protobuf_file
from person_pb2 import Person

# Тест записи данных в файл
write_protobuf_file("person_data.bin", "John Doe", 123, "john.doe@example.com")

# Выводим сообщение, чтобы убедиться, что файл записан
print("Данные успешно записаны в файл 'person_data.bin'.")

# Чтение данных из файла и десериализация
with open("person_data.bin", "rb") as f:
    data = f.read()

# Десериализация данных обратно в объект Person
person = Person()
person.ParseFromString(data)

# Печать десериализованных данных
print(f"Name: {person.name}")
print(f"ID: {person.id}")
print(f"Email: {person.email}")