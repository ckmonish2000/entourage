import os

MODEL_NAME = None
OPENAI_API_KEY = None
TEMPERATURE = 0.4

MAX_ITERATIONS = 5

MAX_CONTEXT_TOKENS = 128000  # Adjust based on your model
COMPACTION_THRESHOLD = 0.0008  # Trigger at 80%

def load_config_from_env():
    global MODEL_NAME, OPENAI_API_KEY
    MODEL_NAME = os.getenv('OPENAI_MODEL')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


load_config_from_env()
