from lagom import Container

from .agent import OpenAIChatAgentRunner


async def init_module(container: Container) -> None:
    container[OpenAIChatAgentRunner] = OpenAIChatAgentRunner


async def shutdown_module() -> None: ...
