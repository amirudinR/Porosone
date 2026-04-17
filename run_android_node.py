import os
import threading
from dotenv import load_dotenv

from poros_one.memory.soul_manager import SoulManager
from poros_one.network.sync_manager import SoulSyncProtocol

def main():
    """
    Script Inisialisasi untuk Node Android (Sang Pertapa).
    Mode hemat daya: Hanya menjalankan Memory Manager dan Sync Server di background.
    Tidak ada tools OS atau Web Browser yang diload.
    """
    print("=== Memulai Poros One [Mode Android / Sang Pertapa] ===")

    # Memuat env vars jika ada (misal LLM API keys untuk konsolidasi memori lokal)
    load_dotenv()

    # 1. Inisialisasi Memori
    memory_dir = "./android_memory"
    print("Membangunkan SoulManager...")
    soul_manager = SoulManager(db_path=memory_dir)

    # 2. Persiapkan Protokol Sinkronisasi
    master_passphrase = os.environ.get("POROS_MASTER_PASSPHRASE", "rahasia_default_123")
    sync_protocol = SoulSyncProtocol(memory_dir=memory_dir)

    # 3. Jalankan Server Sinkronisasi di Background (menggunakan threading)
    # Gunakan port 8000 secara default
    port = int(os.environ.get("POROS_SYNC_PORT", 8000))

    server_thread = threading.Thread(
        target=sync_protocol.start_sync_server,
        args=(port, master_passphrase, "0.0.0.0"),
        daemon=True
    )
    server_thread.start()

    print(f"\\n[STATUS] Node Android Berjalan.")
    print(f"[STATUS] Menunggu koneksi sinkronisasi di Port {port}...")
    print(f"[INFO] Tekan Ctrl+C untuk mematikan node.\\n")

    # Biarkan main thread hidup
    try:
        server_thread.join()
    except KeyboardInterrupt:
        print("\\nMematikan Node Android...")

if __name__ == "__main__":
    main()