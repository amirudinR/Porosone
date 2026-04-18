import json
import litellm
from poros_one.memory.soul_manager import SoulManager
from poros_one.security.hitl_gateway import ActionGateway
from poros_one.core.agent.prompts import build_react_prompt
from poros_one.core.agent.executor import AgentExecutor

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
        ActionGateway.log("\\n--- [THOUGHT] Sedang berpikir ---")

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
            ActionGateway.log(f"Keputusan: {decision}")
            return decision

        except Exception as e:
            ActionGateway.log(f"Gagal berpikir: {e}")
            # Fallback jika API gagal (misal untuk testing lokal tanpa key)
            return {"action": "ask_user_help", "details": f"Error internal LLM: {e}"}

    def run_task(self, user_prompt: str):
        """
        Menjalankan loop ReAct dengan Self-Reflection dan Auto-Correction.
        Maksimal 3 kali percobaan (retry) jika terjadi Error.
        """
        ActionGateway.log(f"\\n=== MEMULAI TUGAS: {user_prompt} ===")

        max_retries = 3
        attempt = 0
        last_error = ""
        final_observation = ""
        last_action = ""

        while attempt < max_retries:
            attempt += 1
            if attempt > 1:
                ActionGateway.log(f"\\n>>> [RETRY LOOP {attempt}/{max_retries}] Melakukan evaluasi ulang karena error sebelumnya...")

            # 1. Thought & Build Prompt
            memories = self.soul_manager.retrieve_core_knowledge(user_prompt)
            memory_context = "\\n".join(memories) if memories else "Tidak ada ingatan relevan."
            prompt = build_react_prompt(user_prompt, memory_context, last_error)

            decision = self._think(prompt)
            last_action = decision.get("action")

            # Jika LLM menyerah dan minta tolong
            if last_action == "ask_user_help":
                final_observation = AgentExecutor.execute_action(last_action, decision.get("details", ""))
                break

            # 2. Action & Observation
            observation = AgentExecutor.execute_action(last_action, decision.get("details", ""))

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
            ActionGateway.log("\\n[FATAL] Agen gagal menyelesaikan tugas setelah batas maksimal retry. Menyerah.")
            # Otomatis eskalasi
            try:
                self.gateway.check_action("ask_user_help", f"Sistem menyerah karena: {last_error}")
            except PermissionError as e:
                ActionGateway.log(f"[OBSERVATION] {e}")

        # Simpan pengalaman ke memori mentah (Raw Memory)
        ActionGateway.log("\\n--- [MEMORY] Menyimpan Pengalaman ---")
        log_entry = f"User Request: {user_prompt} | Last Action: {last_action} | Result: {final_observation}"
        self.soul_manager.add_raw_memory(log_entry)

        ActionGateway.log("=== TUGAS SELESAI ===")
