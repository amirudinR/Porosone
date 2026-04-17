class ActionGateway:
    """
    HitL (Human-in-the-Loop) Security Gateway.
    Mengatur otorisasi tindakan agen AI berdasarkan tingkat risiko.
    """

    # Mapping level keamanan untuk setiap kategori tindakan
    ACTION_LEVELS = {
        "search_text": 1,
        "calculate": 1,
        "read_file": 1,
        "create_file": 2,
        "create_folder": 2,
        "interact_web": 2,
        "run_code": 2,
        "delete_file": 3,
        "send_message": 3,
        "modify_os_config": 3,
        "ask_user_help": 3
    }

    @classmethod
    def check_action(cls, action_name: str, action_details: str = "") -> bool:
        """
        Memeriksa apakah sebuah tindakan diizinkan untuk dieksekusi.

        Args:
            action_name: Nama tindakan (misal: 'search_text', 'delete_file').
            action_details: Detail tambahan mengenai tindakan tersebut.

        Returns:
            bool: True jika diizinkan, raise PermissionError jika ditolak.
        """
        level = cls.ACTION_LEVELS.get(action_name, 3) # Default ke level tertinggi (paling aman) jika tidak terdaftar

        if level == 1:
            # Level 1 (Aman): Langsung eksekusi
            print(f"[GATEWAY - L1] Mengizinkan secara otomatis: {action_name}")
            return True

        elif level == 2:
            # Level 2 (Risiko Sedang): Langsung eksekusi, tapi print warning
            print(f"\\n[WARNING GATEWAY - L2] Tindakan berisiko sedang dijalankan: {action_name} | Detail: {action_details}")
            return True

        elif level == 3:
            # Level 3 (Kritis): Wajib meminta izin pengguna via terminal
            print(f"\\n[CRITICAL GATEWAY - L3] PERINGATAN KEAMANAN TERTINGGI")
            print(f"Agen Poros One meminta izin untuk mengeksekusi: {action_name}")
            print(f"Detail: {action_details}")

            # Meminta input (Dalam implementasi produksi ini bisa diteruskan ke UI/WebSocket)
            while True:
                response = input("Mas Amir, izinkan tindakan ini? [Y/N]: ").strip().upper()
                if response == 'Y':
                    print("[GATEWAY] Tindakan diizinkan oleh sistem.")
                    return True
                elif response == 'N':
                    print("[GATEWAY] Tindakan diblokir.")
                    raise PermissionError(f"Tindakan {action_name} DITOLAK oleh pengguna.")
                else:
                    print("Input tidak valid. Harap ketik 'Y' untuk Yes atau 'N' untuk No.")
