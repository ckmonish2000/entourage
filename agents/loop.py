from .llm import LLM
from .prompts.system_prompt import system_prompt
from .memory import Memory
from .config import MAX_ITERATIONS
class Loop:
    def __init__(self, system_prompt_text=None): 
        self.llm = LLM()
        prompt = system_prompt_text if system_prompt_text else system_prompt
        self.memory = Memory(prompt)
    
    def process_message(self,user_message:str,*,stream:bool =True):
        """Public method to process a user message"""
        self.memory.add_message('user', user_message)
        
        if stream:
            return self._stream_response()
        else:
            return self._generate_response()
    
    def _generate_response(self):
        """Internal Method to handle non-streaming responses"""
        response = self.llm.generate(prompt=self.memory.get_message())
        return response
    
    def _stream_response(self):
        """Internal method to handle streaming responses"""
        response = self.llm.stream(prompt=self.memory.get_message())

        # keep track of streaming response 
        agent_response = ""
        for chunk in response:
            if chunk.type == "response.output_text.delta":
                agent_response += chunk.delta
                # yield the chunk to the caller
                yield chunk.delta
            elif chunk.type == "response.completed":
                # add the final response to the memory
                self.memory.add_message('assistant', agent_response)

    def get_conversation_history(self):
        """Internal method to get the conversation history"""
        return self.memory.get_message()