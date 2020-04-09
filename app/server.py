#
# Серверное приложение для соединений
#
import asyncio
from asyncio import transports
import time


class ServerProtocol(asyncio.Protocol):
    login: str = None
    server: 'Server'
    transport: transports.Transport
    qty_history_messages = 10

    def __init__(self, server: 'Server'):
        self.server = server

    def data_received(self, data: bytes):
        print(data)

        decoded = data.decode()
        if decoded.startswith("login:"):
            incoming_login = decoded.replace("login:", "").replace("\r\n", "")
            for client in self.server.clients:
                print(f"Онлайн сейчас: {client.login}")
                if incoming_login == client.login:
                    self.transport.write(f"Логин {client.login} занят, попробуйте другой".encode())
                    time.sleep(5)  # Сон в 5 секунды
                    self.transport.close()

            self.login = incoming_login
            self.transport.write(
                f"Привет, {self.login}!\n".encode()
            )
            if self.server.history_messages:
                self.send_history(self.qty_history_messages)

        else:
            if self.login is not None:
                self.send_message(decoded)
            else:
                self.transport.write("Неправильный логин\n".encode())

    def send_history(self, number: int):
        self.transport.write(f"Последние {number} сообщения в чате:\n".encode())
        for index, message in enumerate(self.server.history_messages):
            if (index + 1) <= number:
                self.transport.write(message.encode())

    def connection_made(self, transport: transports.Transport):
        self.server.clients.append(self)
        self.transport = transport
        print("Пришел новый клиент")

    def connection_lost(self, exception):
        self.server.clients.remove(self)
        print("Клиент вышел")

    def send_message(self, content: str):
        message = f"{self.login}: {content}"
        self.server.history_messages.append(message)

        for user in self.server.clients:
            if user.login is not None:
                user.transport.write(message.encode())


class Server:
    history_messages: list
    clients: list

    def __init__(self):
        self.clients = []
        self.history_messages = []

    def build_protocol(self):
        return ServerProtocol(self)

    async def start(self):
        loop = asyncio.get_running_loop()

        coroutine = await loop.create_server(
            self.build_protocol,
            '127.0.0.1',
            8888
        )

        print("Сервер запущен ...")

        await coroutine.serve_forever()


process = Server()

try:
    asyncio.run(process.start())
except KeyboardInterrupt:
    print("Сервер остановлен вручную")
