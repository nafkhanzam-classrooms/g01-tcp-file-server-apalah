import socket
import select
import os
import sys
import time

# Konfigurasi Server
PORT = 12345
SERVER_DIR = "server_storage"

if not os.path.exists(SERVER_DIR):
    os.makedirs(SERVER_DIR)

def start_select_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', PORT))
    server_socket.listen(5)
    server_socket.setblocking(False) 

    inputs = [server_socket]
    clients = {} 

    print(f"Select Server ON di port {PORT}")
    print("Mode: I/O Multiplexing (Single-threaded)")

    try:
        while inputs:

            readable, _, exceptional = select.select(inputs, [], inputs, 1.0)

            if not (readable or exceptional):
                continue

            for s in readable:
                if s is server_socket:
                    conn, addr = s.accept()
                    print(f"[NEW CONNECTION] {addr}")
                    conn.setblocking(False)
                    inputs.append(conn)
                    clients[conn] = addr
                else:
                    try:
                        raw_data = s.recv(1024)
                        if raw_data:
                            data = raw_data.decode().strip()
                            addr = clients[s]

                            if data == "/list":
                                files = os.listdir(SERVER_DIR)
                                res = "Files on server: " + (", ".join(files) if files else "Empty")
                                s.send(res.encode())

                            elif data.startswith("/upload "):
                                filename = data.split(maxsplit=1)[1]
                                filepath = os.path.join(SERVER_DIR, filename)
                                
                                s.send(b"READY_TO_RECEIVE")
                                
                                time.sleep(0.5) 

                                s.setblocking(True)
                                file_content = s.recv(10240)
                                with open(filepath, "wb") as f:
                                    f.write(file_content)
                                s.setblocking(False)
                                
                                s.send(f"Upload {filename} berhasil!".encode())
                                print(f"[UPLOAD] {filename} dari {addr} sukses.")

                            elif data.startswith("/download "):
                                filename = data.split(maxsplit=1)[1]
                                filepath = os.path.join(SERVER_DIR, filename)
                                if os.path.exists(filepath):
                                    with open(filepath, "rb") as f:
                                        content = f.read()
                                    header = f"DOWNLOAD_DATA:{filename}:".encode()
                                    s.sendall(header + content)
                                else:
                                    s.send(b"ERR: File tidak ditemukan")

                            else:
                                # Broadcast Chat
                                print(f"[{addr}] Chat: {data}")
                                msg = f"{addr}: {data}".encode()
                                for client_sock in inputs:
                                    if client_sock not in [server_socket, s]:
                                        try: client_sock.send(msg)
                                        except: pass
                        else:
                            print(f"[DISCONNECTED] {clients[s]}")
                            inputs.remove(s)
                            del clients[s]
                            s.close()
                    except:
                        if s in inputs: inputs.remove(s)
                        if s in clients: del clients[s]
                        s.close()
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server OFF.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_select_server()