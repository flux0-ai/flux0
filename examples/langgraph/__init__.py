from lagom import Container

from .weather_agent import WeatherAgentRunner


async def init_module(container: Container) -> None:
    container[WeatherAgentRunner] = WeatherAgentRunner


async def shutdown_module() -> None:
    print("Shutdown!")
