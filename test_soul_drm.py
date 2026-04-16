import os
import shutil
from poros_one.security.soul_drm import export_soul, import_soul, get_hardware_id

def setup_test_env():
    # Membuat direktori dummy untuk memory
    os.makedirs("dummy_memory", exist_ok=True)
    with open("dummy_memory/core_knowledge.json", "w") as f:
        f.write('{"rules": ["Be helpful", "Do not forget"]}')

    # Membuat file .env dummy yang harus diabaikan
    with open("dummy_memory/.env", "w") as f:
        f.write("OPENAI_API_KEY=rahasia_negara")

def cleanup_test_env():
    # Membersihkan semua file dan folder hasil test
    dirs_to_clean = ["dummy_memory", "imported_memory"]
    files_to_clean = ["test_soul.poros"]

    for d in dirs_to_clean:
        if os.path.exists(d):
            shutil.rmtree(d)

    for f in files_to_clean:
        if os.path.exists(f):
            os.remove(f)

def test_drm():
    setup_test_env()

    passphrase = "super_secure_password"
    poros_file = "test_soul.poros"
    import_dir = "imported_memory"

    try:
        # Test 1: Export (harus mengabaikan .env)
        print("--- Test 1: Export Soul ---")
        export_soul(db_path="dummy_memory", output_path=poros_file, passphrase=passphrase)
        assert os.path.exists(poros_file), "File .poros gagal dibuat!"
        print("PASS: Export berhasil.")

        # Test 2: Import sukses
        print("\\n--- Test 2: Import Soul (Passphrase Benar, HW ID Benar) ---")
        import_soul(poros_file_path=poros_file, extract_to_path=import_dir, passphrase=passphrase)
        assert os.path.exists(f"{import_dir}/core_knowledge.json"), "File data tidak terekstrak!"
        assert not os.path.exists(f"{import_dir}/.env"), "BAHAYA: File .env ikut terekstrak!"
        print("PASS: Import berhasil, .env aman tidak terbawa.")

        # Test 3: Import gagal (Passphrase salah)
        print("\\n--- Test 3: Import Soul (Passphrase Salah) ---")
        try:
            import_soul(poros_file_path=poros_file, extract_to_path=import_dir, passphrase="salah_password")
            assert False, "Seharusnya gagal karena password salah!"
        except ValueError as e:
            print(f"PASS: Import gagal seperti yang diharapkan: {e}")

        # Test 4: Import gagal (Hardware ID beda)
        print("\\n--- Test 4: Import Soul (Hardware ID Beda) ---")
        # Ekspor ulang dengan HW ID dummy "123456789"
        export_soul(db_path="dummy_memory", output_path=poros_file, passphrase=passphrase, target_hardware_id="123456789")
        try:
            import_soul(poros_file_path=poros_file, extract_to_path=import_dir, passphrase=passphrase)
            assert False, "Seharusnya gagal karena Hardware ID berbeda!"
        except PermissionError as e:
            print(f"PASS: Import gagal karena HW ID mismatch seperti yang diharapkan: {e}")

    finally:
        cleanup_test_env()

if __name__ == "__main__":
    test_drm()