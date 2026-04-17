import os
import sys
from dotenv import load_dotenv

from poros_one.memory.soul_manager import SoulManager
from poros_one.core.agent_loop import PorosAgent

def main():
    """
    Entry point untuk CLI global Poros One.
    Dijalankan melalui perintah `poros` di terminal.
    """
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
    print("[INFO] Ketik 'exit' atau 'quit' untuk keluar.\\n")

    # Interactive CLI Loop
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