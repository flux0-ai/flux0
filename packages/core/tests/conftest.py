import pytest
from flux0_core.contextual_correlator import ContextualCorrelator
from flux0_core.logging import ILogger, Logger


@pytest.fixture
def correlator() -> ContextualCorrelator:
    return ContextualCorrelator()


@pytest.fixture
def logger(correlator: ContextualCorrelator) -> ILogger:
    return Logger(correlator=correlator)
