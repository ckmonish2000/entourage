import json
from .llm import LLM
from .prompts.system_prompt import system_prompt
from .memory import Memory
from .config import MAX_ITERATIONS
from .tools.executor import execute_tool
class Loop:
    def __init__(self, system_prompt_text=None): 
        self.llm = LLM()
        prompt = system_prompt_text if system_prompt_text else system_prompt
        self.memory = Memory(prompt)
        self.last_tool_calls = []
    
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
        iteration = 0
        
        while iteration < MAX_ITERATIONS:
            response = self.llm.stream(prompt=self.memory.get_message())
            iteration += 1

            # keep track of streaming response 
            agent_response = ""
            tool_calls = {}
            has_tool_calls = False
            for chunk in response:
                if chunk.type == "response.output_text.delta":
                    agent_response += chunk.delta
                    # yield the chunk to the caller
                    yield chunk.delta
                if chunk.type == "response.output_item.added":
                    item = getattr(chunk,'item',None)
                    # identify and store tool calls
                    if(item.type == "function_call"):
                        call_id = getattr(item,'call_id',None)
                        tool_calls[call_id] = {"call_id":call_id,"name":getattr(item,'name',None)}
                        has_tool_calls = True
                if chunk.type == 'response.output_item.done':
                    item = getattr(chunk,'item',None)
                    # store tool call arguments
                    if(item.type == "function_call"):
                        call_id = getattr(item,'call_id',None)
                        # parse and store the tool call arguments
                        args = self.parse_tool_call_argument(item)
                        tool_calls[call_id]['arguments'] = args
                        # store the tool call
                        self.last_tool_calls.append(tool_calls[call_id])
                        # execute the tool
                        tool_result = execute_tool(
                            tool_calls[call_id]['name'],
                            tool_calls[call_id]['arguments']
                        )
                        # mark tool call as completed by adding result to memory
                        self.memory.add_message(
                            role='developer',
                            content=str(tool_result)
                        )
                elif chunk.type == "response.completed":
                    # add the final response to the memory
                    self.memory.add_message('assistant', agent_response)
                    break
            if not has_tool_calls:
                break

    def get_conversation_history(self):
        """Internal method to get the conversation history"""
        return self.memory.get_message()
    
    def parse_tool_call_argument(self,item:object):
        """Internal method to parse the tool call arguments"""
        args = getattr(item,'arguments',None)
        if args is not None:
            return json.loads(args)
        else:
            return None

        

