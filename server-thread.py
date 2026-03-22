import socket
import threading
import os
import sys

PORT = 12345
SERVER_DIR = "server_storage"

if not os.path.exists(SERVER_DIR): 
    os.makedirs(SERVER_DIR)

clients = []

def broadcast(message, sender_conn):
    for client in clients:
        if client != sender_conn:
            try:
                if isinstance(message, str):
                    client.send(message.encode())
                else:
                    client.send(message)
            except:
                if client in clients:
                    clients.remove(client)

def handle_client(conn, addr):
    clients.append(conn)
    print(f"[CONNECTED] {addr}")
    try:
        while True:
            raw_data = conn.recv(10240) 
            if not raw_data: break

            try:
                data = raw_data.decode().strip()
            except:
                data = ""

            if data == "/list":
                files = os.listdir(SERVER_DIR)
                response = "Files on server: " + (", ".join(files) if files else "Empty")
                conn.send(response.encode())

            elif data.startswith("/upload "):
                try:
                    filename = data.split(maxsplit=1)[1]
                    filepath = os.path.join(SERVER_DIR, filename)
                    file_content = conn.recv(10240)
                    with open(filepath, "wb") as f:
                        f.write(file_content)
                    conn.send(f"Upload {filename} berhasil!".encode())
                    broadcast(f"Notif: User {addr} mengupload {filename}", conn)
                except Exception as e:
                    conn.send(f"ERR: Gagal upload ({e})".encode())

            elif data.startswith("/download "):
                try:
                    filename = data.split(maxsplit=1)[1]
                    filepath = os.path.join(SERVER_DIR, filename)
                    if os.path.exists(filepath):
                        with open(filepath, "rb") as f:
                            file_content = f.read()
                        header = f"DOWNLOAD_DATA:{filename}:".encode()
                        conn.sendall(header + file_content)
                    else:
                        conn.send(b"ERR: File tidak ditemukan di server.")
                except Exception as e:
                    conn.send(f"ERR: Gagal download ({e})".encode())

            elif data:
                broadcast(f"{addr}: {data}", conn)
                
    except:
        pass
    finally:
        if conn in clients:
            clients.remove(conn)
        conn.close()

def start_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.settimeout(1.0) 
    
    try:
        s.bind(('0.0.0.0', PORT))
        s.listen(5)
        print(f"Threading Server ON di port {PORT}")
        print("Tekan Ctrl+C untuk mematikan server...")
        
        while True:
            try:
                c, a = s.accept()
                thread = threading.Thread(target=handle_client, args=(c, a), daemon=True)
                thread.start()
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\n[SHUTTING DOWN] Server dimatikan oleh pengguna.")
    finally:
        s.close()
        sys.exit(0)

if __name__ == "__main__":
    start_server()