"""`tutor teacher propose --mode quiz` proposes a quiz set, as the API already could (demo rehearsal, 12 Nov).

Uses the session's seeded store (the `app` fixture). It never calls `tutor setup`, which deletes the shared state
directory and fails on Windows while other tests hold its database open.
"""
from tutor import cli


def test_teacher_can_propose_a_quiz_set_from_the_cli(app, capsys):
    cli.main(["teacher", "propose", "--concept", "qe04", "--mode", "quiz"])
    assert "Proposed quiz set-" in capsys.readouterr().out


def test_practice_stays_the_default(app, capsys):
    cli.main(["teacher", "propose", "--concept", "qe04"])
    assert "Proposed practice set-" in capsys.readouterr().out
