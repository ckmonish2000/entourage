import os
from openai import OpenAI
from . import config
from .tools import tools

class LLM:
    def __init__(self):
        self.client = OpenAI()
    
    def generate(self,*,prompt):
        response = self.client.responses.create(
            model = config.MODEL_NAME,
            temperature= config.TEMPERATURE,
            input = prompt,
            stream=False,
            tools=tools,
            tool_choice='auto'
        )
        return response.output_text

    def stream(self,*,prompt):
        response = self.client.responses.create(
            model = config.MODEL_NAME,
            temperature= config.TEMPERATURE,
            input = prompt,
            stream=True,
            tools=tools,
            tool_choice='auto'
        )
        for chunk in response:
            yield chunk
