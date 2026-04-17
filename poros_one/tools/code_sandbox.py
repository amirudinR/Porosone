import os
import tempfile
import subprocess
from poros_one.security.hitl_gateway import ActionGateway

class CodeSandbox:
    """
    Eksekusi kode secara dinamis.
    Untuk keamanan, implementasi ini membatasi waktu eksekusi (timeout) dan memisahkan proses (subprocess).
    Di level produksi yang sesungguhnya, ini harus dijalankan di dalam Docker Container terpisah.
    """

    @staticmethod
    def run_python_safely(code_string: str) -> str:
        """
        Menjalankan kode Python string dalam environment terpisah.
        Menangkap stdout/stderr atau timeout. (Level 2).
        """
        try:
            ActionGateway.check_action("run_code", "Mengeksekusi kode Python kustom secara dinamis.")

            # Tulis kode LLM ke file temporary
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as temp_file:
                temp_file.write(code_string)
                temp_file_path = temp_file.name

            try:
                # Jalankan subprocess terisolasi dari proses utama agen
                # timeout 10 detik agar kode infinite loop tidak membuat agen hang
                result = subprocess.run(
                    ['python', temp_file_path],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                output = result.stdout
                error = result.stderr

                if result.returncode == 0:
                    return f"Eksekusi Berhasil.\\n[Output]:\\n{output.strip()}"
                else:
                    return f"Eksekusi Gagal (Syntax/Runtime Error).\\n[Error]:\\n{error.strip()}"

            except subprocess.TimeoutExpired:
                return "Eksekusi Gagal: Timeout (Kode memakan waktu lebih dari 10 detik)."
            finally:
                # Bersihkan file temporary
                if os.path.exists(temp_file_path):
                    os.remove(temp_file_path)

        except Exception as e:
            return f"Error sistem Sandbox: {e}"