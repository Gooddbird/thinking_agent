import asyncio

from agent.step_thinking_agent import StepThinkingAgent
from base.logger import logger


async def main():
    agent = StepThinkingAgent()
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
    except Exception as e:
        logger.error("agent exception occurred.")
        logger.exception(e)
    finally:
        await agent.cleanup()


if __name__ == "__main__":
    asyncio.run(main())