import json
from ..llm.client import LLMClient
from ..llm.types import ChunkType, ItemType
from ..prompts.templates import system_prompt
from .conversation import Conversation
from .config import MAX_ITERATIONS
from .types import MessageRole
from ..tools.executor import execute_tool


class Agent:
    def __init__(self, system_prompt_text=None):
        self.llm = LLMClient()
        prompt = system_prompt_text if system_prompt_text else system_prompt
        self.conversation = Conversation(prompt)
        self.tool_calls = []

    def process_message(self, user_message: str, *, stream: bool = True):
        """Public method to process a user message"""
        self.conversation.add_message(MessageRole.USER, user_message)

        if stream:
            return self._stream_response()
        else:
            return self._generate_response()

    async def _generate_response(self):
        """Internal Method to handle non-streaming responses with tool support"""
        iteration = 0
        final_response = ""

        while iteration < MAX_ITERATIONS:
            response = self.llm.generate(prompt=self.conversation.get_messages())
            iteration += 1

            # Check if response contains tool calls
            has_tool_calls = hasattr(response, 'output') and any(
                item.type == ItemType.FUNCTION_CALL
                for item in getattr(response.output, 'items', [])
            )

            if has_tool_calls:
                # Process each tool call
                for item in response.output.items:
                    if item.type == ItemType.FUNCTION_CALL:
                        call_id = getattr(item, 'call_id', None)
                        tool_name = getattr(item, 'name', None)
                        args = self.parse_tool_call_argument(item)

                        if args is not None:
                            # Execute tool
                            tool_output = await execute_tool(tool_name, args)

                            # Update tool calls tracking
                            self._update_tool_call(
                                type="tool_call_done",
                                call_id=call_id,
                                name=tool_name,
                                arguments=args,
                                output=tool_output
                            )

                            # Add tool output to conversation
                            self.conversation.add_message(MessageRole.DEVELOPER, f"Tool output: {tool_output} analyse the output provided and respond to the user")

                # Continue loop to get assistant's response after tool execution
                continue
            else:
                # No tool calls, get text response and break
                final_response = getattr(response, 'output_text', '')
                if final_response:
                    self.conversation.add_message(MessageRole.ASSISTANT, final_response)
                break

        return final_response

    async def _stream_response(self):
        """Internal method to handle streaming responses with tool execution support.

        Processes streaming chunks from the LLM, handles tool calls, executes tools,
        and yields text deltas to the caller. Continues iteration until response
        completes or max iterations reached.
        """
        iteration = 0

        while iteration < MAX_ITERATIONS:
            try:
                response = self.llm.stream(prompt=self.conversation.get_messages())
                iteration += 1

                # keep track of streaming response
                agent_response = ""
                tool_calls = {}
                has_tool_calls = False
                for chunk in response:
                    chunk_result = await self._process_chunk(chunk)

                    if chunk_result is None:
                        continue

                    if chunk_result['type'] == 'text':
                        agent_response += chunk_result['delta']
                        yield chunk_result['delta']
                    if chunk_result['type'] == 'tool_call_added':
                        has_tool_calls = True
                    elif chunk_result['type'] == 'response_completed':
                        if not has_tool_calls and agent_response:
                            self.conversation.add_message(MessageRole.ASSISTANT, agent_response)
                        break

                # Continue loop if there were tool calls (to get assistant's response)
                # Break if no tool calls (conversation is complete)
                if not has_tool_calls:
                    break
            except Exception as e:
                error_message = f"\n❌ Error during response generation: {e}\n"
                yield error_message
                break

    async def _process_chunk(self, chunk):
        """Process a streaming chunk and route it to the appropriate handler.

        Routes chunks to specialized handlers based on chunk type:
        text deltas, tool call additions, tool call completions, or response completion.
        """
        if chunk.type == ChunkType.OUTPUT_TEXT_DELTA:
            return self._handle_text(chunk)
        elif chunk.type == ChunkType.OUTPUT_ITEM_ADDED:
            return self._handle_tool_call_added(chunk)
        elif chunk.type == ChunkType.OUTPUT_ITEM_DONE:
            return await self._handle_tool_call_done(chunk)
        elif chunk.type == ChunkType.RESPONSE_COMPLETED:
            return {'type': 'response_completed'}
        else:
            return {"type": "unknown"}


    def _handle_text(self, chunk):
        """Extract text delta from a streaming chunk.

        Returns a dictionary containing the text type and delta content.
        """
        return {
            "type": "text",
            "delta": chunk.delta
        }

    def _handle_tool_call_added(self, chunk):
        """Handle the addition of a new tool call in the streaming response.

        Extracts tool call metadata (call_id, name) and registers it in the
        tool_calls tracking list.
        """
        item = self._get_chunk_item(chunk)
        call_id = getattr(item, 'call_id', None)
        if item.type == ItemType.FUNCTION_CALL:
            tool_name = getattr(item, 'name', None)
            tool_call_data = {
                "type": "tool_call_added",
                "call_id": call_id,
                "name": tool_name
            }

            self._update_tool_call(
                **tool_call_data
            )
            return tool_call_data


    async def _handle_tool_call_done(self, chunk):
        """Handle completion of a tool call in the streaming response.

        Parses tool arguments, executes the tool, stores the output,
        and adds the result to conversation memory.
        """
        item = self._get_chunk_item(chunk)
        call_id = getattr(item, 'call_id', None)

        if item.type == ItemType.FUNCTION_CALL:
            index, tool_call = self._fetch_tool_call(call_id)

            if index is None:
                return {"type": "error", "message": "Tool call not found"}

            args = self.parse_tool_call_argument(item)

            if args is None:
                return {"type": "error", "message": "Failed to parse tool arguments"}

            tool_call_data = {
                "type": "tool_call_done",
                "call_id": call_id,
                "name": tool_call['name'],
                "arguments": args
            }

            tool_output = await execute_tool(tool_call['name'], args)

            self._update_tool_call(
                **tool_call_data,
                output=tool_output
            )

            self.conversation.add_message(MessageRole.DEVELOPER, f"Tool output: {tool_output}")

            return tool_call_data

    def _fetch_tool_call(self, call_id: str) -> tuple[int, dict]:
        """Find a tool call by its call_id in the tracking list.

        Returns the index and tool call dict if found, otherwise (None, None).
        """
        for index, tool_call in enumerate(self.tool_calls):
            if tool_call['call_id'] == call_id:
                return index, tool_call
        return None, None

    def _update_tool_call(self, type, call_id, name, arguments={}, output=None):
        """Update or add a tool call entry in the tracking list.

        If a tool call with the given call_id exists, it's updated.
        Otherwise, a new entry is appended.
        """
        index, tool_call = self._fetch_tool_call(call_id)
        tool_call_data = {
            "type": type,
            "call_id": call_id,
            "name": name,
            "arguments": arguments,
            "output": output
        }

        if index is not None:
            self.tool_calls[index] = tool_call_data
        else:
            self.tool_calls.append(tool_call_data)

    def get_conversation_history(self):
        """Return the full conversation history stored in memory.

        This includes system, user, assistant, and tool-related developer
        messages in chronological order.
        """
        return self.conversation.get_messages()

    def parse_tool_call_argument(self, item: object):
        """Parse tool call arguments from a streamed function-call item.

        Returns a decoded dict when valid JSON is present, otherwise ``None``.
        Invalid JSON is logged and treated as missing arguments.
        """
        # get the arguments from the tool call
        args = getattr(item, 'arguments', None)
        # parse the arguments
        if args is None:
            return None

        try:
            return json.loads(args)
        except json.JSONDecodeError as e:
            # Log the error and return None to prevent tool execution with invalid args
            print(f"Warning: Failed to parse tool arguments: {e}")
            return None

    def _get_chunk_item(self, chunk: object):
        """Safely extract ``item`` from a streaming chunk."""
        return getattr(chunk, 'item', None)
