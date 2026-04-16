import os
import requests
from poros_one.security.hitl_gateway import ActionGateway
from dotenv import load_dotenv

# Muat variabel environment dari file .env (jika ada)
load_dotenv()

class Communicator:
    """
    Tool untuk berinteraksi dengan aplikasi pesan eksternal (Telegram).
    """

    @staticmethod
    def send_telegram_message(message: str) -> str:
        """
        Mengirim pesan Telegram (Level 3 - Kritis).
        Token dan Chat ID diambil secara eksklusif dari environment variables.
        """
        try:
            ActionGateway.check_action("send_message", f"Kirim pesan Telegram: {message}")

            bot_token = os.environ.get("TELEGRAM_BOT_TOKEN")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID")

            if not bot_token or not chat_id:
                return "Error: Konfigurasi TELEGRAM_BOT_TOKEN atau TELEGRAM_CHAT_ID tidak ditemukan di environment variables."

            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                "chat_id": chat_id,
                "text": message
            }

            response = requests.post(url, json=payload)
            response.raise_for_status()

            return "Pesan Telegram berhasil dikirim."

        except requests.exceptions.RequestException as e:
            return f"Gagal mengirim pesan Telegram via API: {e}"
        except Exception as e:
            return f"Operasi pengiriman pesan dibatalkan atau gagal: {e}"