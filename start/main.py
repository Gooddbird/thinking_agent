import asyncio

from agent.thinking_agent import ThinkingAgent
from base.logger import logger


async def main():
    agent = ThinkingAgent()
    try:
        await agent.init_tool()

        prompt = input("Enter your prompt: ")
        if not prompt.strip():
            logger.warning("Empty prompt provided.")
            return

        logger.warning("Processing your request...")
        await agent.run(prompt)
        logger.info("Request processing completed.")
    except KeyboardInterrupt:
        logger.warning("Operation interrupted.")

if __name__ == "__main__":
    asyncio.run(main())