"""
server-poll.py — Multi-client TCP File Server menggunakan select.poll()
PERHATIAN: poll() tidak tersedia di Windows. Jalankan di Linux/macOS/WSL.
"""

import socket
import select
import os

HOST = '0.0.0.0'
PORT = 9000
BUFFER_SIZE = 4096
SERVER_FILES_DIR = './server_files'

def setup():
    os.makedirs(SERVER_FILES_DIR, exist_ok=True)

def recv_line_from_buf(buf):
    if b'\n' in buf:
        idx = buf.index(b'\n')
        return buf[:idx].decode('utf-8', errors='replace').strip(), buf[idx+1:]
    return None, buf

def broadcast(fd_to_socket, server_fd, sender_fd, message):
    """Broadcast pesan ke semua client kecuali sender dan server."""
    msg = f'[BROADCAST] {message}\n'.encode()
    for fd, sock in fd_to_socket.items():
        if fd != server_fd and fd != sender_fd:
            try:
                sock.sendall(msg)
            except Exception:
                pass

def handle_list(conn):
    files = os.listdir(SERVER_FILES_DIR)
    response = 'FILES: ' + (', '.join(files) if files else '(kosong)')
    conn.sendall((response + '\n').encode())

def handle_download(conn, filename):
    file_path = os.path.join(SERVER_FILES_DIR, os.path.basename(filename))
    if not os.path.isfile(file_path):
        conn.sendall(f'ERROR: File \'{filename}\' tidak ditemukan\n'.encode())
        return
    filesize = os.path.getsize(file_path)
    conn.sendall(f'{filesize}\n'.encode())
    with open(file_path, 'rb') as f:
        while True:
            chunk = f.read(BUFFER_SIZE)
            if not chunk:
                break
            conn.sendall(chunk)
    print(f"[DOWNLOAD] Dikirim: {filename} ({filesize} bytes)")

def main():
    setup()

    # Cek apakah poll tersedia (tidak tersedia di Windows)
    if not hasattr(select, 'poll'):
        print("[ERROR] select.poll() tidak tersedia di sistem ini (Windows tidak mendukung poll).")
        print("[INFO] Gunakan WSL (Windows Subsystem for Linux) atau jalankan di Linux/macOS.")
        return

    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((HOST, PORT))
    server_sock.listen(10)
    server_sock.setblocking(False)

    poller = select.poll()
    poller.register(server_sock, select.POLLIN)

    fd_to_socket = {server_sock.fileno(): server_sock}
    addr_map = {}       # fd -> addr
    client_state = {}   # fd -> state dict

    SERVER_FD = server_sock.fileno()

    print(f"[SERVER-POLL] Mendengarkan di {HOST}:{PORT} ...")
    print("[INFO] Mode: select.poll() — multi-client non-blocking")

    try:
        while True:
            events = poller.poll(1000)  # timeout 1000ms

            for fd, event in events:
                sock = fd_to_socket[fd]

                if event & (select.POLLHUP | select.POLLERR | select.POLLNVAL):
                    # Socket error atau hangup
                    addr = addr_map.get(fd, '?')
                    print(f"[DISCONNECT] {addr} (error/hangup)")
                    poller.unregister(fd)
                    fd_to_socket.pop(fd, None)
                    addr_map.pop(fd, None)
                    client_state.pop(fd, None)
                    sock.close()
                    continue

                if not (event & select.POLLIN):
                    continue

                if fd == SERVER_FD:
                    # Koneksi baru
                    conn, addr = server_sock.accept()
                    conn.setblocking(False)
                    cfd = conn.fileno()
                    poller.register(cfd, select.POLLIN | select.POLLHUP | select.POLLERR)
                    fd_to_socket[cfd] = conn
                    addr_map[cfd] = addr
                    client_state[cfd] = {'state': 'idle', 'buf': b''}
                    print(f"[CONNECT] {addr}")
                    broadcast(fd_to_socket, SERVER_FD, cfd,
                              f"Client baru terhubung dari {addr}")
                else:
                    # Data dari client
                    addr = addr_map.get(fd, '?')
                    state = client_state[fd]
                    try:
                        data = sock.recv(BUFFER_SIZE)
                    except Exception:
                        data = b''

                    if not data:
                        print(f"[DISCONNECT] {addr}")
                        poller.unregister(fd)
                        fd_to_socket.pop(fd, None)
                        addr_map.pop(fd, None)
                        client_state.pop(fd, None)
                        sock.close()
                        continue

                    state['buf'] += data

                    # Proses buffer dengan state machine
                    while True:
                        if state['state'] == 'idle':
                            line, state['buf'] = recv_line_from_buf(state['buf'])
                            if line is None:
                                break
                            print(f"[CMD] {addr} >> {line}")
                            parts = line.split(maxsplit=1)
                            cmd = parts[0].lower()

                            if cmd == '/list':
                                handle_list(sock)
                            elif cmd == '/download':
                                fname = parts[1].strip() if len(parts) > 1 else ''
                                if not fname:
                                    sock.sendall(b'ERROR: nama file diperlukan\n')
                                else:
                                    handle_download(sock, fname)
                            elif cmd == '/upload':
                                fname = parts[1].strip() if len(parts) > 1 else ''
                                if not fname:
                                    sock.sendall(b'ERROR: nama file diperlukan\n')
                                else:
                                    state['upload_file'] = fname
                                    state['upload_data'] = b''
                                    state['upload_size'] = None
                                    state['state'] = 'upload_wait_size'
                                    sock.sendall(b'READY\n')
                            else:
                                sock.sendall(f'ERROR: Perintah tidak dikenal: {cmd}\n'.encode())

                        elif state['state'] == 'upload_wait_size':
                            line, state['buf'] = recv_line_from_buf(state['buf'])
                            if line is None:
                                break
                            try:
                                state['upload_size'] = int(line)
                                state['state'] = 'upload_recv_data'
                            except ValueError:
                                sock.sendall(b'ERROR: ukuran file tidak valid\n')
                                state['state'] = 'idle'

                        elif state['state'] == 'upload_recv_data':
                            needed = state['upload_size'] - len(state['upload_data'])
                            chunk = state['buf'][:needed]
                            state['buf'] = state['buf'][needed:]
                            state['upload_data'] += chunk

                            if len(state['upload_data']) >= state['upload_size']:
                                fname = state['upload_file']
                                save_path = os.path.join(SERVER_FILES_DIR, os.path.basename(fname))
                                with open(save_path, 'wb') as f:
                                    f.write(state['upload_data'])
                                sz = state['upload_size']
                                print(f"[UPLOAD] Disimpan: {save_path} ({sz} bytes)")
                                sock.sendall(f"OK: File '{fname}' berhasil diupload ({sz} bytes)\n".encode())
                                state['state'] = 'idle'
                                state['upload_data'] = b''
                            else:
                                break
                        else:
                            break

    except KeyboardInterrupt:
        print("\n[SERVER] Dihentikan.")
    finally:
        server_sock.close()

if __name__ == '__main__':
    main()
