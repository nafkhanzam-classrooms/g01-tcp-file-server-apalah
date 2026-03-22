import socket
import os
import sys

PORT = 12345
SERVER_DIR = "server_storage"

if not os.path.exists(SERVER_DIR):
    os.makedirs(SERVER_DIR)

def start_sync_server():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    s.settimeout(1.0)
    
    try:
        s.bind(('0.0.0.0', PORT))
        s.listen(1)
        print(f"Sync Server ON di port {PORT}")
        print("Mode: Synchronous (Hanya melayani 1 client secara bergantian)")
        print("Tekan Ctrl+C untuk mematikan server.")

        while True:
            try:
                conn, addr = s.accept()
                print(f"[CONNECTED] Client terhubung: {addr}")
                
                with conn:
                    while True:
                        try:
                            raw_data = conn.recv(10240)
                            if not raw_data:
                                break
                            
                            try:
                                data = raw_data.decode().strip()
                            except:
                                data = ""

                            # LIST
                            if data == "/list":
                                files = os.listdir(SERVER_DIR)
                                res = "Files on server: " + (", ".join(files) if files else "Empty")
                                conn.send(res.encode())

                            # UPLOAD
                            elif data.startswith("/upload "):
                                try:
                                    filename = data.split(maxsplit=1)[1]
                                    filepath = os.path.join(SERVER_DIR, filename)
                                    
                                    conn.send(b"READY") 
                                    
                                    file_content = conn.recv(10240)
                                    with open(filepath, "wb") as f:
                                        f.write(file_content)
                                    
                                    conn.send(f"Upload {filename} berhasil!".encode())
                                    print(f"[UPLOAD] File {filename} berhasil disimpan dari {addr}")
                                except Exception as e:
                                    conn.send(f"ERR: Gagal upload ({e})".encode())

                            # DOWNLOAD
                            elif data.startswith("/download "):
                                try:
                                    filename = data.split(maxsplit=1)[1]
                                    filepath = os.path.join(SERVER_DIR, filename)
                                    if os.path.exists(filepath):
                                        with open(filepath, "rb") as f:
                                            content = f.read()
                                        header = f"DOWNLOAD_DATA:{filename}:".encode()
                                        conn.sendall(header + content)
                                        print(f"[DOWNLOAD] Mengirim {filename} ke {addr}")
                                    else:
                                        conn.send(b"ERR: File tidak ditemukan di server.")
                                except Exception as e:
                                    conn.send(f"ERR: Gagal download ({e})".encode())

                            # FITUR: CHAT
                            elif data:
                                print(f"[{addr}] Chat: {data}")
                                conn.send(f"Server (Sync): Pesan '{data}' diterima.".encode())

                        except ConnectionResetError:
                            print(f"[DISCONNECTED] Client {addr} memutus koneksi secara paksa.")
                            break
                        except Exception as e:
                            print(f"[ERROR] Kesalahan pada {addr}: {e}")
                            break

                print(f"[FINISHED] Selesai melayani {addr}. Menunggu client berikutnya...")
                
            except socket.timeout:
                continue
    except KeyboardInterrupt:
        print("\n[SHUTDOWN] Server dimatikan oleh pengguna.")
    finally:
        s.close()
        sys.exit(0)

if __name__ == "__main__":
    start_sync_server()