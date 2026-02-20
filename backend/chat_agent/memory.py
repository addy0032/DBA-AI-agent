from typing import Dict, List
from threading import Lock
from models.chat_models import ChatAgentState
from config.settings import settings
import time

class ChatMemoryManager:
    """Manages short-term conversation context for SQL Chat Agent."""
    def __init__(self):
        self._memory_store: Dict[str, List[Dict[str, str]]] = {}
        self._lock = Lock()
        
    def add_message(self, session_id: str, role: str, content: str):
        with self._lock:
            if session_id not in self._memory_store:
                self._memory_store[session_id] = []
                
            self._memory_store[session_id].append({
                "role": role,
                "content": content,
                "timestamp": time.time()
            })
            
            # Slide window to prevent context limits blowing up
            if len(self._memory_store[session_id]) > settings.CHAT_MEMORY_WINDOW:
                # Keep last N messages
                self._memory_store[session_id] = self._memory_store[session_id][-settings.CHAT_MEMORY_WINDOW:]

    def get_history(self, session_id: str) -> List[Dict[str, str]]:
        with self._lock:
            return self._memory_store.get(session_id, [])
            
    def clear_session(self, session_id: str):
        with self._lock:
            if session_id in self._memory_store:
                del self._memory_store[session_id]

chat_memory = ChatMemoryManager()
