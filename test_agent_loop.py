import os
import shutil
import builtins
from poros_one.memory.soul_manager import SoulManager
from poros_one.core.agent_loop import PorosAgent

def mock_litellm_completion(*args, **kwargs):
    class MockMessage:
        content = '{"action": "delete_file", "details": "Hapus file rahasia.txt"}'
    class MockChoice:
        message = MockMessage()
    class MockResponse:
        choices = [MockChoice()]
    return MockResponse()

def setup_test_env():
    if os.path.exists("./test_agent_memory"):
        shutil.rmtree("./test_agent_memory")

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
        assert "Berhasil mengeksekusi delete_file" in manager.raw_memory_buffer[0].content
        print("PASS: Agen mengeksekusi setelah disetujui dan menyimpan memori.")
    finally:
        builtins.input = original_input

    # Skenario 2: Level 3 (Kritis) - Pengguna menolak (N)
    print("\\n\\n>>> SKENARIO 2: Pengguna menolak tindakan kritis (N)")
    builtins.input = lambda prompt: 'N'
    try:
        agent.run_task("Tolong hapus file rahasia.txt lagi")
        assert len(manager.raw_memory_buffer) == 2
        assert "Gagal mengeksekusi delete_file" in manager.raw_memory_buffer[1].content
        assert "DITOLAK oleh pengguna" in manager.raw_memory_buffer[1].content
        print("PASS: Agen membatalkan eksekusi setelah ditolak dan menyimpan log penolakan di memori.")
    finally:
        builtins.input = original_input

    cleanup_test_env()

if __name__ == "__main__":
    test_agent_loop_level_3()