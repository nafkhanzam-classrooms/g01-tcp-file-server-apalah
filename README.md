[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mRmkZGKe)
# Network Programming - Assignment G01

## Anggota Kelompok
| Nama           | NRP        | Kelas     |
| ---            | ---        | ----------|
| Rynofaldi Damario Dzaki               | 5025231042           |  D         |
| Naufal Dariskarim| 5025231027           | D          |

## Link Youtube (Unlisted)
Link ditaruh di bawah ini
```

```

## Penjelasan Program

# Penjelasan Kode TCP File Server & Panduan Testing

Tugas **TCP File Server** ini mengimplementasikan satu klien ([client.py](file:///c:/SMT%206/Progjar/G01/client.py)) dan empat jenis server yang berbeda secara fundamental dalam menangani banyak *client* (klien). Berikut adalah penjelasan struktur, logika kode, serta cara kerjanya.

---

## 1. Protokol Komunikasi (Application Layer)
Semua file ([client](file:///c:/SMT%206/Progjar/G01/server-thread.py#97-143) dan `server`) berkomunikasi menggunakan TCP pada port `9000` dengan protokol teks dan biner buatan sendiri:

1. **Format Perintah Dasar:** Perintah dikirim sebagai string teks diakhiri dengan karakter newline (`\n`). Contoh: `/list\n`, `/download file.txt\n`.
2. **Transfer File (Download/Upload):** Berbeda dengan perintah teks biasa, transfer file juga mengirimkan ukuran file (byte) sebelum isi filenya agar penerima tahu kapan harus berhenti membaca buffer.

---

## 2. Penjelasan File dan Fungsinya

### A. [client.py](file:///c:/SMT%206/Progjar/G01/client.py)
Ini adalah antarmuka interaktif (REPL - Read Eval Print Loop) untuk pengguna.
*   **Fungsi Kunci:**
    *   [recv_line()](file:///c:/SMT%206/Progjar/G01/server-sync.py#17-26): Digunakan untuk membaca respon server baris demi baris (sampai ketemu `\n`).
    *   [recv_exact(n)](file:///c:/SMT%206/Progjar/G01/server-sync.py#27-36): Membaca secara eksak sebanyak `n` byte dari socket. Sangat penting digunakan saat mendownload file, karena kita tidak bisa mengandalkan [recv()](file:///c:/SMT%206/Progjar/G01/server-sync.py#17-26) biasa (bisa terpotong di tengah jalan karena MTU batasan jaringan).
    *   [cmd_upload()](file:///c:/SMT%206/Progjar/G01/client.py#59-93): Membaca ukuran file lokal menggunakan `os.path.getsize()`, mengirimkan `/upload <nama>`, menunggu `READY` dari server, mengirim ukuran, lalu mengirim byte file secara berkelanjutan (`chunk`).
*   **Thread Receive:** [client.py](file:///c:/SMT%206/Progjar/G01/client.py) memiliki thread terpisah [receive_broadcast()](file:///c:/SMT%206/Progjar/G01/client.py#11-24) agar klien bisa menerima pesan broadcast (seperti "Client baru terhubung") secara asinkron tanpa mengganggu `input()` user yang bersifat *blocking*.

### B. [server-sync.py](file:///c:/SMT%206/Progjar/G01/server-sync.py) (Synchronous)
Server ini adalah bentuk paling sederhana dan konvensional.
*   **Cara Kerja:** Server memanggil `conn, addr = accept()`. Eksekusi program akan **berhenti** pada pemanggilan ini sampai ada client yang terkoneksi. Setelah terhubung, server memanggil [handle_client()](file:///c:/SMT%206/Progjar/G01/server-thread.py#97-143) yang bersifat *blocking loop*, membaca perintah dari klien tersebut.
*   **Masalah Utama:** Selama server sedang melayani klien A (berada di dalam loop [handle_client](file:///c:/SMT%206/Progjar/G01/server-thread.py#97-143)), klien B yang mencoba terkoneksi akan dimasukkan ke dalam antrian sistem operasi (*backlog*) dan **tidak akan direspon** sampai klien A terputus.

### C. [server-select.py](file:///c:/SMT%206/Progjar/G01/server-select.py) (I/O Multiplexing dengan `select()`)
Server ini memecahkan masalah *blocking* pada [server-sync.py](file:///c:/SMT%206/Progjar/G01/server-sync.py) untuk bisa melayani >1 klien dalam satu proses (tanpa perlu thread/process baru).
*   **Cara Kerja:** OS memantau sekelompok socket (*monitor list*). Fungsi `select.select(inputs, ...)` akan meminta OS untuk memberitahu socket mana saja yang siap ("readable"), entah itu server socket (berarti ada koneksi baru siap di-`accept()`) atau client socket (berarti ada data baru yang siap di-[recv()](file:///c:/SMT%206/Progjar/G01/server-sync.py#17-26)).
*   **Fungsi Kunci (State Machine):** Mengingat non-blocking [recv()](file:///c:/SMT%206/Progjar/G01/server-sync.py#17-26) pada TCP tidak menjamin membaca satu pesan utuh sekaligus, `server-select` menggunakan variabel `client_state` untuk melacak status setiap klien (apakah sedang `idle`, atau sedang ditengah-tengah `upload_wait_size`). Buffer teks yang belum lengkap disimpan per-klien.

### D. [server-poll.py](file:///c:/SMT%206/Progjar/G01/server-poll.py) (I/O Multiplexing dengan `poll()`)
Sangat mirip dengan `select()`, namun lebih modern untuk sistem UNIX (Linux/macOS/WSL).
*   **Cara Kerja:** Menggunakan `poller = select.poll()`. Berbeda dengan `select()` tradisional yang harus mengirim ulang daftar socket setiap kali pemanggilan (terbatas biasanya 1024 FD maksimal), `poll()` mendaftarkan *file descriptor* (FD) di level *kernel* (`poller.register()`). OS akan mengembalikan *event mask* (contoh: `select.POLLIN` berarti ada data masuk).
*   **Catatan:** Syscall `poll()` tidak didukung oleh kernel Windows.

### E. [server-thread.py](file:///c:/SMT%206/Progjar/G01/server-thread.py) (Concurrency dengan Multi-threading)
Menggunakan pendekatan klasik untuk *concurrency*.
*   **Cara Kerja:** Server tetap melakukan `accept()` yang berjalan *blocking* di *Main Thread*. Namun, setiap kali ada klien baru, server akan menciptakan pekerja baru: `threading.Thread(target=handle_client)`.
*   **Kelebihan/Kekurangan:** Penulisan logikanya sangat mudah (hampir sama seperti [server-sync.py](file:///c:/SMT%206/Progjar/G01/server-sync.py)), karena setiap *thread* dapat melakukan operasi yang memakan waktu (*blocking*) tanpa menghentikan *thread* klien lainnya. Namun, jika ada ribuan klien, ribuan *thread* yang aktif bisa menghabiskan memori dan memberatkan *context switching* prosesor.
*   **Locking:** Menggunakan `threading.Lock()` yang krusial pada fungsi [broadcast()](file:///c:/SMT%206/Progjar/G01/server-thread.py#42-52) untuk mencegah modifikasi terhadap list klien secara bersamaan (*Race Condition*) saat satu klien terkoneksi dan satu klien lain terputus.

---

## 3. Eksekusi Uji Coba (Testing Guide)

Anda membutuhkan setidaknya 2 Window/Tab Terminal di folder `c:\SMT 6\Progjar\G01\`.

### 1. Test One-on-One (`server-sync`)
*   **Terminal 1:** `python server-sync.py`
*   **Terminal 2:** `python client.py`
*   Uji `/list`, `/upload`, dan `/download` di Terminal 2. File akan masuk ke `server_files/` (server) dan `downloads/` (klien).
*   Jika Anda coba buka **Terminal 3**, klien akan nyangkut (*hanging*).

### 2. Test Multi-Client (`server-thread` atau `server-select`)
*   **Terminal 1:** `python server-thread.py` (atau ganti jadi `server-select.py`)
*   **Terminal 2:** `python client.py` (akan terhubung)
*   **Terminal 3:** `python client.py` (akan terhubung)
*   **Test Broadcast:** Saat Terminal 3 masuk, lihat output di Terminal 2. Terminal 2 akan langsung mendapat pesan: `[BROADCAST] Client baru terhubung dari ...`.
*   **Test Interaktif:** Klien di Terminal 2 dan 3 bisa melakukan upload/download dan list file secara simultan tanpa ada satu klien menghalangi klien lain.

### 3. Test `server-poll` (Bila di sistem Linux / macOS / WSL)
*   Ikuti langkah yang sama seperti Nomor 2 di atas, hanya saja jalankan `python server-poll.py`.
*   *(Jika Anda menjalankannya pada CMD/Powershell Windows asli, script akan mendeteksinya dan mengeluarkan notifikasi Error dengan benar).*


## Screenshot Hasil
