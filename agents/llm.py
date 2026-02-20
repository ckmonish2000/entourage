import os
from openai import OpenAI
import config
class LLM:
    def __init__(self):
        self.client = OpenAI()
    
    def generate(self,*,prompt):
        response = self.client.responses.create(
            model = config.MODEL_NAME,
            temperature= config.TEMPRATURE,
            input = prompt,
            stream=False
        )
        return response.output_text

    def stream(self,*,prompt):
        response = self.client.responses.create(
            model = config.MODEL_NAME,
            temperature= config.TEMPRATURE,
            input = prompt,
            stream=True
        )
        for chunk in response:
            yield chunk
