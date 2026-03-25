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

def start_poll_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', PORT))
    server_socket.listen(5)
    server_socket.setblocking(False)

    # Inisialisasi objek poll
    poller = select.poll()
    
    # Daftarkan server_socket untuk memantau koneksi masuk (POLLIN)
    poller.register(server_socket, select.POLLIN)

    # Dictionary untuk memetakan file descriptor (fd) ke objek socket
    # Karena poll() hanya mengembalikan fd (angka), kita butuh ini untuk mengambil socket-nya
    fd_to_socket = {server_socket.fileno(): server_socket}
    clients = {} # Untuk menyimpan alamat client {(socket): addr}

    print(f"Poll Server ON di port {PORT}")
    print("Mode: I/O Multiplexing (Poll System Call)")

    try:
        while True:
            # poll(timeout dalam milidetik). 1000ms = 1 detik agar bisa interrupt Ctrl+C
            events = poller.poll(1000)

            for fd, flag in events:
                s = fd_to_socket[fd]

                # 1. Jika ada koneksi baru (POLLIN pada server_socket)
                if s is server_socket:
                    conn, addr = s.accept()
                    print(f"[NEW CONNECTION] {addr}")
                    conn.setblocking(False)
                    
                    # Daftarkan client socket baru ke poller
                    poller.register(conn, select.POLLIN)
                    fd_to_socket[conn.fileno()] = conn
                    clients[conn] = addr

                # 2. Jika ada data masuk dari client (POLLIN)
                elif flag & select.POLLIN:
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
                                
                                # Switch ke blocking sementara untuk terima file
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
                                for fd_idx in fd_to_socket:
                                    sock = fd_to_socket[fd_idx]
                                    if sock not in [server_socket, s]:
                                        try: sock.send(msg)
                                        except: pass
                        else:
                            # Client menutup koneksi
                            print(f"[DISCONNECTED] {clients[s]}")
                            poller.unregister(s)
                            del fd_to_socket[fd]
                            del clients[s]
                            s.close()
                    except:
                        if s in clients:
                            poller.unregister(s)
                            del fd_to_socket[fd]
                            del clients[s]
                            s.close()

                # 3. Jika ada error pada socket (POLLERR / POLLHUP)
                elif flag & (select.POLLHUP | select.POLLERR):
                    poller.unregister(s)
                    del fd_to_socket[fd]
                    if s in clients: del clients[s]
                    s.close()

    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server OFF.")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_poll_server()
