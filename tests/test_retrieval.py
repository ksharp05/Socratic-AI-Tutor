"""Retrieval (R2): chunking, source refusal, RRF and the no-index fallback.

Every text here is synthetic, written for these tests; no NCERT text is used.
"""
import asyncio
import json

import pytest
from fastmcp import Client

from tutor.mcp_servers import textbook_kb
from tutor.retrieval import ingest
from tutor.retrieval.chunk import MAX_WORDS, chunk_pages, printed_page_of
from tutor.retrieval.hybrid import HybridRetriever, build_retriever, rrf
from tutor.retrieval.sources import RefusedSource, resolve
from tutor.retrieval.textnorm import repair_symbols, tokenize

PAGE_1 = """\
60                                    SAMPLE BOOK

                     9         WIDGET THEORY

9.1 Introduction

Widgets are small things that hum. This opening paragraph talks about widgets.

9.2 Counting Widgets            Fig. 9.1

A widget count w satisfies w  0 for every busy shelf.

Example 1 : Count the widgets on a shelf with three rows.
Solution : Each row holds four widgets, so the shelf holds twelve.
                          Reprint 2099-00
"""
PAGE_2 = """\
SAMPLE BOOK                                                   61

                        1
Example 2 : Halve the widgets.
                        2
Solution : Half of twelve is six.

                         EXERCISE 9.1

1. Count the widgets in a box of five.

9.3 Summary

In this chapter, widgets were counted.
                          Reprint 2099-00
"""


def _chunks():
    return chunk_pages([PAGE_1, PAGE_2], stem="zz109", chapter="widgets", chapter_number=9)


def test_chunks_follow_sections_with_stable_ids_and_pages():
    chunks = _chunks()
    assert [c.section for c in chunks] == ["9.1", "9.2", "9.2", "9.2", "9.2", "9.3"]
    assert [c.kind for c in chunks] == ["theory", "theory", "example", "example", "exercise", "theory"]
    assert [c.passage_id for c in chunks[:3]] == ["ncert:zz109:s9.1:c01", "ncert:zz109:s9.2:c01",
                                                  "ncert:zz109:s9.2:c02"]
    assert [c.passage_id for c in _chunks()] == [c.passage_id for c in chunks]  # deterministic
    assert chunks[1].section_title == "Counting Widgets"  # the figure label beside the heading is dropped
    assert (chunks[0].pdf_page, chunks[0].printed_page) == (1, 60)
    assert (chunks[-1].pdf_page, chunks[-1].printed_page) == (2, 61)
    # running heads and reprint footers never reach chunk text; the Symbol-font glyph is repaired
    assert all("Reprint" not in c.text and "SAMPLE BOOK" not in c.text for c in chunks)
    assert "w ≠ 0" in chunks[1].text
    # an example keeps its solution, and a fraction numerator above "Example 2" moves with it
    assert "twelve" in chunks[2].text and chunks[3].text.startswith("1\nExample 2")


def test_long_sections_are_capped_at_sentence_breaks():
    para = " ".join(["widget"] * 99) + " end."
    body = "\n\n".join([para] * 8)
    chunks = chunk_pages([f"1 HEAD\n9.1 Long\n\n{body}\n"], stem="zz109", chapter="widgets", chapter_number=9)
    assert len(chunks) > 1
    assert all(len(c.text.split()) <= MAX_WORDS + 100 for c in chunks)
    assert all(c.text.endswith("end.") for c in chunks)


def test_headings_out_of_order_are_not_sections():
    page = "1 HEAD\n9.1 Start\nSee 9.3 Later for more.\n9.3 Not Next\ntext\n9.2 Real\nmore text\n"
    chunks = chunk_pages([page], stem="zz109", chapter="widgets", chapter_number=9)
    assert [c.section for c in chunks] == ["9.1", "9.2"]


def test_printed_page_from_running_head():
    assert printed_page_of("\n  42        MATHEMATICS\nbody") == 42
    assert printed_page_of("QUADRATIC EQUATIONS     43\nbody") == 43
    assert printed_page_of("no number here\n") is None


@pytest.mark.parametrize("name", ["jemh1an", "jemh1an.pdf", "data/ncert/JEMH1AN.pdf"])
def test_answers_appendix_is_refused(name):
    with pytest.raises(RefusedSource, match="D-4"):
        resolve(name)


@pytest.mark.parametrize("name", ["jemh101.pdf", "jemh106", "jesc104.pdf", "notes.pdf"])
def test_other_chapters_are_refused(name):
    with pytest.raises(RefusedSource, match="REFUSED"):
        resolve(name)


