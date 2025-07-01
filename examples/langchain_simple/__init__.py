from lagom import Container

from .agent import LangChainAgentRunner


async def init_module(container: Container) -> None:
    container[LangChainAgentRunner] = LangChainAgentRunner


async def shutdown_module() -> None: ...
