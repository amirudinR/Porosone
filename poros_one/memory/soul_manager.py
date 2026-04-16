import os
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
import litellm
import chromadb
from pydantic import BaseModel

class MemoryEntry(BaseModel):
    timestamp: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class SoulManager:
    """
    SoulManager handles the "Life" or Long-Term Memory of Poros One.
    It manages raw memory storage and applies Smart Memory Consolidation
    to prevent memory bloating while keeping essential core rules and knowledge.
    """

    def __init__(self, db_path: str = "./poros_memory", model_name: str = "gpt-3.5-turbo"):
        """
        Initializes the SoulManager.

        Args:
            db_path: Path to the local ChromaDB storage directory.
            model_name: LLM model used for memory consolidation (via litellm).
        """
        self.db_path = db_path
        self.model_name = model_name
        self.raw_memory_buffer: List[MemoryEntry] = []
        self.buffer_limit = 20 # Number of raw memories before triggering consolidation

        # Initialize local vector DB for Core Knowledge
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)
        self.core_knowledge_collection = self.chroma_client.get_or_create_collection(name="core_knowledge")

        print(f"SoulManager initialized. DB Path: {self.db_path}, Consolidation Model: {self.model_name}")

    def add_raw_memory(self, content: str, metadata: Optional[Dict[str, Any]] = None):
        """
        Stores a raw interaction/experience into the memory buffer.
        Triggers consolidation if the buffer limit is reached.
        """
        entry = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            content=content,
            metadata=metadata or {}
        )
        self.raw_memory_buffer.append(entry)
        print(f"Added raw memory. Buffer size: {len(self.raw_memory_buffer)}/{self.buffer_limit}")

        if len(self.raw_memory_buffer) >= self.buffer_limit:
            self.consolidate_memory()

    def consolidate_memory(self):
        """
        Smart Memory Consolidation.
        Summarizes raw logs into dense, structured core rules/knowledge using LLM,
        and saves them into the local vector DB to maintain a small memory footprint.
        """
        if not self.raw_memory_buffer:
            return

        print("Starting Smart Memory Consolidation...")

        # Prepare context from raw memories
        memory_texts = [f"[{m.timestamp}] {m.content}" for m in self.raw_memory_buffer]
        combined_context = "\\n".join(memory_texts)

        # Prompt for the LLM to extract core rules/facts
        prompt = f"""
You are the memory consolidation module of an AI named Poros One.
Your task is to analyze the following raw memory logs and extract key facts, user preferences, and new rules.
Condense the information into a few dense, standalone sentences.
Discard any conversational filler or redundant information.
Do not lose essential knowledge.

Raw Logs:
{combined_context}

Condensed Core Knowledge:
"""

        try:
            # Call LLM via litellm
            response = litellm.completion(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )

            consolidated_text = response.choices[0].message.content.strip()

            if consolidated_text:
                # Save to local vector DB
                doc_id = f"core_rule_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                self.core_knowledge_collection.add(
                    documents=[consolidated_text],
                    metadatas=[{"source": "consolidation", "timestamp": datetime.now().isoformat()}],
                    ids=[doc_id]
                )
                print(f"Consolidation successful. Core Knowledge saved with ID: {doc_id}")
                print(f"Condensed Text: {consolidated_text}")

                # Clear buffer after successful consolidation
                self.raw_memory_buffer.clear()
            else:
                print("Consolidation yielded empty result. Buffer retained.")

        except Exception as e:
            print(f"Error during memory consolidation: {e}")
            # Keep the buffer intact if consolidation fails

    def retrieve_core_knowledge(self, query: str, n_results: int = 3) -> List[str]:
        """
        Retrieves relevant core knowledge from the local vector database based on a query.
        """
        try:
            results = self.core_knowledge_collection.query(
                query_texts=[query],
                n_results=n_results
            )
            # Flatten the results
            documents = results.get('documents', [[]])[0]
            return documents
        except Exception as e:
            print(f"Error retrieving core knowledge: {e}")
            return []
