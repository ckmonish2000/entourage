import os 
from dotenv import load_dotenv
from pathlib import Path

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(ENV_PATH)

MODEL_NAME = os.getenv('OPENAI_MODEL')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
TEMPRATURE = 0.4

MAX_ITERATIONS = 5

