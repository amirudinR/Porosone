# 🧠 Poros One
> **The Autonomous Continuous Learning AI Agent**

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)]()
[![Code Style: Black](https://img.shields.io/badge/Code%20Style-Black-000000.svg)]()

**Poros One** adalah agen AI otonom yang didesain untuk belajar dan mengeksekusi tugas secara terus-menerus. Berbeda dengan asisten konvensional, Poros One memiliki "Nyawa" (*Long-Term Memory*) sendiri yang berjalan 100% lokal dan mengadopsi mekanisme *Smart Memory Consolidation* agar tidak mengalami pembengkakan data atau "kepunahan ingatan" (*catastrophic forgetting*).

---

## 🌟 Fitur Utama (Core Features)

| Fitur | Deskripsi |
| :--- | :--- |
| **🧠 Smart Memory Consolidation** | Mengekstrak raw logs menjadi *core knowledge* menggunakan ChromaDB. Nyawa tidak akan membengkak, stabil di ukuran puluhan MB. |
| **🛡️ Human-in-the-Loop (HitL) Security** | Sistem *ActionGateway* mengamankan eksekusi OS dan API eksternal. Tindakan kritis (Level 3) wajib disetujui pengguna (Y/N) di terminal. |
| **🔒 Digital Rights Management (DRM)** | Nyawa diekspor dalam format terenkripsi `.poros` (AES-256) dan terikat dengan **Hardware ID** (*Anti-Piracy/Theft*). |
| **🔄 Dual-Node Soul Sync** | Sinkronisasi mulus via REST API (FastAPI) untuk transfer "Nyawa" antara Node PC dan Node Android. |
| **⚙️ ReAct Cognitive Loop** | Berpikir (*Reason*), Bertindak (*Act*), dan Mengobservasi (*Observe*) menggunakan LLM canggih via `litellm`. |

---

## 🏗️ Arsitektur Dual-Node

Poros One dirancang untuk beroperasi secara simbiotik pada dua perangkat (*nodes*):

1. **Sang Pertapa (Node Android)** 📱
   - **Tugas:** Belajar, membaca jurnal, dan memproses data ringan 24/7.
   - **Environment:** Termux (CLI based).
   - **Karakteristik:** Sangat hemat daya, tidak memiliki akses *heavy tools* (seperti Browser/OS control). Fokus mengkompresi memori (Consolidation).

2. **Sang Eksekutor (Node PC)** 💻
   - **Tugas:** Mengerjakan instruksi berat, coding, riset web, dan modifikasi *file system*.
   - **Environment:** Desktop (Windows/Linux/Mac).
   - **Karakteristik:** Akses penuh ke seluruh `tools` namun diikat erat oleh HitL Gateway.

Mereka bertukar ingatan melalui *FastAPI Local Sync Server* menggunakan file `.poros`.

---

## 🚀 Cara Instalasi (Installation)

### Prasyarat (Prerequisites)
- **Node.js** (v14+ untuk NPM CLI wrapper)
- **Python 3.10+** (Pastikan Python sudah ditambahkan ke `PATH` OS/Windows Anda)

### Menggunakan `npm` (Local Install)
1. *Clone* repositori ini:
   ```bash
   git clone https://github.com/yourusername/poros-one.git
   cd poros-one
   ```
2. Instal secara global menggunakan `npm` (Ini akan mengotomatisasi instalasi *dependencies* Python via `pip`):
   ```bash
   npm install -g .
   ```
3. Install Playwright browser binaries (opsional, jika tools Web Browser dibutuhkan):
   ```bash
   playwright install chromium
   ```
4. Buat file `.env` di root direktori Anda dan isi kredensial yang dibutuhkan:
   ```env
   OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
   TELEGRAM_BOT_TOKEN=123456789:ABCDEFGHIJKLMNOPQRSTUVWXYZ
   TELEGRAM_CHAT_ID=987654321
   POROS_MASTER_PASSPHRASE=rahasia_negara_123
   ```

---

## 💻 Cara Penggunaan (Usage)

Setelah instalasi berhasil, command global `poros` akan tersedia di terminal Anda.

### Menjalankan Node PC (Sang Eksekutor)
Cukup ketik perintah berikut di terminal Anda untuk masuk ke *Interactive ReAct Loop*:
```bash
poros
```
*Contoh Prompt:* `"Tolong cari informasi terbaru tentang framework FastAPI di internet, lalu rangkum dalam file ringkasan.txt"`

### Menjalankan Node Android (Sang Pertapa & Sync Server)
Untuk menjalankan mode hemat daya yang hanya menjalankan *Memory Engine* dan mendengarkan permintaan sinkronisasi nyawa:
```bash
python run_android_node.py
```
*(Server akan berjalan secara default di port 8000).*

---

*Dibuat dengan ❤️ oleh AI Architect & Lead Programmer.*