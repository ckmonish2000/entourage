import json
from .llm import LLM
from .prompts.system_prompt import system_prompt
from .memory import Memory
from .config import MAX_ITERATIONS
from .tools.executor import execute_tool
from .constants import ChunkType, ItemType, MessageRole
class Loop:
    def __init__(self, system_prompt_text=None): 
        self.llm = LLM()
        prompt = system_prompt_text if system_prompt_text else system_prompt
        self.memory = Memory(prompt)
        self.last_tool_calls = []
    
    def process_message(self,user_message:str,*,stream:bool =True):
        """Public method to process a user message"""
        self.memory.add_message(MessageRole.USER, user_message)
        
        if stream:
            return self._stream_response()
        else:
            return self._generate_response()
    
    def _generate_response(self):
        """Internal Method to handle non-streaming responses"""
        response = self.llm.generate(prompt=self.memory.get_messages())
        return response
    
    def _stream_response(self):
        """Internal method to handle streaming responses"""
        iteration = 0

        while iteration < MAX_ITERATIONS:
            try:
                response = self.llm.stream(prompt=self.memory.get_messages())
                iteration += 1

                # keep track of streaming response
                agent_response = ""
                tool_calls = {}
                has_tool_calls = False
                for chunk in response:
                    if chunk.type == ChunkType.OUTPUT_TEXT_DELTA:
                        agent_response += chunk.delta
                        # yield the chunk to the caller
                        yield chunk.delta
                    if chunk.type == ChunkType.OUTPUT_ITEM_ADDED:
                        item = self._get_chunk_item(chunk)
                        # identify and store tool calls
                        if item.type == ItemType.FUNCTION_CALL:
                            call_id = getattr(item,'call_id',None)
                            tool_calls[call_id] = {"call_id":call_id,"name":getattr(item,'name',None)}
                            has_tool_calls = True
                    if chunk.type == ChunkType.OUTPUT_ITEM_DONE:
                        item = self._get_chunk_item(chunk)
                        # store tool call arguments
                        if item.type == ItemType.FUNCTION_CALL:
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
                                role=MessageRole.DEVELOPER,
                                content=f"Tool {tool_calls[call_id]['name']} executed successfully with result: {tool_result} respond back to user in friendly manner"
                            )
                    elif chunk.type == ChunkType.RESPONSE_COMPLETED:
                        # Only save assistant response if there was actual text (no tool calls)
                        if not has_tool_calls and agent_response:
                            self.memory.add_message(MessageRole.ASSISTANT, agent_response)
                        break

                # Continue loop if there were tool calls (to get assistant's response)
                # Break if no tool calls (conversation is complete)
                if not has_tool_calls:
                    break
            except Exception as e:
                error_message = f"\n❌ Error during response generation: {e}\n"
                yield error_message
                break

    def get_conversation_history(self):
        """Return the full conversation history stored in memory.

        This includes system, user, assistant, and tool-related developer
        messages in chronological order.
        """
        return self.memory.get_messages()
    
    def parse_tool_call_argument(self,item:object):
        """Parse tool call arguments from a streamed function-call item.

        Returns a decoded dict when valid JSON is present, otherwise ``None``.
        Invalid JSON is logged and treated as missing arguments.
        """
        # get the arguments from the tool call
        args = getattr(item,'arguments',None)
        # parse the arguments
        if args is None:
            return None

        try:
            return json.loads(args)
        except json.JSONDecodeError as e:
            # Log the error and return None to prevent tool execution with invalid args
            print(f"Warning: Failed to parse tool arguments: {e}")
            return None
    
    def _get_chunk_item(self,chunk:object):
        """Safely extract ``item`` from a streaming chunk."""
        return getattr(chunk,'item',None)

        
