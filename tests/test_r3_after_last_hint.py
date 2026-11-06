"""TP-A1 to TP-A3: what the tutor does once every hint on an item is used."""


def _revisit(app, session):
    return app.graph.get_state({"configurable": {"thread_id": session}}).values.get("revisit", [])


def _use_every_hint(app, session):
    app.turn(session, "L-B", "practice")
    for _ in range(3):
        app.turn(session, "L-B", "hint")


def test_it_triggers_after_three_stages_and_two_wrong_attempts(app, published_set):
    _use_every_hint(app, "s-last-hint")
    first = app.turn("s-last-hint", "L-B", "x = 100")
    assert "used every hint" not in first["reply"]
    assert _revisit(app, "s-last-hint") == []
    second = app.turn("s-last-hint", "L-B", "x = 101")
    assert second["route"] == "grade"
    assert "used every hint" in second["reply"]
    assert len(_revisit(app, "s-last-hint")) == 1
    assert second["reply"].split("(Study plan")[0].count("?") == 1


def test_hints_alone_never_trigger_it(app, published_set):
    _use_every_hint(app, "s-hints-only")
    result = app.turn("s-hints-only", "L-B", "hint")
    assert "used every hint" not in result["reply"]
    assert _revisit(app, "s-hints-only") == []


def test_a_hint_request_also_triggers_it_once_both_conditions_hold(app, published_set):
    _use_every_hint(app, "s-last-hint-ask")
    app.turn("s-last-hint-ask", "L-B", "x = 100")
    app.turn("s-last-hint-ask", "L-B", "x = 101")
    result = app.turn("s-last-hint-ask", "L-B", "hint")
    assert "used every hint" in result["reply"]
    assert len(_revisit(app, "s-last-hint-ask")) == 1  # marked once, not twice


def test_solving_the_item_clears_the_revisit_mark(app, monkeypatch, published_set):
    _use_every_hint(app, "s-last-hint-solved")
    app.turn("s-last-hint-solved", "L-B", "x = 100")
    app.turn("s-last-hint-solved", "L-B", "x = 101")
    real_call = app._call

    def call(state, node, role, server, tool, args):
        if tool == "check_equivalence":
            return {"status": "correct", "scorable": True, "correct": True, "reason": None, "parsed": "{1}"}
        return real_call(state, node, role, server, tool, args)

    monkeypatch.setattr(app, "_call", call)
    app.turn("s-last-hint-solved", "L-B", "x = 102")
    assert _revisit(app, "s-last-hint-solved") == []
