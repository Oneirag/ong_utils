"""
General functions to deal with web servers
"""
import socket


def find_available_port(initial_port: int = 5000, end_port: int = 9999, logger=None) -> int:
    """
    Tries to bind to a port, if not possible increments by one until a free port is found
    :param initial_port: start port to try (defaults to 5000)
    :param end_port: final port to try (defaults to 9999)
    :param logger: and optional logger to log tries. If none, loger.info will be used to log retries
    :return: the number of the first free port found
    """
    initial_port = int(initial_port)
    for port in range(initial_port, end_port + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if not s.connect_ex(('localhost', port)) == 0:     # Port NOT in use
                if port != initial_port:
                    info_msg = f"Port {initial_port} is in use. Using next available port: {port}"
                    if logger is not None:
                        logger.info(info_msg)
                    else:
                        print(info_msg)
                return port
    raise ConnectionRefusedError(f"No available ports in range from {initial_port} to {end_port}")


