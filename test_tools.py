import os
import builtins
from poros_one.tools.os_manager import OSManager

def test_os_manager():
    test_file = "test_file.txt"

    # 1. Test Write File (Level 2)
    print("\\n--- TEST 1: Write File ---")
    res_write = OSManager.write_file(test_file, "Ini isi file testing.")
    print(res_write)
    assert os.path.exists(test_file)

    # 2. Test Read File (Level 1)
    print("\\n--- TEST 2: Read File ---")
    res_read = OSManager.read_file(test_file)
    print(res_read)
    assert "Ini isi file testing" in res_read

    # 3. Test Delete File (Level 3 - Approved)
    print("\\n--- TEST 3: Delete File (Disetujui) ---")
    original_input = builtins.input
    builtins.input = lambda prompt: 'Y'
    try:
        res_del = OSManager.delete_file(test_file)
        print(res_del)
        assert not os.path.exists(test_file)
    finally:
        builtins.input = original_input

    # 4. Test Delete File (Level 3 - Denied)
    print("\\n--- TEST 4: Delete File (Ditolak) ---")
    # Buat file lagi
    OSManager.write_file(test_file, "File untuk dihapus.")
    builtins.input = lambda prompt: 'N'
    try:
        try:
            OSManager.delete_file(test_file)
            assert False, "Harusnya raise PermissionError"
        except PermissionError as e:
            print(f"Berhasil diblokir: {e}")
            assert os.path.exists(test_file)
    finally:
        builtins.input = original_input
        # Bersihkan sisa file
        if os.path.exists(test_file):
            os.remove(test_file)

if __name__ == "__main__":
    test_os_manager()