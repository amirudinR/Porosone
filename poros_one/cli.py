import os
import sys
from dotenv import load_dotenv

from poros_one.memory.soul_manager import SoulManager
from poros_one.core.agent_loop import PorosAgent

import argparse
from poros_one.security.hitl_gateway import ActionGateway
from poros_one.network.web_dashboard import WebDashboardServer

def main():
    """
    Entry point untuk CLI global Poros One.
    Dijalankan melalui perintah `poros` di terminal.
    """
    parser = argparse.ArgumentParser(description="Poros One - Autonomous Continuous Learning AI Agent")
    parser.add_argument("command", nargs="?", default="run", help="Perintah untuk dieksekusi (default: run)")
    parser.add_argument("--web", action="store_true", help="Jalankan antarmuka Local Web Dashboard UI")
    args = parser.parse_args()

    print("==================================================")
    print("      POROS ONE - Autonomous AI Agent Node PC     ")
    print("==================================================")

    # Load environment variables
    load_dotenv()

    # Inisialisasi Memori
    memory_dir = os.environ.get("POROS_MEMORY_DIR", "./poros_memory")
    try:
        soul_manager = SoulManager(db_path=memory_dir)
        agent = PorosAgent(soul_manager=soul_manager)
    except Exception as e:
        print(f"\\n[FATAL ERROR] Gagal menginisialisasi Poros One: {e}")
        sys.exit(1)

    print(f"\\n[INFO] Poros One siap. Memori dimuat dari: {memory_dir}")

    if args.web:
        # Mode Web Dashboard
        print("[INFO] Memulai Mode Web Dashboard...")
        dashboard = WebDashboardServer(agent)

        # Konfigurasi ActionGateway untuk menggunakan Web Callback
        ActionGateway.set_web_mode(
            active=True,
            hitl_cb=dashboard.trigger_hitl_approval_sync,
            log_cb=dashboard.stream_log_sync
        )

        try:
            dashboard.start(port=8000)
        except KeyboardInterrupt:
            print("\\nMematikan Web Dashboard Poros One. Sampai jumpa!")
    else:
        # Mode CLI Standar
        print("[INFO] Ketik 'exit' atau 'quit' untuk keluar.\\n")
        while True:
            try:
                user_input = input("Mas Amir > ").strip()

                if not user_input:
                    continue

                if user_input.lower() in ['exit', 'quit']:
                    print("Poros One offline. Sampai jumpa!")
                    break

                # Jalankan siklus ReAct berdasarkan prompt
                agent.run_task(user_input)

            except KeyboardInterrupt:
                print("\\nPoros One offline. Sampai jumpa!")
                break
            except Exception as e:
                print(f"\\n[ERROR] Terjadi kesalahan saat mengeksekusi tugas: {e}")

if __name__ == "__main__":
    main()