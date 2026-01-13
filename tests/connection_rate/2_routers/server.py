#!/usr/bin/env python3

import socket
import sys

if len(sys.argv) != 2:
    print("Usage: python server.py <port>")
    sys.exit(1)

port = int(sys.argv[1])
host = '0.0.0.0'

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen()
    print(f"Server listening on {host}:{port}")
    while True:
        conn, addr = s.accept()
        conn.sendall(b'OK')
        conn.close()
