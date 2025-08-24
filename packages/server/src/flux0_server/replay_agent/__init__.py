from lagom import Container

from .replay_agent import ReplayAgentRunner


async def init_module(container: Container) -> None:
    container[ReplayAgentRunner] = ReplayAgentRunner


async def shutdown_module() -> None:
    print("Shutdown!")
