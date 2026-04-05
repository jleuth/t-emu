from openai import OpenAI
from config import Conf
import os

class Llm:

    def __init__(self):
        self._client = OpenAI()
        self._config = Conf.load()


    def request_response(self, userInput):
        sys_prompt = os.open(self._config.current_instructions_path)

        response = client.responses.create(
            model=self._config.current_model,
            instructions=sys_prompt,
            input=userInput,
        )

        return response

        