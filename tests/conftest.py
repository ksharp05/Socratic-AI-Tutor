import os
import tempfile

import pytest

# Every test run uses its own state directory, so tests never touch var/ used for manual testing.
os.environ["TUTOR_VAR_DIR"] = tempfile.mkdtemp(prefix="tutor-test-")
os.environ["TUTOR_LLM"] = "stub"


@pytest.fixture(scope="session")
def app():
    from tutor.seed import reset_and_seed
    from tutor.app import TutorApp
    reset_and_seed()
    application = TutorApp()
    yield application
    application.close()


@pytest.fixture(scope="session")
def published_set(app):
    proposal = app.propose_set("qe04")
    result = app.decide(proposal["set_id"], "approve", "T-001")
    assert result["status"] == "published"
    return {**proposal, **result}
