from typing import override

from flux0_core.agent_runners.api import AgentRunner, AgentRunnerFactory
from flux0_core.agents import AgentType
from lagom import Container


class ContainerAgentRunnerFactory(AgentRunnerFactory):
    def __init__(self, container: Container) -> None:
        self.container = container

    @override
    def create_runner(self, agent_type: AgentType) -> AgentRunner:
        for defi in self.container.defined_types:
            if not isinstance(defi, type):
                continue
            if issubclass(defi, AgentRunner) and getattr(defi, "agent_type") == agent_type:
                return self.container[defi]
        raise ValueError(f"No engine found for agent type {agent_type}")
