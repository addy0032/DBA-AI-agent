import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import settings
from utils.logger import setup_logger
from utils.db import get_db_connection
from models.db_models import MetricSnapshot
from models.api_models import Recommendation
from models.agent_models import AgentState
from data_collection.queries import ACTIVE_SESSIONS_QUERY
from data_collection.snapshot import snapshot_manager
from data_collection.poller import collector
from anomaly_detection.rules import AnomalyRules
from anomaly_detection.detector import detector
from llm.groq_client import groq_client
from agent.persona import DBA_SYSTEM_PROMPT
from agent.memory import anomaly_memory
from agent.graph import dba_agent
from api.routes import router
from api.main import app

def main():
    print("All imports successful! The backend modular architecture is structurally sound.")

if __name__ == "__main__":
    main()
