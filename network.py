"""DOCSTING."""
import socket
import json


def tcp_server(host, port, signals, handle_func):
    """DOCSTRING."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        s.settimeout(1)
        print(f"Listening on {host}:{port}")
        while not signals["shutdown"]:
            try:
                clientsocket, address = s.accept()
            except socket.timeout:
                continue

            clientsocket.settimeout(1)
            with clientsocket:
                message_chunks = []
                while not signals["shutdown"]:
                    try:
                        data = clientsocket.recv(4096)
                    except socket.timeout:
                        continue
                    if not data:
                        break
                    message_chunks.append(data)
            message_bytes = b''.join(message_chunks)
            message_str = message_bytes.decode("utf-8")
            try:
                message_dict = json.loads(message_str)
            except json.JSONDecodeError:
                continue
            handle_func(message_dict)


def udp_server(host, port, signals, handle_func):
    """DOCSTRING."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((host, port))
        sock.settimeout(1)

        while not signals["shutdown"]:
            try:
                message_bytes = sock.recv(4096)
            except socket.timeout:
                continue
            message_str = message_bytes.decode("utf-8")
            message_dict = json.loads(message_str)
            handle_func(message_dict)
    print("SHUTDOWN UDP")


def udp_client(host, port, message):
    """DOCSTRING."""
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:

        sock.connect((host, port))

        sock.sendall(message.encode('utf-8'))


def tcp_client(host, port, message):
    """DOCSTRING."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:

        sock.connect((host, port))

        sock.sendall(message.encode('utf-8'))
