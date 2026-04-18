import json
from poros_one.security.hitl_gateway import ActionGateway
from poros_one.tools.os_manager import OSManager
from poros_one.tools.web_browser import WebBrowser
from poros_one.tools.communicator import Communicator
from poros_one.tools.code_sandbox import CodeSandbox

class AgentExecutor:
    """
    Menangani eksekusi tindakan agen (ReAct's ACT) dengan memanggil tools yang sesuai
    berdasarkan keputusan dari LLM.
    """

    @staticmethod
    def execute_action(action_name: str, details: str | dict) -> str:
        """
        Mengeksekusi tool berdasarkan nama action dan menangani error-nya.

        Args:
            action_name: Nama tindakan yang dipilih LLM.
            details: Parameter untuk tindakan (string atau dict/JSON).

        Returns:
            str: Hasil observasi dari eksekusi.
        """
        ActionGateway.log(f"\\n--- [ACTION] Mencoba mengeksekusi ---")

        try:
            observation = ""

            # Eksekusi Tool Sebenarnya
            if action_name == "read_file":
                observation = OSManager.read_file(details)
            elif action_name == "create_file":
                try:
                    parsed = json.loads(details) if isinstance(details, str) else details
                    observation = OSManager.write_file(parsed.get("filepath", ""), parsed.get("content", ""))
                except Exception:
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
                ActionGateway.log(f"[ESCALATION] Agen meminta bantuan Anda: {details}")
                ActionGateway.check_action("ask_user_help", details)
                observation = "Tindakan dihentikan secara aman karena eskalasi pengguna."
            else:
                observation = f"Error: Tindakan tidak dikenal '{action_name}'"

            ActionGateway.log(f"[OBSERVATION] {observation}")
            return observation

        except PermissionError as e:
            observation = f"Error Eksekusi Ditolak: {action_name} - {e}"
            ActionGateway.log(f"[OBSERVATION] {observation}")
            return observation
        except Exception as e:
            observation = f"Error tidak terduga saat mengeksekusi {action_name}: {e}"
            ActionGateway.log(f"[OBSERVATION] {observation}")
            return observation