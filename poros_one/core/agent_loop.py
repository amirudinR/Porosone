import json
from poros_one.memory.soul_manager import SoulManager
from poros_one.security.hitl_gateway import ActionGateway
from poros_one.tools.os_manager import OSManager
from poros_one.tools.web_browser import WebBrowser
from poros_one.tools.communicator import Communicator
import litellm

class PorosAgent:
    """
    Inti dari agen Poros One.
    Menggabungkan Memori (SoulManager) dan Keamanan (ActionGateway) dalam siklus ReAct (Reason, Act, Observe).
    """

    def __init__(self, soul_manager: SoulManager, model_name: str = "gpt-3.5-turbo"):
        self.soul_manager = soul_manager
        self.model_name = model_name
        self.gateway = ActionGateway()

    def _think(self, user_prompt: str) -> dict:
        """
        THOUGHT: Mengambil konteks dari memori dan meminta LLM menentukan tindakan.
        Simulasi sederhana ini akan mengembalikan dictionary berupa action dan details.
        """
        print("\\n--- [THOUGHT] Sedang berpikir ---")
        # 1. Ambil memori terkait
        memories = self.soul_manager.retrieve_core_knowledge(user_prompt)
        memory_context = "\\n".join(memories) if memories else "Tidak ada ingatan relevan."
        print(f"Konteks Memori: {memory_context}")

        # 2. Promt LLM untuk menentukan tindakan
        prompt = f"""
Anda adalah Poros One, agen AI yang mandiri.
Ingatan relevan Anda:
{memory_context}

Tugas Pengguna: {user_prompt}

Pilih SATU tindakan yang paling sesuai dari daftar alat berikut:
1. read_file (details: filepath)
2. create_file (details: format json {{"filepath": "...", "content": "..."}})
3. delete_file (details: filepath)
4. search_text (details: query pencarian)
5. send_message (details: pesan teks)

Berikan output murni dalam format JSON:
{{"action": "nama_tindakan", "details": "detail_tindakan_sesuai_format"}}
"""

        # Simulasi LLM call
        try:
            response = litellm.completion(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            llm_output = response.choices[0].message.content.strip()

            # Bersihkan blok markdown JSON jika ada
            if llm_output.startswith("```json"):
                llm_output = llm_output[7:-3].strip()
            elif llm_output.startswith("```"):
                llm_output = llm_output[3:-3].strip()

            decision = json.loads(llm_output)
            print(f"Keputusan: {decision}")
            return decision

        except Exception as e:
            print(f"Gagal berpikir: {e}")
            # Fallback untuk simulasi jika API gagal/tidak diset
            if "hapus" in user_prompt.lower():
                return {"action": "delete_file", "details": user_prompt}
            else:
                return {"action": "search_text", "details": user_prompt}

    def _act_and_observe(self, decision: dict) -> str:
        """
        ACTION & OBSERVATION: Memeriksa otorisasi lalu memanggil tools yang sesuai.
        """
        action_name = decision.get("action", "")
        details = decision.get("details", "")

        print(f"\\n--- [ACTION] Mencoba mengeksekusi ---")

        try:
            # Otorisasi Gateway ditangani di dalam masing-masing method tools
            # Namun kita juga bisa memanggil pre-check jika diperlukan

            observation = ""

            # Eksekusi Tool Sebenarnya
            if action_name == "read_file":
                observation = OSManager.read_file(details)
            elif action_name == "create_file":
                try:
                    # Mem-parsing details JSON
                    parsed = json.loads(details) if isinstance(details, str) else details
                    observation = OSManager.write_file(parsed.get("filepath", ""), parsed.get("content", ""))
                except Exception:
                    # Fallback apabila LLM tidak memberikan format JSON yang sempurna
                    observation = OSManager.write_file("output.txt", str(details))
            elif action_name == "delete_file":
                observation = OSManager.delete_file(details)
            elif action_name == "search_text":
                observation = WebBrowser.search_and_summarize(details)
            elif action_name == "send_message":
                observation = Communicator.send_telegram_message(details)
            else:
                observation = f"Tindakan tidak dikenal: {action_name}"

            print(f"[OBSERVATION] {observation}")
            return observation

        except PermissionError as e:
            observation = f"Gagal mengeksekusi {action_name}. Alasan: {e}"
            print(f"[OBSERVATION] {observation}")
            return observation
        except Exception as e:
            observation = f"Error tidak terduga saat mengeksekusi {action_name}: {e}"
            print(f"[OBSERVATION] {observation}")
            return observation

    def run_task(self, user_prompt: str):
        """
        Menjalankan loop ReAct.
        """
        print(f"\\n=== MEMULAI TUGAS: {user_prompt} ===")

        # 1. Thought
        decision = self._think(user_prompt)

        # 2. Action & Observation
        observation = self._act_and_observe(decision)

        # 3. Simpan pengalaman ke memori mentah (Raw Memory)
        print("\\n--- [MEMORY] Menyimpan Pengalaman ---")
        log_entry = f"User Request: {user_prompt} | Action Attempted: {decision.get('action')} | Result: {observation}"
        self.soul_manager.add_raw_memory(log_entry)

        print("=== TUGAS SELESAI ===")
