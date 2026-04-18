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

    web_mode = False
    hitl_callback = None
    log_callback = None

    @classmethod
    def set_web_mode(cls, active: bool, hitl_cb=None, log_cb=None):
        cls.web_mode = active
        cls.hitl_callback = hitl_cb
        cls.log_callback = log_cb

    @classmethod
    def log(cls, message: str):
        if cls.web_mode and cls.log_callback:
            cls.log_callback(message)
        print(message)

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
            cls.log(f"[GATEWAY - L1] Mengizinkan secara otomatis: {action_name}")
            return True

        elif level == 2:
            # Level 2 (Risiko Sedang): Langsung eksekusi, tapi print warning
            cls.log(f"\\n[WARNING GATEWAY - L2] Tindakan berisiko sedang dijalankan: {action_name} | Detail: {action_details}")
            return True

        elif level == 3:
            # Level 3 (Kritis): Wajib meminta izin pengguna via terminal atau WebSocket
            cls.log(f"\\n[CRITICAL GATEWAY - L3] PERINGATAN KEAMANAN TERTINGGI")
            cls.log(f"Agen Poros One meminta izin untuk mengeksekusi: {action_name}")
            cls.log(f"Detail: {action_details}")

            if cls.web_mode and cls.hitl_callback:
                cls.log("Menunggu persetujuan HitL via Web Dashboard...")
                approved = cls.hitl_callback(action_name, action_details)
                if approved:
                    cls.log("[GATEWAY] Tindakan diizinkan oleh sistem via Web.")
                    return True
                else:
                    cls.log("[GATEWAY] Tindakan diblokir via Web.")
                    raise PermissionError(f"Tindakan {action_name} DITOLAK oleh pengguna.")
            else:
                # Meminta input via CLI terminal
                while True:
                    response = input("Mas Amir, izinkan tindakan ini? [Y/N]: ").strip().upper()
                    if response == 'Y':
                        cls.log("[GATEWAY] Tindakan diizinkan oleh sistem.")
                        return True
                    elif response == 'N':
                        cls.log("[GATEWAY] Tindakan diblokir.")
                        raise PermissionError(f"Tindakan {action_name} DITOLAK oleh pengguna.")
                    else:
                        cls.log("Input tidak valid. Harap ketik 'Y' untuk Yes atau 'N' untuk No.")
