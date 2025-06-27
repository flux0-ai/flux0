from lagom import Container

from .static_agent import StaticAgentRunner


async def init_module(container: Container) -> None:
    container[StaticAgentRunner] = StaticAgentRunner


async def shutdown_module() -> None:
    print("Shutdown!")
