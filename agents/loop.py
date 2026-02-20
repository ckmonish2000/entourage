from llm import LLM
from prompts.system_prompt import system_prompt
from memory import Memory


class Loop:
    def __init__(self):
        self.llm = LLM()
        self.memory = Memory(system_prompt)
    
    def run(self):
        while True:
            user_question = input("You: ")
            self.memory.add_message('user',user_question)

            response = self.llm.stream(prompt=self.memory.get_message())
            
            agent_response = ""
            for chunk in response:
                if(chunk.type == "response.output_text.delta"):
                    print(f"{chunk.delta}", end="", flush=True)
                    agent_response += chunk.delta
                elif chunk.type == "response.completed":
                    print('\n')
                    self.memory.add_message('assistant',agent_response)
                    agent_response=""
            