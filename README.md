[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/mRmkZGKe)
# Network Programming - Assignment G01

## Anggota Kelompok
| Nama           | NRP        | Kelas     |
| ---            | ---        | ----------|
| Rynofaldi Damario Dzaki               | 5025231042           |  D         |
| Naufal Dariskarim| 5025231027           | D          |

## Link Youtube (Unlisted)
Link ditaruh di bawah ini

Link Youtube : https://www.youtube.com/watch?v=O-EzFnm3Q_c

## Penjelasan Program

# Penjelasan Kode TCP File Server (G01)

Laporan ini berisi penjelasan singkat dan sederhana mengenai sistem **TCP File Server** yang telah diimplementasikan. Program ini terdiri dari satu file klien (Client) dan empat variasi file Server. Fungsi utamanya adalah menangani command `/list`, `/upload`, dan `/download`.

---

## 1. Penjelasan Masing-Masing File

### 1️. [client.py](file:///c:/SMT%206/Progjar/G01/client.py) (Aplikasi Pengguna)
Ini adalah program yang dijalankan oleh klien untuk berkomunikasi dengan server (menggunakan port 9000).
*   **Koneksi (Socket):** `socket.connect((HOST, PORT))` menginisialisasi jalur TCP.
*   **Loop Perintah:** Membaca input (ketikan) pengguna dengan `input('> ')`.
*   **Mekanisme Upload/Download:** Saat command `/upload <file>` ditekan, *client* membaca besar ukuran file lokal (`os.path.getsize`), memberitahu server untuk bersiap (`READY`), kemudian mengirim ukuran byte total diikuti data isi file. Saat `/download`, *client* menerima ukuran byte dari server, lalu membuat file baru berisi data byte yang datang.
*   **Broadcast Receive:** Berjalan di `thread` terpisah, sehingga klien tetap bisa menerima notifikasi obrolan/info dari pengguna lain meskipun sedang mengetik perintah.

