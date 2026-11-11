"""`tutor teacher propose --mode quiz` proposes a quiz set, as the API already could (demo rehearsal, 12 Nov)."""
from tutor import cli


def test_teacher_can_propose_a_quiz_set_from_the_cli(capsys):
    cli.main(["setup"])
    cli.main(["teacher", "propose", "--concept", "qe04", "--mode", "quiz"])
    out = capsys.readouterr().out
    assert "Proposed quiz set-" in out


def test_practice_stays_the_default(capsys):
    cli.main(["setup"])
    cli.main(["teacher", "propose", "--concept", "qe04"])
    assert "Proposed practice set-" in capsys.readouterr().out
