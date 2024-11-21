import socket
import threading
import os

HOST = "localhost"
PORT = 8080
DOCUMENT_ROOT = './www'

def handle_request(client_socket):
    try:
        request = client_socket.recv(1024).decode()
        if not request:
            return
        
        
        lines = request.splitlines()
        if len(lines) > 0:
            method, path, _ = lines[0].split()

            if path == '/':
                path = '/index.html'

            file_path = os.path.join(DOCUMENT_ROOT, path.lstrip('/'))
            print(f"Запрашиваемый файл: {file_path}")

            if method in ['GET', 'HEAD']:
                if os.path.isfile(file_path):
                    # Если файл существует, читаем его
                    with open(file_path, 'rb') as f:
                        content = f.read()
                    
                    # Формируем ответ
                    response_line = 'HTTP/1.1 200 OK\r\n'
                    headers = f'Content-Length: {len(content)}\r\n'
                    headers += 'Content-Type: text/html\r\n'
                    response = response_line + headers + '\r\n'
                    
                    # Если метод GET, добавляем содержимое файла
                    if method == 'GET':
                        response = response.encode() + content
                    else:
                        response = response.encode()  # Для HEAD, содержимое не добавляется
                    
                else:
                    # Если файл не найден
                    response = 'HTTP/1.1 404 Not Found\r\n\r\nFile Not Found'.encode()
            else:
                # Если метод не поддерживается
                response = 'HTTP/1.1 405 Method Not Allowed\r\n\r\nMethod Not Allowed'.encode()
            
            # Отправляем ответ клиенту
            client_socket.sendall(response)
    finally:
        client_socket.close()

def start_server():
    # Создаем сокет
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen(5)
    print(f'Server running on http://{HOST}:{PORT}')

    while True:
        # Принимаем входящие соединения
        client_socket, addr = server_socket.accept()
        print(f'Connection from {addr}')
        # Создаем новый поток для обработки запроса
        thread = threading.Thread(target=handle_request, args=(client_socket,))
        thread.start()

if __name__ == "__main__":
    start_server()