### 2️. [server-sync.py](file:///c:/SMT%206/Progjar/G01/server-sync.py) (Server Sederhana - *Synchronous*)
Ini adalah bentuk server berbasis TCP yang paling dasar. 
*   **Cara Kerja:** Server secara terus-menerus memanggil `accept()` untuk menunggu klien. Saat *Client A* tersambung, program masuk ke dalam blok/fungsi baru yang dinamakan [handle_client(conn)](file:///c:/SMT%206/Progjar/G01/server-thread.py#97-143).
*   **Kelemahan & Blocking:** Selama [handle_client()](file:///c:/SMT%206/Progjar/G01/server-thread.py#97-143) berjalan menanggapi *Client A*, *Client B* yang mencoba terhubung akan tersendat dan masuk antrian panjang OS (statusnya *hanging* atau *blocking*). Server ini baru melayani *Client B* ketika *Client A* putus (`close()`).

### 3️. [server-thread.py](file:///c:/SMT%206/Progjar/G01/server-thread.py) (Server Multi-Klien - *Threading*)
Implementasi solusi sederhana yang menyelesaikan masalah *blocking* pada `server-sync`.
*   **Cara Kerja:** Begitu fungsi `accept()` menerima *Client A*, program tidak melayaninya langsung, melainkan "mendelegasikan" tugas *Client A* ke sebuah pekerja baru bernama *Thread* (`threading.Thread(target=handle_client)`). Setelah pendelegasian ini sukses, otak server (*Main Thread*) dengan cepat kembali siap meng-`accept()` *Client B* seketika itu juga.
*   **Solusi Konflik:** Dilengkapi dengan sistem `threading.Lock()`, supaya daftar pengguna (`clients = []`) aman dari error ketidakstabilan akibat ditulis bersamaan secara tidak sengaja oleh beberapa obrolan klien berbeda (*Thread-safe*).

### 4️. [server-select.py](file:///c:/SMT%206/Progjar/G01/server-select.py) (Server Multi-Klien - *I/O Multiplexing*)
Pendekatan cerdas di mana Server dapat melayani banyak *client* sekaligus **tanpa** membutuhkan pekerja ekstra atau proses *thread* baru. Sangat menghemat memori.
*   **Cara Kerja:** Mendaftarkan seluruh socket klien aktif ke dalam keranjang `inputs`. Lalu server memanggil syscall OS bernama `select.select(inputs)`. Fungsi ini akan berdiam diri (nganggur) hingga ia diberitahu *"ada 2 klien ini nih pak yang ngirim pesan baru"*.
*   **State Machine:** Karena [recv()](file:///c:/SMT%206/Progjar/G01/server-sync.py#17-26) pada TCP tidak pasti datang sekaligus, server menyiasatinya. Misalnya kalau *Client A* sedang meng-upload sebuah file bergiga-giga, state variabelnya diubah menjadi `upload_wait_size`, dan tidak akan menghabiskan CPU untuk menungguinya karena server bisa sembari memproses *Client B*.

### 5️. [server-poll.py](file:///c:/SMT%206/Progjar/G01/server-poll.py) (Server Multi-Klien - *Poll Linux / WSL*)
Ini adalah varian dari *Multiplexing* (sama fungsinya seperti `select`), dengan pendekatan *Event-based* menggunakan API `poller.register()` & `poller.poll()`. File ini menggunakan port `12345`.
*   **Perbedaannya:** Daripada mengirim daftar puluhan hingga ribuan klien bolak-balik ke Kernel (yang terjadi pada *select()*), [poll()](file:///c:/SMT%206/Progjar/G01/server-poll.py#14-129) mendaftarkan ID (disebut tipe file *descriptor*) langsung ke memori kernel Linux hanya satu kali.
*   **Cara Kerja Kode Anda:** Fungsi `events = poller.poll()` akan menanti. Bila salah satu *client* (*socket*) mengirimkan `hello`, kernel akan otomatis mengekstrak *file descriptor* yang cocok beserta tandanya (`select.POLLIN`), lalu merespons chat, atau jika yang datang `/upload`, ia siap menerima file.
*   **Hanya Untuk Linux / Unix:** API [poll()](file:///c:/SMT%206/Progjar/G01/server-poll.py#14-129) khusus disiapkan pada Linux, sehingga Windows CMD akan gagal menjalankan file ini tanpa subsistem perantara (WSL).

---

## 2. Cara Melakukan Pengujian (Testing)

Karena Anda memiliki 4 variasi file Server, silakan ikuti petunjuk dua sub-skenario berikut ini. Gunakan dua terminal atau Command Prompt terpisah secara bersebelahan.

### Skenario 1: Test Biasa (Windows & Linux)
Bisa digunakan untuk File: [server-sync.py](file:///c:/SMT%206/Progjar/G01/server-sync.py), [server-thread.py](file:///c:/SMT%206/Progjar/G01/server-thread.py), [server-select.py](file:///c:/SMT%206/Progjar/G01/server-select.py) (Default: Port 9000)

**Terminal/CMD A (Menjalankan Server):**
1. Buka CMD, ketik `cd "c:\SMT 6\Progjar\G01"` (sesuaikan path folder Anda).
2. Jalankan kode server. Contoh instruksinya: `python server-thread.py`

**Terminal/CMD B (Menjalankan Klien & Uji Interaksi):**
1. Buka CMD ke-2 (di direktori yang sama dengan langkah 1).
2. Jalankan klien TCP: `python client.py`
3. Begitu terhubung, lakukan tes perintah ini satu persatu:
   *   `/list` Cek folder server. (Harusnya kosong).
   *   `/upload namaku.txt` Pilih salah satu file teks untuk dikirim ke atas Server.
   *   `/list` Cek apakah file sudah muncul di sana.
   *   `/download namaku.txt` Tarik kembali file dan pastikan muncul di sub-folder `downloads/`.
**Catatan Penting Skenario 1:** Untuk tes sinkron [server-sync.py](file:///c:/SMT%206/Progjar/G01/server-sync.py), buka "Terminal C" baru lagi dan luncurkan [client.py](file:///c:/SMT%206/Progjar/G01/client.py) - Terminal tersebut akan terkunci / menunggu antrian, tidak bisa mengetik sampai Terminal B menutup programnya (ketik `/quit`). Ini tandanya [server-sync.py](file:///c:/SMT%206/Progjar/G01/server-sync.py) benar.

---

### Skenario 2: Test API Linux Poll (Khusus WSL Ubuntu/Debian)
Eksklusif digunakan untuk File: [server-poll.py](file:///c:/SMT%206/Progjar/G01/server-poll.py) (Port 12345)

**Terminal A (Linux WSL):**
1. Luncurkan aplikasi "Ubuntu" atau "WSL" di Windows Search.
2. Akses folder G01 sistem Windows melalui jalur `mnt`: `cd /mnt/c/SMT\ 6/Progjar/G01/`
3. Hidupkan server Poll: `python3 server-poll.py` (Server ini jalan mandiri di Sub-sistem).
4. Output muncul: `Poll Server ON di port 12345`

**Terminal B (Testing Menggunakan Tool Bantu - Bebas di WSL / CMD Normal):**
*(Klien kita tidak bisa langsung dikaitkan karena [server-poll.py](file:///c:/SMT%206/Progjar/G01/server-poll.py) menggunakan protokol beda format dan beda port (12345), jadi uji coba raw akan dilakukan:*
1. Ketik instruksi ini di CMD Asli Windows Anda: `telnet localhost 12345`  
   *(Jika Telnet belum aktif, cari di Windows 'turn on telnet client')*  
   Atau jika menggunakan netcat WSL: `nc localhost 12345`.
2. Ketik `/list` -> Anda dapat melihat output `Files on server: Empty`
3. Buka **Terminal C** menggunakan tes netcat lagi ke Port 12345. Anda bisa menguji fitur **Broadcast Chat** bawaan `server-poll` dengan langsung asal mengetik di layar. Terminal netcat yang lainnya akan kebanjiran pesan dari klien yang sedang meracau.
4. Apungkan `Ctrl+C` ketika selesai.


## Screenshot Hasil

### Server Threading

**Server**

<img width="895" height="275" alt="image" src="https://github.com/user-attachments/assets/da17c42d-a7ba-45ae-8c70-939efcd43e3f" />


**Client 1**

<img width="839" height="340" alt="image" src="https://github.com/user-attachments/assets/42b0c5fd-bdc6-440f-8af6-38ace698e259" />


**Client 2**

<img width="828" height="318" alt="image" src="https://github.com/user-attachments/assets/45bb5dd6-e59d-432a-b9d7-cd17d0227f91" />


**Client 3**

<img width="827" height="299" alt="image" src="https://github.com/user-attachments/assets/8d33561b-da96-4dfd-b273-6b5911e40076" />


**Files**

<img width="356" height="116" alt="image" src="https://github.com/user-attachments/assets/05c762b4-22bf-4feb-94aa-ffa838f4f709" />



### Server Select

**Server**

<img width="902" height="286" alt="image" src="https://github.com/user-attachments/assets/6ad4eae8-7ef7-4744-8426-50619ce6098b" />



**Client 1**

<img width="879" height="291" alt="image" src="https://github.com/user-attachments/assets/31c6a282-d410-419d-baaf-1e948167ec12" />


**Client 2**

<img width="846" height="257" alt="image" src="https://github.com/user-attachments/assets/09cf8673-1d26-4156-b204-1657339951e2" />


**Client 3**

<img width="845" height="256" alt="image" src="https://github.com/user-attachments/assets/13721ab8-efed-4d74-824d-71b816cab689" />


**Files**

<img width="377" height="172" alt="image" src="https://github.com/user-attachments/assets/7648e933-6195-41ce-b065-cfacd3961348" />


### Server Poll

**Server**

<img width="1267" height="417" alt="image" src="https://github.com/user-attachments/assets/a4f1d4f0-134a-4db3-b4b4-394b37cbf165" />


**Client 1**

<img width="827" height="279" alt="image" src="https://github.com/user-attachments/assets/94c231b1-58e8-4f69-9396-72cbf10d9108" />


**Client 2**

<img width="895" height="493" alt="image" src="https://github.com/user-attachments/assets/af493c2c-f5ce-4cf8-a7d8-cbdc595a0efb" />


**Client 3**

<img width="864" height="301" alt="image" src="https://github.com/user-attachments/assets/a0bce2f9-2a6c-47d7-9484-368a2a083f15" />


**Files**

<img width="360" height="332" alt="image" src="https://github.com/user-attachments/assets/3a5904f5-edbf-4d27-86b2-679725bf81b2" />


### Server Sync

**Server**

<img width="889" height="263" alt="image" src="https://github.com/user-attachments/assets/63bb53fd-4cab-467b-9e80-65495cba9c60" />


**Client 1**

<img width="816" height="372" alt="image" src="https://github.com/user-attachments/assets/d9d900d1-21a0-4f54-846c-835c411f7b1b" />


**Client 2**

<img width="823" height="185" alt="image" src="https://github.com/user-attachments/assets/7e271e35-0e5b-4287-add1-097b48db6d51" />


**Files**

<img width="351" height="387" alt="image" src="https://github.com/user-attachments/assets/92229ee2-3453-4392-badc-16711dff30f3" />
