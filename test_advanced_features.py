import os
import builtins
import json
from poros_one.tools.code_sandbox import CodeSandbox
from poros_one.core.agent_loop import PorosAgent
from poros_one.memory.soul_manager import SoulManager

def mock_litellm_completion_retry(*args, **kwargs):
    messages = kwargs.get("messages", [])
    prompt_content = messages[0]["content"] if messages else ""

    class MockMessage:
        content = ""
    class MockChoice:
        message = MockMessage()
    class MockResponse:
        choices = [MockChoice()]

    response = MockResponse()

    # Berikan error pertama, lalu setelah diprompt ulang, perbaiki.
    if "[PERINGATAN REFLEKSI]" not in prompt_content:
        # Percobaan pertama: Syntax Error
        response.choices[0].message.content = json.dumps({
            "action": "run_code",
            "details": "print('Halo Dunia" # Syntax error sengaja
        })
    else:
        # Percobaan kedua (Setelah Reflection): Kode Benar
        response.choices[0].message.content = json.dumps({
            "action": "run_code",
            "details": "print('Halo Dunia')" # Syntax benar
        })

    return response

def test_sandbox():
    print("\\n--- TEST 1: Sandbox Sukses ---")
    res = CodeSandbox.run_python_safely("print('Halo dari Sandbox')")
    print(res)
    assert "Halo dari Sandbox" in res

    print("\\n--- TEST 2: Sandbox Syntax Error ---")
    res_err = CodeSandbox.run_python_safely("print('Error)")
    print(res_err)
    assert "Eksekusi Gagal" in res_err

    print("\\n--- TEST 3: Sandbox Timeout ---")
    res_timeout = CodeSandbox.run_python_safely("import time\nwhile True:\n    time.sleep(1)")
    print(res_timeout)
    assert "Timeout" in res_timeout

def test_retry_loop():
    print("\\n--- TEST 4: Agent Retry Loop Reflection ---")
    import litellm
    litellm.completion = mock_litellm_completion_retry

    manager = SoulManager(db_path="./test_advanced_memory", model_name="mock-model")
    agent = PorosAgent(soul_manager=manager, model_name="mock-model")

    agent.run_task("Jalankan print hello world")

    assert len(manager.raw_memory_buffer) > 0
    # Memastikan observasi final sukses setelah diretry
    assert "Berhasil" in manager.raw_memory_buffer[0].content or "Eksekusi Berhasil" in manager.raw_memory_buffer[0].content

if __name__ == "__main__":
    test_sandbox()
    test_retry_loop()