import os
from poros_one.security.hitl_gateway import ActionGateway

class OSManager:
    """
    Kumpulan tools untuk berinteraksi dengan sistem operasi (File System).
    Terintegrasi dengan Human-in-the-Loop Gateway untuk validasi otorisasi.
    """

    @staticmethod
    def read_file(filepath: str) -> str:
        """
        Membaca isi file (Level 1 - Aman).
        """
        try:
            ActionGateway.check_action("read_file", f"Membaca file: {filepath}")
            if not os.path.exists(filepath):
                return f"Error: File {filepath} tidak ditemukan."

            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            return f"Error membaca file: {e}"

    @staticmethod
    def write_file(filepath: str, content: str) -> str:
        """
        Membuat atau menulis ulang file (Level 2 - Risiko Sedang).
        """
        try:
            ActionGateway.check_action("create_file", f"Menulis ke file: {filepath}")

            # Pastikan direktori ada
            os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return f"Berhasil menulis isi ke file: {filepath}"
        except Exception as e:
            return f"Error menulis file: {e}"

    @staticmethod
    def delete_file(filepath: str) -> str:
        """
        Menghapus file (Level 3 - Kritis, butuh persetujuan).
        """
        ActionGateway.check_action("delete_file", f"Menghapus file secara permanen: {filepath}")
        try:
            if not os.path.exists(filepath):
                return f"Error: File {filepath} tidak ditemukan."

            os.remove(filepath)
            return f"Berhasil menghapus file: {filepath}"
        except Exception as e:
            return f"Error menghapus file: {e}"