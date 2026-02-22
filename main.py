from pathlib import Path
from dotenv import load_dotenv
from cli import CLI
from agents.core import config

def boot():
    """Bootstrapping function to load environment variables and configuration"""
    env_path = Path(__file__).resolve().parent / ".env"
    load_dotenv(env_path)
    config.load_config_from_env()

def main():    
    boot()
    cli = CLI()
    cli.run()

if __name__ == "__main__":
    main()
