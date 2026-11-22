import textwrap

from hld_agent.adoc import lint_document, lint_section, normalize_body, refs
from hld_agent.template import parse_template


def write(tmp_path, text):
    p = tmp_path / "t.adoc"
    p.write_text(textwrap.dedent(text))
    return p


def test_sample_template_structure(root):
    t = parse_template(root / "templates/sample_hld_template.adoc")
    ids = [s.id for s in t.sections]
    assert ids[0] == "document-control" and "non-functional-design" in ids
    assert t.section("document-control").mode == "manual"          # explicit hint
    assert t.section("approvals").mode == "manual"                 # inferred from title
    integ = t.section("integration-and-interfaces")
    assert integ.diagram == "sequence" and integ.diagram_required and integ.min_citations == 1
    assert integ.checks and "protocol" in integ.checks[0]
    assert t.section("non-functional-design").role == "nfr"
    assert [s.title for s in t.section("introduction").subsections] == ["Purpose", "Scope", "Definitions and Acronyms"]
    assert t.header_lines[0].startswith("= ")


def test_headings_inside_blocks_and_anchors(tmp_path):
    p = write(tmp_path, """\
        = Doc
        :toc:

        [[ctx]]
        == 1. Context
        // Explain the context.
        ////
        Hidden guidance in a comment block.
        ////
        ----
        == not a heading (inside listing)
        ----
        ```
        == also not a heading
        ```

        [appendix]
        == Glossary
        // hld: mode=generate, diagram=none
        Terms.
        """)
    t = parse_template(p)
    assert [s.id for s in t.sections] == ["ctx", "glossary"]
    assert t.sections[0].title == "1. Context"
    assert "Hidden guidance" in t.sections[0].guidance and "Explain the context." in t.sections[0].guidance
    assert t.sections[1].pre_lines == ["[appendix]"] and t.sections[1].mode == "generate"
    assert t.sections[1].diagram is None


def test_normalize_converts_markdown(root):
    t = parse_template(root / "templates/sample_hld_template.adoc")
    sec = t.section("solution-architecture")
    body = normalize_body("== Solution Architecture\n## Component View\nSee [docs](https://x.io/a).\n"
                          "```mermaid\nflowchart LR\n A-->B\n```\n```java\nint x;\n```", sec)
    assert "Solution Architecture" not in body.split("\n")[0]     # repeated heading dropped
    assert "=== Component View" in body
    assert "https://x.io/a[docs]" in body
    assert "[mermaid]\n....\nflowchart LR" in body and "[source,java]\n----\nint x;\n----" in body


def test_lint_section_rules(root):
    t = parse_template(root / "templates/sample_hld_template.adoc")
    sec = t.section("solution-architecture")
    body = ("=== Component View\nUses the seat service <<EV-1>> and <<EV-42>>. TBD.\nApplies DEC-3 for FR-9.\n"
            "----\nunclosed\n")
    rules = {f["rule"] for f in lint_section(sec, body, evidence_ids={"EV-1"}, req_ids={"FR-1"},
                                              dec_ids={"DEC-1"}, min_citations=1)}
    assert {"L002", "L003", "L006", "L007", "L008", "L104", "L105"} <= rules
    assert "L004" not in rules            # one valid citation present


def test_lint_document_attributes_nfr_gap_to_owner(root):
    t = parse_template(root / "templates/sample_hld_template.adoc")
    brief = {"requirements": [{"id": "FR-1", "kind": "functional", "text": "a"},
                              {"id": "NFR-1", "kind": "non_functional", "text": "fast"}]}
    f = lint_document(t, {"x": {"body": "covers FR-1"}}, brief,
                      [{"id": "DEC-1", "title": "t", "status": "accepted"}])
    nfr = [x for x in f if x["rule"] == "L102"]
    assert nfr and nfr[0]["section_id"] == "non-functional-design"
    assert any(x["rule"] == "L103" for x in f)
    assert refs("see <<EV-2>>, <<EV-10>> NFR-1 DEC-2")["evidence"] == ["EV-2", "EV-10"]
