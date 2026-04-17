import os
import time
import threading
import shutil
from fastapi.testclient import TestClient
from poros_one.network.sync_manager import SoulSyncProtocol
from poros_one.security.soul_drm import export_soul, get_hardware_id

def setup_test_env():
    os.makedirs("node_a_memory", exist_ok=True)
    with open("node_a_memory/core_knowledge.json", "w") as f:
        f.write('{"rules": ["Node A Initial Knowledge"]}')

    os.makedirs("node_b_memory", exist_ok=True)
    with open("node_b_memory/core_knowledge.json", "w") as f:
        f.write('{"rules": ["Node B Knowledge"]}')

def cleanup_test_env():
    for d in ["node_a_memory", "node_b_memory", "pulled_memory"]:
        if os.path.exists(d):
            shutil.rmtree(d)
    for f in os.listdir("."):
        if f.endswith(".poros"):
            os.remove(f)

def test_sync():
    setup_test_env()

    passphrase = "test_passphrase_123"

    # Inisialisasi Server Node A
    protocol_a = SoulSyncProtocol(memory_dir="node_a_memory")
    protocol_a.master_passphrase = passphrase
    protocol_a._setup_routes()
    client_a = TestClient(protocol_a.app) # Gunakan TestClient FastAPI untuk menghindari binding port asli

    # Inisialisasi Server Node B
    protocol_b = SoulSyncProtocol(memory_dir="node_b_memory")

    try:
        print("\\n--- TEST 1: PUSH (Client B mengirim ke Server A) ---")

        # 1. B mengekspor memorinya ke file poros
        export_soul("node_b_memory", "b_soul.poros", passphrase)

        # 2. B PUSH ke A
        # Simulasikan push via TestClient
        file_mtime = os.path.getmtime("b_soul.poros")
        from datetime import datetime
        timestamp_iso = datetime.fromtimestamp(file_mtime).isoformat()

        with open("b_soul.poros", "rb") as f:
            response = client_a.post(
                "/sync/push",
                headers={
                    "x-passphrase": passphrase,
                    "x-timestamp": timestamp_iso
                },
                files={"file": ("soul.poros", f, "application/octet-stream")}
            )

        print(f"Response PUSH: {response.status_code} - {response.json()}")
        assert response.status_code == 200

        # Verifikasi bahwa Node A sudah menimpa memorinya dengan konten B
        with open("node_a_memory/core_knowledge.json", "r") as f:
            content = f.read()
            assert "Node B Knowledge" in content
            print("PASS: Push berhasil. Memori Node A telah ditimpa dengan memori B.")

        print("\\n--- TEST 2: PULL (Client B menarik dari Server A) ---")
        # Simulasikan pull via TestClient
        hwid = get_hardware_id()
        response_pull = client_a.get(
            "/sync/pull",
            headers={
                "x-passphrase": passphrase,
                "x-target-hwid": hwid
            }
        )

        assert response_pull.status_code == 200
        with open("pulled_a_soul.poros", "wb") as f:
            f.write(response_pull.content)

        assert os.path.exists("pulled_a_soul.poros")
        print("PASS: Pull berhasil. Memori Node A telah diunduh sebagai file .poros.")

    finally:
        cleanup_test_env()

if __name__ == "__main__":
    test_sync()