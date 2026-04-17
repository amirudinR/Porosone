import os
import shutil
import builtins
from poros_one.memory.soul_manager import SoulManager
from poros_one.core.agent_loop import PorosAgent

def mock_litellm_completion(*args, **kwargs):
    class MockMessage:
        # Menghapus mock 'Hapus file rahasia.txt' karena details ini yang dilempar langsung ke os.remove oleh OSManager,
        # sehingga harus valid nama file
        content = '{"action": "delete_file", "details": "rahasia.txt"}'
    class MockChoice:
        message = MockMessage()
    class MockResponse:
        choices = [MockChoice()]
    return MockResponse()

def setup_test_env():
    if os.path.exists("./test_agent_memory"):
        shutil.rmtree("./test_agent_memory")
    # Buat file dummy agar delete tidak error
    with open("rahasia.txt", "w") as f:
        f.write("test")

def cleanup_test_env():
    if os.path.exists("./test_agent_memory"):
        shutil.rmtree("./test_agent_memory")

def test_agent_loop_level_3():
    setup_test_env()

    # Mock litellm
    import litellm
    litellm.completion = mock_litellm_completion

    # Inisialisasi komponen
    manager = SoulManager(db_path="./test_agent_memory", model_name="mock-model")
    agent = PorosAgent(soul_manager=manager, model_name="mock-model")

    # Skenario 1: Level 3 (Kritis) - Pengguna menyetujui (Y)
    print("\\n\\n>>> SKENARIO 1: Pengguna menyetujui tindakan kritis (Y)")
    original_input = builtins.input
    builtins.input = lambda prompt: 'Y'
    try:
        agent.run_task("Tolong hapus file rahasia.txt karena sudah tidak dipakai")
        assert len(manager.raw_memory_buffer) == 1
        assert "Berhasil menghapus file" in manager.raw_memory_buffer[0].content
        print("PASS: Agen mengeksekusi setelah disetujui dan menyimpan memori.")
    finally:
        builtins.input = original_input

    # Skenario 2: Level 3 (Kritis) - Pengguna menolak (N)
    print("\\n\\n>>> SKENARIO 2: Pengguna menolak tindakan kritis (N)")
    # Mock input logic: Tolak delete_file (N), tapi izinkan ask_user_help (Y)
    def mock_input_deny_action(prompt_text):
        # "Mas Amir, izinkan tindakan ini?" does not contain action name in prompt string.
        # However, the test only checks for a denied outcome.
        # We can just allow all exceptions to be caught so the loop continues.
        return 'N'

    builtins.input = mock_input_deny_action
    try:
        # Re-create dummy agar test loop retry tidak terjebak "Error tidak ditemukan" yg mengganggu tes penolakan
        with open("rahasia.txt", "w") as f:
            f.write("test")

        agent.run_task("Tolong hapus file rahasia.txt lagi")

        # Karena ReAct loop mencoba ulang 3 kali saat error "Ditolak", maka buffer akan diisi hasil retry yg gagal.
        # Kita cek pesan memori mentah terakhir
        last_memory = manager.raw_memory_buffer[-1].content
        assert "Ditolak" in last_memory or "DITOLAK" in last_memory or "Error Eksekusi Ditolak" in last_memory
        print("PASS: Agen membatalkan eksekusi setelah ditolak dan menyimpan log penolakan di memori.")
    finally:
        builtins.input = original_input

    cleanup_test_env()

if __name__ == "__main__":
    test_agent_loop_level_3()