import sys
import os

# Add the current directory to sys.path to resolve 'poros_one' imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from poros_one.memory.soul_manager import SoulManager

def mock_litellm_completion(*args, **kwargs):
    class MockChoice:
        class MockMessage:
            content = "User is interested in Python programming and prefers modular code structures."
        message = MockMessage()
    class MockResponse:
        choices = [MockChoice()]
    return MockResponse()

def main():
    import litellm
    # Mock litellm to avoid needing an actual API key for this basic test
    litellm.completion = mock_litellm_completion

    print("Initializing SoulManager...")
    manager = SoulManager(db_path="./test_memory", model_name="mock-model")

    # Adjust buffer limit for testing
    manager.buffer_limit = 3

    print("Adding raw memories...")
    manager.add_raw_memory("I really like learning about Python.")
    manager.add_raw_memory("Modular code is much easier to maintain.")
    manager.add_raw_memory("I want to build an AI agent.")

    print(f"Remaining buffer size (should be 0 after consolidation): {len(manager.raw_memory_buffer)}")

    print("Retrieving core knowledge...")
    knowledge = manager.retrieve_core_knowledge("What does the user like?")
    print(f"Retrieved knowledge: {knowledge}")

if __name__ == "__main__":
    main()