def test_allowed_chapters_resolve():
    assert [resolve(f"x/jemh10{n}.pdf").chapter_number for n in (4, 5, 8)] == [4, 5, 8]


def test_ingest_refuses_before_writing(tmp_path):
    pdf = tmp_path / "jemh1an.pdf"
    pdf.write_bytes(b"%PDF-1.4 synthetic")
    with pytest.raises(RefusedSource):
        ingest.ingest([pdf], tmp_path / "index", dense=False)
    assert not (tmp_path / "index").exists()
    assert ingest.main([str(pdf), "--out", str(tmp_path / "index2"), "--no-dense"]) == 2
    assert not (tmp_path / "index2").exists()


def test_rrf_fusion_order():
    fused = rrf([["a", "b", "c"], ["b", "c", "a"]], k=60)
    assert [doc for doc, _ in fused] == ["b", "a", "c"]
    assert fused[0][1] == pytest.approx(1 / 61 + 1 / 62)
    # a document found by one list only ranks below one found high by both
    assert [d for d, _ in rrf([["x", "y"], ["y"]], k=60)] == ["y", "x"]
    # equal scores keep first-seen order, so fusion is deterministic
    assert [d for d, _ in rrf([["p"], ["q"]])] == ["p", "q"]


def test_maths_tokenizer():
    assert tokenize("x² − 5x = 0, θ") == ["x^2", "5", "x", "0", "theta"]
    assert "a_n" in tokenize("the term a_n") and "neq" in tokenize("a ≠ 0")
    assert repair_symbols("a  0  b") == "a ≠ 0 ± b"


CARDS = [
    {"passage_id": "normalized:zz01", "concept_id": "zz01", "title": "Widget hum", "text": "Widgets hum loudly.",
     "chapter": "widgets", "class": 10, "source_anchor": {"source_printed_page": 60, "source_section": "9.1"}},
    {"passage_id": "normalized:zz02", "concept_id": "zz02", "title": "Gadget spin", "text": "Gadgets spin fast.",
     "chapter": "gadgets", "class": 10, "source_anchor": {"source_printed_page": 70, "source_section": "7.1"}},
]


def test_hybrid_results_carry_kind_citation_and_page():
    chunks = [{**c.to_dict(), "source_url": "https://example.invalid/zz109.pdf"} for c in _chunks()]
    retriever = HybridRetriever(CARDS, chunks)
    results = retriever.search("how many widgets on a shelf", k=5)
    kinds = {r["kind"] for r in results}
    assert kinds == {"card", "section"}
    section = next(r for r in results if r["kind"] == "section")
    assert section["passage_id"].startswith("ncert:zz109:s9.") and section["source"]["page"] in (60, 61)
    assert section["use_for_formulas"] is False
    assert all(r["chapter"] == "gadgets" for r in retriever.search("spin", chapter="gadgets"))
    assert all(r["kind"] == "card" for r in retriever.search("widgets", kinds=("card",)))


def _write_cards(tmp_path):
    path = tmp_path / "cards.jsonl"
    path.write_text("".join(json.dumps(c) + "\n" for c in CARDS), encoding="utf-8")
    return path


def test_fallback_to_cards_when_index_missing(tmp_path):
    cfg = {"mode": "hybrid", "cards": str(_write_cards(tmp_path)), "index_dir": str(tmp_path / "no_index"),
           "dense": False}
    retriever, notices = build_retriever(cfg, tmp_path)
    assert retriever.chunks == [] and any("not found" in n for n in notices)
    assert [r["kind"] for r in retriever.search("widgets hum")] == ["card"]


def test_textbook_kb_hybrid_without_index_says_so(tmp_path):
    cfg = {"mode": "hybrid", "cards": str(_write_cards(tmp_path)), "index_dir": str(tmp_path / "no_index"),
           "dense": False}
    server = textbook_kb.build(cfg)

    async def go():
        async with Client(server) as client:
            found = (await client.call_tool("search", {"query": "widgets hum", "chapter": "widgets"})).structured_content
            card = (await client.call_tool("get_section", {"passage_id": "normalized:zz02"})).structured_content
            return found, card
    found, card = asyncio.run(go())
    assert "serving cards only" in found["notice"]
    assert found["results"][0]["passage_id"] == "normalized:zz01"
    assert card["concept_id"] == "zz02"


def test_textbook_kb_rejects_unknown_mode():
    with pytest.raises(ValueError, match="unknown"):
        textbook_kb.build({"mode": "vectors_only"})
