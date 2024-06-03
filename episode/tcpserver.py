import socket
import select
from enum import Enum

from episode.logger import EPISODE_LOGGER


class AppMode(Enum):
    DEV = "Development"
    PROD = "Production"
    TEST = "Testing"


class TCPServer:
    def __init__(self, host="127.0.0.1", port=8880):
        self.host = host
        self.port = port
        self.connections_fds = []

    def start(self, host="127.0.0.1", port=8880, mode=AppMode.DEV):
        if host:
            self.host = host
        if port:
            self.port = port
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connections_fds.append(server_socket)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((self.host, self.port))
        server_socket.listen(5)

        sockhost, sockport = server_socket.getsockname()

        EPISODE_LOGGER.info("Serving at http://{}:{}  (Press CTRL+C to quit)".format(sockhost, sockport))

        while True:
            read_fds, _, _ = select.select(self.connections_fds, [], [], 10)

            for fd in read_fds:
                if fd == server_socket:
                    conn, addr = server_socket.accept()
                    print("Connected by", addr)
                    self.connections_fds.append(conn)
                else:
                    data = fd.recv(1024)

                    response = self.handle_request(data)

                    fd.sendall(response)
                    fds = self.connections_fds.copy()
                    for i in fds:
                        if i == fd:
                            self.connections_fds.remove(i)

                    fd.close()

    def handle_request(self, data):
        """Handles incoming data and returns a response.
        Override this in subclass.
        """
        return data
