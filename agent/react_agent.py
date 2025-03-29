from abc import ABC, abstractmethod
from contextlib import asynccontextmanager

from typing import List, Optional

from base.logger import logger
from base.schema import AgentState, Message, Memory, ROLE_TYPE

class ReActAgent(ABC):
    def __init__(self):
        self.max_step = 15
        self.current_step = 0
        self.state = AgentState.FREE
        self.memory = Memory()

    @abstractmethod
    async def think(self) -> bool:
        """Process current state and decide next action"""

    @abstractmethod
    async def act(self) -> str:
        """Execute decided actions"""

    @asynccontextmanager
    async def state_context(self, new_state: AgentState):
        """Context manager for safe agent state transitions.

        Args:
            new_state: The state to transition to during the context.

        Yields:
            None: Allows execution within the new state.

        Raises:
            ValueError: If the new_state is invalid.
        """
        if not isinstance(new_state, AgentState):
            raise ValueError(f"Invalid state: {new_state}")

        previous_state = self.state
        self.state = new_state
        try:
            yield
        except Exception as e:
            self.state = AgentState.ERROR  # Transition to ERROR on failure
            raise e
        finally:
            self.state = previous_state  # Revert to previous state


    def update_memory(
        self,
        role: ROLE_TYPE,  # type: ignore
        content: str,
        **kwargs,
    ) -> None:
        """Add a message to the agent's memory.

        Args:
            role: The role of the message sender (user, system, assistant, tool).
            content: The message content.
            **kwargs: Additional arguments (e.g., tool_call_id for tool messages).

        Raises:
            ValueError: If the role is unsupported.
        """
        message_map = {
            "user": Message.user_message,
            "system": Message.system_message,
            "assistant": Message.assistant_message,
            "tool": lambda content2, **kw: Message.tool_message(content2, **kw),
        }

        if role not in message_map:
            raise ValueError(f"Unsupported message role: {role}")

        msg_factory = message_map[role]
        msg = msg_factory(content, **kwargs) if role == "tool" else msg_factory(content)
        self.memory.add_message(msg)

    async def step(self) -> str:
        """Execute a single step: think and act."""
        should_act = await self.think()
        if not should_act:
            return "Thinking complete - no action needed"
        return await self.act()

    async def run(self, request: Optional[str] = None) -> str:

        if self.state != AgentState.FREE:
            raise RuntimeError("not free state")
        self.state = AgentState.RUNNING
        if request is not None:
            self.state = AgentState.FINISHED

        if request:
            self.update_memory("user", request)

        results: List[str] = []
        async with self.state_context(AgentState.RUNNING):
            while (
                self.current_step < self.max_step and self.state != AgentState.FINISHED
            ):
                self.current_step += 1
                logger.info(f"Executing step {self.current_step}/{self.max_step}")
                step_result = await self.step()

                results.append(f"Step {self.current_step}: {step_result}")

            if self.current_step >= self.max_step:
                self.current_step = 0
                self.state = AgentState.FREE
                results.append(f"Terminated: Reached max steps ({self.max_step})")

        return "\n".join(results) if results else "No steps executed"
