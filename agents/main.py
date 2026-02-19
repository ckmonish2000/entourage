import os

from prompts.system_prompt import system_prompt
from llm import LLM
import config

def main():
    llm = LLM()
    response = llm.generate(prompt='hey')
    print(response)

    



if __name__ == "__main__":
    main()