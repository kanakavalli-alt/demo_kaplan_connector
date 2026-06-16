# main.py
import os
from dotenv import load_dotenv

load_dotenv()

# ADK looks for a module-level variable named `agent` — this is required
from agents.root_agent import root_agent as agent