import json
from poros_one.memory.soul_manager import SoulManager
from poros_one.security.hitl_gateway import ActionGateway
from poros_one.tools.os_manager import OSManager
from poros_one.tools.web_browser import WebBrowser
from poros_one.tools.communicator import Communicator
from poros_one.tools.code_sandbox import CodeSandbox
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

    def _think(self, prompt: str) -> dict:
        """
        THOUGHT: Mengambil konteks dari memori dan meminta LLM menentukan tindakan.
        Mengembalikan dictionary berupa action dan details.
        """
        print("\\n--- [THOUGHT] Sedang berpikir ---")

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
            # Fallback jika API gagal (misal untuk testing lokal tanpa key)
            return {"action": "ask_user_help", "details": f"Error internal LLM: {e}"}

    def _build_prompt(self, user_prompt: str, error_context: str = "") -> str:
        """Membangun prompt untuk siklus ReAct, termasuk konteks error jika ada."""
        # 1. Ambil memori terkait
        memories = self.soul_manager.retrieve_core_knowledge(user_prompt)
        memory_context = "\\n".join(memories) if memories else "Tidak ada ingatan relevan."

        reflection_block = ""
        if error_context:
            reflection_block = f"""
[PERINGATAN REFLEKSI]
Tindakan sebelumnya gagal dengan error:
{error_context}
Evaluasi kenapa ini terjadi, buat rencana perbaikan, dan coba eksekusi tindakan alternatif atau perbaiki parameter Anda.
"""

        prompt = f"""
Anda adalah Poros One, agen AI yang mandiri (The God Mode).
Ingatan relevan Anda:
{memory_context}

Tugas Pengguna: {user_prompt}
{reflection_block}

Pilih SATU tindakan yang paling sesuai dari daftar alat berikut:
1. read_file (details: filepath)
2. create_file (details: format json {{"filepath": "...", "content": "..."}})
3. delete_file (details: filepath)
4. search_text (details: query pencarian web pasif)
5. interact_web (details: format json {{"url": "...", "action_type": "click/fill", "selector": "...", "input_text": "opsional"}})
6. run_code (details: kode python untuk dieksekusi di sandbox)
7. send_message (details: pesan teks telegram)
8. ask_user_help (details: pertanyaan atau permintaan bantuan ke pengguna)

Berikan output murni dalam format JSON:
{{"action": "nama_tindakan", "details": "detail_tindakan_sesuai_format"}}
"""
        return prompt

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
            elif action_name == "interact_web":
                parsed = json.loads(details) if isinstance(details, str) else details
                observation = WebBrowser.interact_with_webpage(
                    parsed.get("url"),
                    parsed.get("action_type"),
                    parsed.get("selector"),
                    parsed.get("input_text")
                )
            elif action_name == "run_code":
                observation = CodeSandbox.run_python_safely(details)
            elif action_name == "ask_user_help":
                print(f"[ESCALATION] Agen meminta bantuan Anda: {details}")
                ActionGateway.check_action("ask_user_help", details)
                observation = "Tindakan dihentikan secara aman karena eskalasi pengguna."
            else:
                observation = f"Error: Tindakan tidak dikenal '{action_name}'"

            print(f"[OBSERVATION] {observation}")
            return observation

        except PermissionError as e:
            observation = f"Error Eksekusi Ditolak: {action_name} - {e}"
            print(f"[OBSERVATION] {observation}")
            return observation
        except Exception as e:
            observation = f"Error tidak terduga saat mengeksekusi {action_name}: {e}"
            print(f"[OBSERVATION] {observation}")
            return observation

    def run_task(self, user_prompt: str):
        """
        Menjalankan loop ReAct dengan Self-Reflection dan Auto-Correction.
        Maksimal 3 kali percobaan (retry) jika terjadi Error.
        """
        print(f"\\n=== MEMULAI TUGAS: {user_prompt} ===")

        max_retries = 3
        attempt = 0
        last_error = ""
        final_observation = ""
        last_action = ""

        while attempt < max_retries:
            attempt += 1
            if attempt > 1:
                print(f"\\n>>> [RETRY LOOP {attempt}/{max_retries}] Melakukan evaluasi ulang karena error sebelumnya...")

            # 1. Thought & Build Prompt
            prompt = self._build_prompt(user_prompt, last_error)
            decision = self._think(prompt)
            last_action = decision.get("action")

            # Jika LLM menyerah dan minta tolong
            if last_action == "ask_user_help":
                final_observation = self._act_and_observe(decision)
                break

            # 2. Action & Observation
            observation = self._act_and_observe(decision)

            # 3. Evaluasi apakah sukses atau perlu retry
            if "Error" in observation or "Gagal" in observation:
                last_error = observation
                final_observation = observation
            else:
                # Sukses
                last_error = "" # Bersihkan error agar tidak memicu kondisi FATAL di bawah
                final_observation = observation
                break

        if attempt == max_retries and last_error:
            print("\\n[FATAL] Agen gagal menyelesaikan tugas setelah batas maksimal retry. Menyerah.")
            # Otomatis eskalasi
            try:
                self.gateway.check_action("ask_user_help", f"Sistem menyerah karena: {last_error}")
            except PermissionError as e:
                print(f"[OBSERVATION] {e}")

        # Simpan pengalaman ke memori mentah (Raw Memory)
        print("\\n--- [MEMORY] Menyimpan Pengalaman ---")
        log_entry = f"User Request: {user_prompt} | Last Action: {last_action} | Result: {final_observation}"
        self.soul_manager.add_raw_memory(log_entry)

        print("=== TUGAS SELESAI ===")
