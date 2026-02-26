import os

MODEL_NAME = None
OPENAI_API_KEY = None
TEMPERATURE = 0.4

MAX_ITERATIONS = 5

MAX_CONTEXT_TOKENS = 128000  # Adjust based on your model
COMPACTION_THRESHOLD = 0.8  # Trigger at 80%
MAX_CONSECUTIVE_TOOL_CALLS = 5   # Maximum number of consecutive tool calls before loop detection

def load_config_from_env():
    global MODEL_NAME, OPENAI_API_KEY
    MODEL_NAME = os.getenv('OPENAI_MODEL')
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


load_config_from_env()
