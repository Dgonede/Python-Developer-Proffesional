# Импортируем нашу функцию из модуля protobuf_writer
from protobuf_writer import write_protobuf_file

# Тест записи данных в файл
write_protobuf_file("person_data.bin", "John Doe", 123, "john.doe@example.com")

# Выводим сообщение, чтобы убедиться, что файл записан
print("Данные успешно записаны в файл 'person_data.bin'.")