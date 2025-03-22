from typing import List

from pydantic import BaseModel
from openai import AsyncOpenAI

from base.logger import logger
from base.schema import Message


class LLM:
    def __init__(self, model: str, api_key: str, base_url: str):
        self.model = model
        self.api_key = api_key
        self.base_url = base_url
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

    async def ask_tool(self, system_messages: List[Message], user_messages: List[Message], tools: []):
        formatted_messages = []
        if system_messages:
            for message in system_messages:
                formatted_messages.append(message.to_dict())
        for message in user_messages:
            formatted_messages.append(message.to_dict())

        logger.info("messages: {}".format(formatted_messages))
        logger.info("tools: {}".format(tools))

        params = {
            "model": self.model,
            "messages": formatted_messages,
            "tools": tools,
        }
        response2 = await self.client.chat.completions.create(**params)
        logger.info("llm response: {}".format(response2))

        return response2.choices[0].message