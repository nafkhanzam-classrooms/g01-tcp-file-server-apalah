import socket
import threading
import os
import time
import sys

DOWNLOAD_DIR = "client_downloads"
if not os.path.exists(DOWNLOAD_DIR): 
    os.makedirs(DOWNLOAD_DIR)

def receive_messages(sock):
    while True:
        try:
            data = sock.recv(10240)
            if not data: break
            
            sys.stdout.write("\r" + " " * 60 + "\r")
            sys.stdout.flush()

            if data.startswith(b"DOWNLOAD_DATA:"):
                _, filename_bytes, content = data.split(b":", 2)
                filename = filename_bytes.decode()
                filepath = os.path.join(DOWNLOAD_DIR, filename)
                
                with open(filepath, "wb") as f:
                    f.write(content)
                
                print(f"[Selesai] File '{filename}' tersimpan di '{DOWNLOAD_DIR}'.")
            
            elif data.startswith(b"ERR:"):
                print(f"[Error Server] {data.decode()}")
            
            else:
                print(f"[Server] {data.decode()}")
            
            sys.stdout.write(">> ")
            sys.stdout.flush()
            
        except:
            break

def start_client():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect(('127.0.0.1', 12345))
        
        threading.Thread(target=receive_messages, args=(client,), daemon=True).start()
        
        print("--- TCP File Client ---")
        print("Ketik pesan atau perintah: /list, /upload <nama_file>, /download <nama_file>")
        sys.stdout.write(">> ")
        sys.stdout.flush()
        
        while True:
            msg = input("") 
            if not msg: 
                sys.stdout.write(">> ")
                sys.stdout.flush()
                continue

            if msg.startswith("/upload"):
                parts = msg.split(maxsplit=1)
                if len(parts) < 2:
                    print("Gunakan: /upload <nama_file>")
                    sys.stdout.write(">> ")
                    sys.stdout.flush()
                    continue
                
                filename = parts[1]
                if os.path.exists(filename):
                    client.send(msg.encode())
                    
                    with open(filename, "rb") as f:
                        client.sendall(f.read())
                    print(f"Sedang mengupload '{filename}'...")
                else:
                    print(f"File '{filename}' tidak ditemukan di folder lokal.")
                    sys.stdout.write(">> ")
                    sys.stdout.flush()
            
            else:
                client.send(msg.encode())
                if msg.startswith("/download"):
                    print("Meminta file ke server...")

    except Exception as e:
        print(f"\nGagal terhubung ke server: {e}")

if __name__ == "__main__":
    start_client()