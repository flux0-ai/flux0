from flux0_core.contextual_correlator import ContextualCorrelator


def test_correlation_scopes() -> None:
    correlator = ContextualCorrelator()

    # Initially, correlation_id should be the default "<main>"
    assert correlator.correlation_id == "<main>"

    # Enter first scope "user"
    with correlator.scope("user"):
        assert correlator.correlation_id == "user"

        # Enter nested scope "session"
        with correlator.scope("session"):
            assert correlator.correlation_id == "user::session"

            # Enter further nested scope "action"
            with correlator.scope("action"):
                assert correlator.correlation_id == "user::session::action"

            # After exiting "action", back to "user::session"
            assert correlator.correlation_id == "user::session"

        # After exiting "session", back to "user"
        assert correlator.correlation_id == "user"

    # After exiting all scopes, the default should be restored
    assert correlator.correlation_id == "<main>"


def test_unique_instance_ids() -> None:
    """
    Ensure each instance of Correlator has a unique generated ID.
    """
    c1 = ContextualCorrelator()
    c2 = ContextualCorrelator()

    assert c1._instance_id != c2._instance_id  # Ensure different IDs
    assert isinstance(c1._instance_id, str) and len(c1._instance_id) > 0  # Ensure non-empty ID
    assert isinstance(c2._instance_id, str) and len(c2._instance_id) > 0  # Ensure non-empty ID


def test_isolated_contexts() -> None:
    """
    Ensure that different Correlator instances do not share context.
    """
    c1 = ContextualCorrelator()
    c2 = ContextualCorrelator()

    assert c1.correlation_id == "<main>"
    assert c2.correlation_id == "<main>"

    with c1.scope("A"):
        assert c1.correlation_id == "A"
        assert c2.correlation_id == "<main>"  # c2 should remain unaffected

        with c2.scope("B"):
            assert c1.correlation_id == "A"  # c1 should remain unaffected
            assert c2.correlation_id == "B"

    assert c1.correlation_id == "<main>"
    assert c2.correlation_id == "<main>"
