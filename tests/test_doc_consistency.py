"""Doc-consistency checks across the plugin's markdown and metadata (stdlib unittest).

Several facts are written down in more than one place: the /bmad and /sdd phase
maps, the equipment names, the skill list, the relay-config section numbers, the
plugin version and the agents' shared design standard. These tests keep the copies
in agreement, and keep the instruction docs free of mid-run agent messaging, a
channel subagents do not have.

Every checker is a pure function over text: it takes the file contents plus a path
label and returns a list of problems, each "path:line: what is wrong, what was
expected". The top-level tests feed the real files; the mutation tests feed
drifted strings and assert the checker reports them, which proves each check can
fail.

Run: python3 -m unittest discover -s tests -v
"""
from __future__ import annotations

import importlib.util
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]

# -- shared parsing ------------------------------------------------------------

PHASE_ID = {
    "bmad": re.compile(r"^(\d+(?:\.\d+)?[a-z]?)$"),
    "sdd": re.compile(r"^(\d+|[A-Z])$"),
}
# Second header cell that identifies a phase table of each relay.
PHASE_TABLE_HEADER = {"bmad": "Real skill", "sdd": "Tool / procedure"}
# Chain steps allowed in a track string besides phase IDs.
TRACK_EXTRA_STEPS = {
    "bmad": {"gate", "quick-dev", "Captain diff review"},
    "sdd": {"gate"},
}
# Numbered-list sections (CLAUDE.md, personas/ironman.md) that copy each phase map.
LIST_HEADING = {"bmad": "BMAD Methodology", "sdd": "Spec-Driven Change"}

EQUIPMENT = {
    # type dir: (registry word, equip skill, plural used in "Valid <plural>:")
    "lenses": ("Lenses", "equip-lens", "lenses"),
    "toolbelts": ("Toolbelts", "equip-toolbelt", "toolbelts"),
    "goggles": ("Goggles", "equip-goggles", "goggles"),
    "gadgets": ("Gadgets", "equip-gadget", "gadgets"),
    "schemes": ("Schemes", "equip-scheme", "schemes"),
}
EQUIPMENT_REGISTRIES = ["README.md", "CLAUDE.md", "personas/ironman.md", "equipment/README.md"]

SECTION_SOURCE = "references/bmad/relay-config.md"
SECTION_HEADING = re.compile(r"^###\s+§(\d+\.\d+)\s+(.+?)\s*$")
CITATION = re.compile(r"§(\d+\.\d+)")


def norm(text: str) -> str:
    """Collapse whitespace and casefold, for title comparison."""
    return " ".join(text.split()).casefold()


def split_row(line: str) -> list[str]:
    """Split a markdown table row into stripped cells; `|` inside backticks is kept."""
    body = line.strip()
    if body.startswith("|"):
        body = body[1:]
    if body.endswith("|") and not body.endswith("\\|"):
        body = body[:-1]
    cells, cur, in_code, i = [], [], False, 0
    while i < len(body):
        ch = body[i]
        if ch == "\\" and i + 1 < len(body) and body[i + 1] == "|":
            cur.append("|")
            i += 2
            continue
        if ch == "`":
            in_code = not in_code
        if ch == "|" and not in_code:
            cells.append("".join(cur).strip())
            cur = []
        else:
            cur.append(ch)
        i += 1
    cells.append("".join(cur).strip())
    return cells


def is_separator(cells: list[str]) -> bool:
    return bool(cells) and all(re.fullmatch(r":?-{3,}:?", c) for c in cells)


def tables(text: str) -> list[list[tuple[int, list[str]]]]:
    """Every markdown table as a list of (1-based line, cells); separator rows dropped."""
    found: list[list[tuple[int, list[str]]]] = []
    current: list[tuple[int, list[str]]] = []
    for lineno, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith("|"):
            cells = split_row(line)
            if not is_separator(cells):
                current.append((lineno, cells))
        elif current:
            found.append(current)
            current = []
    if current:
        found.append(current)
    return found


def section(text: str, heading_prefix: str) -> tuple[int, list[tuple[int, str]]] | None:
    """(heading line, [(line, text)...]) for the first heading whose title starts with
    heading_prefix; the section ends at the next heading of the same or higher level."""
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m and m.group(2).startswith(heading_prefix):
            level = len(m.group(1))
            body = []
            for j in range(idx + 1, len(lines)):
                h = re.match(r"^(#{1,6})\s", lines[j])
                if h and len(h.group(1)) <= level:
                    break
                body.append((j + 1, lines[j]))
            return idx + 1, body
    return None


def blank_code(text: str) -> str:
    """Replace fenced code blocks and inline code spans with spaces, keeping offsets
    and newlines, so matches inside code are ignored but line numbers stay right."""
    def spaces(m: re.Match) -> str:
        return re.sub(r"[^\n]", " ", m.group(0))
    text = re.sub(r"(?ms)^[ \t]*(```|~~~).*?^[ \t]*\1[^\n]*$", spaces, text)
    return re.sub(r"`[^`\n]*`", spaces, text)


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


# -- phase tables ------------------------------------------------------------------


def phase_table(text: str, label: str, kind: str) -> tuple[dict[str, int], list[str]]:
    """Phase IDs -> line from the one phase table of `kind` in text.

    The table is the one whose header is `Phase | <PHASE_TABLE_HEADER[kind]>...`. The
    boundary row (`—`) and `... track` rows are skipped; any other row must start with
    a phase ID."""
    problems: list[str] = []
    candidates = [t for t in tables(text)
                  if len(t[0][1]) > 1 and t[0][1][0] == "Phase"
                  and t[0][1][1].startswith(PHASE_TABLE_HEADER[kind])]
    if len(candidates) != 1:
        return {}, [f"{label}:1: expected exactly one /{kind} phase table (header "
                    f"'| Phase | {PHASE_TABLE_HEADER[kind]}...'), found {len(candidates)}"]
    ids: dict[str, int] = {}
    for lineno, cells in candidates[0][1:]:
        first = cells[0].replace("*", "").strip()
        if not first or first.startswith("—") or first.lower().endswith(" track"):
            continue
        token = first.split()[0]
        if not PHASE_ID[kind].match(token):
            problems.append(f"{label}:{lineno}: row '{first}' does not start with a /{kind} "
                            f"phase ID (pattern {PHASE_ID[kind].pattern})")
        elif token in ids:
            problems.append(f"{label}:{lineno}: phase {token} is listed twice "
                            f"(first at line {ids[token]})")
        else:
            ids[token] = lineno
    if not ids and not problems:
        problems.append(f"{label}:{candidates[0][0][0]}: /{kind} phase table has no phase rows")
    return ids, problems


def check_phase_tables(docs: dict[str, str], kind: str) -> list[str]:
    """Every doc's /kind phase table has the same phase-ID set as the first doc's."""
    parsed = {}
    problems: list[str] = []
    for label, text in docs.items():
        ids, errs = phase_table(text, label, kind)
        parsed[label] = ids
        problems += errs
    ref_label = next(iter(docs))
    ref = parsed[ref_label]
    for label, ids in parsed.items():
        if label == ref_label or not ids:
            continue
        for pid in sorted(set(ids) - set(ref)):
            problems.append(f"{label}:{ids[pid]}: phase {pid} is not in {ref_label}'s "
                            f"phase table; expected the set {sorted(ref)}")
        for pid in sorted(set(ref) - set(ids)):
            problems.append(f"{label}:1: phase {pid} (from {ref_label}:{ref[pid]}) is missing "
                            f"from the /{kind} phase table")
    return problems


# -- numbered-list copies -------------------------------------------------------------


def list_phase_ids(text: str, label: str, kind: str) -> tuple[dict[str, int], int, list[str]]:
    """Phase IDs named in the bold labels of the numbered list under the LIST_HEADING
    section. /bmad items read `**Phase <id> ...**`; /sdd items read `**<id> ...**`."""
    found = section(text, LIST_HEADING[kind])
    if found is None:
        return {}, 1, [f"{label}:1: no heading starting with '{LIST_HEADING[kind]}'"]
    heading_line, body = found
    ids: dict[str, int] = {}
    for lineno, line in body:
        if not re.match(r"^\d+\.\s", line):
            continue
        for bold in re.findall(r"\*\*(.+?)\*\*", line):
            words = bold.split()
            if kind == "bmad":
                if len(words) >= 2 and words[0] == "Phase":
                    ids.setdefault(words[1], lineno)
            elif words and PHASE_ID[kind].match(words[0]):
                ids.setdefault(words[0], lineno)
    return ids, heading_line, []


def check_list_copy(table_ids: set[str], text: str, label: str, kind: str) -> list[str]:
    """Every phase-table ID appears in the numbered workflow list, and the list names
    no phase the table lacks. Order is not checked (the /sdd list merges E and P)."""
    ids, heading_line, problems = list_phase_ids(text, label, kind)
    if problems:
        return problems
    for pid in sorted(table_ids - set(ids)):
        problems.append(f"{label}:{heading_line}: the '{LIST_HEADING[kind]}' list has no item "
                        f"for phase {pid}; expected every phase of the /{kind} table")
    for pid in sorted(set(ids) - table_ids):
        problems.append(f"{label}:{ids[pid]}: the '{LIST_HEADING[kind]}' list names phase "
                        f"{pid}, which is not in the /{kind} phase table {sorted(table_ids)}")
    return problems


# -- track strings ---------------------------------------------------------------------


def check_tracks(text: str, label: str, kind: str, known_ids: set[str]) -> list[str]:
    """The `→` chains in the Tracks table name only known phase IDs plus the allowed
    extra steps, and the `standard` chain covers every phase."""
    problems: list[str] = []
    track_tables = [t for t in tables(text) if t[0][1] and t[0][1][0] == "Track"
                    and "Phases" in t[0][1]]
    if len(track_tables) != 1:
        return [f"{label}:1: expected exactly one Tracks table (header '| Track | ... "
                f"Phases ...'), found {len(track_tables)}"]
    header = track_tables[0][0][1]
    col = header.index("Phases")
    allowed = known_ids | TRACK_EXTRA_STEPS[kind]
    saw_standard = False
    for lineno, cells in track_tables[0][1:]:
        if col >= len(cells) or "→" not in cells[col]:
            continue
        track = cells[0].strip("` ")
        steps = []
        for raw in cells[col].split("→"):
            step = re.sub(r"\s*\([^)]*\)", "", raw.replace("`", "")).strip()
            steps.append(step)
            if step not in allowed:
                problems.append(f"{label}:{lineno}: track '{track}' step '{step}' is not a "
                                f"/{kind} phase ID or one of {sorted(TRACK_EXTRA_STEPS[kind])}")
        if track == "standard":
            saw_standard = True
            for pid in sorted(known_ids - set(steps)):
                problems.append(f"{label}:{lineno}: track 'standard' skips phase {pid}; "
                                f"expected it to run every phase of the table")
    if not saw_standard:
        problems.append(f"{label}:{track_tables[0][0][0]}: Tracks table has no 'standard' chain")
    return problems


# -- § citations ------------------------------------------------------------------------


def relay_sections(text: str, label: str) -> dict[str, tuple[str, int]]:
    """{'3.8': ('KB Lifecycle', line)} from `### §N.N Title` headings."""
    out: dict[str, tuple[str, int]] = {}
    for lineno, line in enumerate(text.splitlines(), 1):
        m = SECTION_HEADING.match(line)
        if m:
            out[m.group(1)] = (m.group(2), lineno)
    return out


def citations(text: str) -> list[tuple[int, str, str | None]]:
    """(line, number, cited title or None) for every § citation outside code.

    A title is either `§N.N (Title)` or, in a table cell that starts with the
    citation, the rest of that cell. `### §N.N` headings are definitions, not
    citations, and are skipped. A non-title parenthetical right after a citation
    (e.g. "§3.8 (see below)") is read as a title and fails loudly on purpose:
    reword the citation instead."""
    clean = blank_code(text)
    lines = clean.splitlines()
    out: list[tuple[int, str, str | None]] = []
    for m in CITATION.finditer(clean):
        lineno = line_of(clean, m.start())
        line = lines[lineno - 1]
        if SECTION_HEADING.match(line):
            continue
        title = None
        paren = re.match(r"[ \t]*\n?[ \t]*\(([^()]+)\)", clean[m.end():])
        if paren:
            title = " ".join(paren.group(1).split())
        elif line.lstrip().startswith("|"):
            col = line[:m.start() - (clean.rfind("\n", 0, m.start()) + 1)]
            cell_start = col.rstrip()
            if cell_start.endswith("|"):
                rest = line[len(col) + len(m.group(0)):].split("|", 1)[0].strip()
                title = rest or None
        out.append((lineno, m.group(1), title))
    return out


def check_citations(text: str, label: str, sections: dict[str, tuple[str, int]]) -> list[str]:
    """Every §N.N exists in the /bmad relay-config, and a cited title is a prefix of
    the heading title (so '§3.6 Design-Implementation Boundary' matches
    '§3.6 Design-Implementation Boundary (Hard Gate)')."""
    problems: list[str] = []
    for lineno, num, title in citations(text):
        if num not in sections:
            problems.append(f"{label}:{lineno}: cites §{num}, but {SECTION_SOURCE} has no "
                            f"'### §{num}' heading (known: {', '.join(sorted(sections))})")
            continue
        heading, hline = sections[num]
        if title is not None and not norm(heading).startswith(norm(title)):
            problems.append(f"{label}:{lineno}: cites §{num} as '{title}', but "
                            f"{SECTION_SOURCE}:{hline} titles it '{heading}'")
    return problems


def check_no_foreign_sections(text: str, label: str) -> list[str]:
    """Only the /bmad relay-config defines `### §` headings; a second definer would make
    plain §N.N citations ambiguous."""
    return [f"{label}:{lineno}: defines '### §{num}'; only {SECTION_SOURCE} may define "
            f"§ sections, or plain citations become ambiguous"
            for num, (_, lineno) in relay_sections(text, label).items()]


# -- equipment registries -----------------------------------------------------------------


def registry_row_names(text: str, label: str, word: str) -> tuple[set[str], int, list[str]]:
    """Names from the last cell of the one table row with a cell equal to `word`
    (bold and backticks stripped)."""
    rows = [(lineno, cells) for t in tables(text) for lineno, cells in t
            if any(c.replace("*", "").strip().casefold() == word.casefold() for c in cells)]
    if len(rows) != 1:
        return set(), 1, [f"{label}:1: expected exactly one registry row for '{word}', "
                          f"found {len(rows)}"]
    lineno, cells = rows[0]
    names = {n.strip().strip("`").strip() for n in cells[-1].split(",")}
    return {n for n in names if n}, lineno, []


def equip_skill_names(text: str, label: str, plural: str) -> list[tuple[str, int, set[str]]]:
    """[(source, line, names)] from the `argument-hint` and the `Valid <plural>:` line."""
    out = []
    for lineno, line in enumerate(text.splitlines(), 1):
        hint = re.match(r'^argument-hint:\s*"?([^"]*)"?\s*$', line)
        if hint:
            out.append(("argument-hint", lineno,
                        {n.strip() for n in hint.group(1).split("|") if n.strip()}))
        valid = re.search(rf"Valid {re.escape(plural)}:\s*(.+)$", line)
        if valid:
            out.append((f"'Valid {plural}:'", lineno, set(re.findall(r"`([^`]+)`",
                                                                  valid.group(1)))))
    return out


def compare_names(label: str, lineno: int, what: str, names: set[str],
                  expected: set[str], expected_from: str) -> list[str]:
    problems = []
    if names - expected:
        problems.append(f"{label}:{lineno}: {what} lists {sorted(names - expected)}, which "
                        f"are not in {expected_from}; expected exactly {sorted(expected)}")
    if expected - names:
        problems.append(f"{label}:{lineno}: {what} is missing {sorted(expected - names)}; "
                        f"expected exactly {sorted(expected)} ({expected_from})")
    return problems


def check_equip_skill(text: str, label: str, plural: str, expected: set[str],
                      expected_from: str) -> list[str]:
    """The equip skill's argument-hint and 'Valid ...' line equal the equipment files."""
    sources = equip_skill_names(text, label, plural)
    found = {s for s, _, _ in sources}
    problems = [f"{label}:1: no {s} found" for s in ("argument-hint", f"'Valid {plural}:'")
                if s not in found]
    for what, lineno, names in sources:
        problems += compare_names(label, lineno, what, names, expected, expected_from)
    return problems


def check_registry(text: str, label: str, word: str, expected: set[str],
                   expected_from: str) -> list[str]:
    """A registry table row for `word` names exactly the equipment files."""
    names, lineno, problems = registry_row_names(text, label, word)
    if problems:
        return problems
    return compare_names(label, lineno, f"the {word} row", names, expected, expected_from)


# -- skills --------------------------------------------------------------------------------


def frontmatter_name(text: str) -> tuple[str | None, int]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, 1
    for lineno, line in enumerate(lines[1:], 2):
        if line.strip() == "---":
            break
        m = re.match(r"^name:\s*(\S+)\s*$", line)
        if m:
            return m.group(1).strip("\"'"), lineno
    return None, 1


def check_skill_name(text: str, label: str, dirname: str) -> list[str]:
    """A skill's frontmatter `name:` equals its directory name."""
    name, lineno = frontmatter_name(text)
    if name != dirname:
        return [f"{label}:{lineno}: frontmatter name is {name!r}; expected {dirname!r} "
                f"(the directory name)"]
    return []


def check_skill_list(text: str, label: str, skills: set[str]) -> list[str]:
    """The 'User-Invoked Skills' list names every skill except equip-*, and nothing else."""
    found = section(text, "User-Invoked Skills")
    if found is None:
        return [f"{label}:1: no 'User-Invoked Skills' heading"]
    heading_line, body = found
    listed: dict[str, int] = {}
    for lineno, line in body:
        for name in re.findall(r"\*\*/([a-z0-9-]+)", line):
            listed.setdefault(name, lineno)
    expected = {s for s in skills if not s.startswith("equip-")}
    problems = [f"{label}:{heading_line}: User-Invoked Skills list is missing /{s}; expected "
                f"every skills/*/ except equip-*" for s in sorted(expected - set(listed))]
    problems += [f"{label}:{listed[s]}: User-Invoked Skills list names /{s}, which has no "
                 f"skills/{s}/SKILL.md" for s in sorted(set(listed) - expected)]
    return problems


# -- ensure-bmad and versions ---------------------------------------------------------------


def check_expected_files(expected: list[str], actual: set[str], label: str) -> list[str]:
    """ensure-bmad's EXPECTED_FILES equals the references/bmad/*.md files."""
    problems = []
    dupes = sorted({f for f in expected if expected.count(f) > 1})
    if dupes:
        problems.append(f"{label}: EXPECTED_FILES lists {dupes} more than once")
    if set(expected) - actual:
        problems.append(f"{label}: EXPECTED_FILES has {sorted(set(expected) - actual)}, which "
                        f"are not in references/bmad/")
    if actual - set(expected):
        problems.append(f"{label}: EXPECTED_FILES is missing {sorted(actual - set(expected))} "
                        f"from references/bmad/")
    return problems


def plugin_json_version(text: str, label: str) -> tuple[str | None, list[str]]:
    try:
        data = json.loads(text)
    except ValueError as exc:
        return None, [f"{label}: invalid JSON ({exc})"]
    version = data.get("version")
    return (version, []) if version else (None, [f"{label}: no top-level \"version\""])


def marketplace_version(text: str, label: str) -> tuple[str | None, list[str]]:
    try:
        data = json.loads(text)
    except ValueError as exc:
        return None, [f"{label}: invalid JSON ({exc})"]
    for plugin in data.get("plugins") or []:
        if plugin.get("name") == "avengers-dev" and plugin.get("version"):
            return plugin["version"], []
    return None, [f"{label}: no plugins[] entry named avengers-dev with a \"version\""]


def settings_template_version(text: str, label: str) -> tuple[str | None, list[str]]:
    m = re.search(r'SETTINGS_TEMPLATE\s*=\s*\{[^}]*?"version"\s*:\s*"([^"]+)"', text)
    if not m:
        return None, [f"{label}: no \"version\" in SETTINGS_TEMPLATE"]
    return m.group(1), []


def check_versions(versions: dict[str, str | None]) -> list[str]:
    """plugin.json, marketplace.json and SETTINGS_TEMPLATE carry one version."""
    distinct = {v for v in versions.values() if v}
    if len(distinct) <= 1:
        return []
    return ["versions disagree: " + ", ".join(f"{k}={v!r}" for k, v in versions.items())]


# -- shared paragraphs ----------------------------------------------------------------------------


def lead_paragraph(text: str, label: str, lead: str) -> tuple[str | None, int, list[str]]:
    """The one paragraph whose first line starts with `lead`, up to the next blank line.

    Returns (paragraph, 1-based line of its first line, problems)."""
    lines = text.split("\n")
    starts = [i for i, line in enumerate(lines) if line.startswith(lead)]
    if len(starts) != 1:
        return None, 1, [f"{label}:1: {len(starts)} paragraphs start with {lead!r}; "
                         f"expected exactly one"]
    end = starts[0]
    while end < len(lines) and lines[end].strip():
        end += 1
    return "\n".join(lines[starts[0]:end]), starts[0] + 1, []


def check_shared_paragraph(texts: dict[str, str], lead: str) -> list[str]:
    """Every file carries exactly one paragraph starting with `lead`, byte-identical."""
    problems: list[str] = []
    reference: tuple[str, str] | None = None
    for label, text in texts.items():
        para, lineno, errs = lead_paragraph(text, label, lead)
        problems += errs
        if para is None:
            continue
        if reference is None:
            reference = (label, para)
        elif para != reference[1]:
            problems.append(f"{label}:{lineno}: the {lead} paragraph differs from "
                            f"{reference[0]}; expected byte-identical copies")
    return problems


# -- agent messaging ------------------------------------------------------------------------------

# Subagents have no tool to message IronMan or each other mid-run; a question comes
# back in a Blocked or Stuck report and IronMan re-dispatches. Any instruction to
# message, ask, ping or contact a named agent describes a channel that does not exist.
AGENT_MESSAGING = re.compile(
    r"\b(message|messages|ask|asks|ping|contact)\s+"
    r"(ironman|tony|blackwidow|black widow|thor|captain|hulk|vision)\b"
    r"|communicate directly", re.IGNORECASE)
MESSAGING_SCOPE_DIRS = ("agents/", "personas/", "equipment/", "skills/", "references/",
                        ".claude/rules/")
MESSAGING_SCOPE_FILES = ("CLAUDE.md", "README.md")


def in_messaging_scope(rel: str) -> bool:
    """Instruction docs only; specs/ and tests/ record the history and the check itself."""
    return rel.startswith(MESSAGING_SCOPE_DIRS) or rel in MESSAGING_SCOPE_FILES


def check_no_agent_messaging(text: str, label: str) -> list[str]:
    """No instruction tells an agent to message another agent mid-run."""
    return [f"{label}:{line_of(text, m.start())}: '{m.group(0)}' describes mid-run agent "
            f"messaging; agents return a Blocked or Stuck report and IronMan re-dispatches"
            for m in AGENT_MESSAGING.finditer(text)]


# -- real-file tests ----------------------------------------------------------------------------


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def tracked_markdown(root: Path = ROOT) -> list[str]:
    """Tracked *.md files. Never a recursive glob: the main checkout holds
    .claude/worktrees/* copies that would be scanned twice.

    Fails loudly unless the result includes SECTION_SOURCE: a tree that is not a git
    checkout of avengers-dev (for example `git archive` output inside an unrelated
    repo) lists nothing, and the § checks would otherwise pass vacuously."""
    proc = subprocess.run(["git", "ls-files", "-z", "--", "*.md"], cwd=root,
                          capture_output=True, text=True, check=False)
    files = sorted(p for p in proc.stdout.split("\0") if p) if proc.returncode == 0 else []
    if SECTION_SOURCE not in files:
        detail = proc.stderr.strip() or f"{len(files)} tracked *.md, none is {SECTION_SOURCE}"
        raise AssertionError(f"{root}: not a git checkout of avengers-dev; § scan needs "
                             f"git ls-files ({detail})")
    return files


BMAD_TABLES = ["skills/bmad/SKILL.md", "references/bmad/relay-config.md", "agents/vision.md",
               "equipment/schemes/bmad-sequence.md"]
SDD_TABLES = ["skills/sdd/SKILL.md", "references/sdd/relay-config.md", "agents/vision.md",
              "equipment/schemes/sdd-sequence.md"]
LIST_COPIES = ["CLAUDE.md", "personas/ironman.md"]
DESIGN_STANDARD_COPIES = ["agents/captain.md", "agents/hulk.md", "agents/thor.md"]
DESIGN_STANDARD_LEAD = "**Design standard.**"


class DocConsistencyCase(unittest.TestCase):
    def assertNoProblems(self, problems: list[str]) -> None:
        if problems:
            self.fail("\n" + "\n".join(problems))


class PhaseTableTests(DocConsistencyCase):
    def test_bmad_phase_tables_agree(self) -> None:
        """/bmad phase maps in the skill, relay-config, Vision and the scheme agree."""
        self.assertNoProblems(check_phase_tables({p: read(p) for p in BMAD_TABLES}, "bmad"))

    def test_sdd_phase_tables_agree(self) -> None:
        """/sdd phase maps in the skill, relay-config, Vision and the scheme agree."""
        self.assertNoProblems(check_phase_tables({p: read(p) for p in SDD_TABLES}, "sdd"))

    def test_numbered_lists_cover_phase_tables(self) -> None:
        """CLAUDE.md and the persona list every phase of both relays."""
        for kind, source in (("bmad", BMAD_TABLES[0]), ("sdd", SDD_TABLES[0])):
            ids, errs = phase_table(read(source), source, kind)
            self.assertNoProblems(errs)
            for rel in LIST_COPIES:
                with self.subTest(kind=kind, file=rel):
                    self.assertNoProblems(check_list_copy(set(ids), read(rel), rel, kind))

    def test_track_strings_use_known_phases(self) -> None:
        """Track chains in both SKILL.md files name only real phases."""
        for kind, source in (("bmad", BMAD_TABLES[0]), ("sdd", SDD_TABLES[0])):
            with self.subTest(kind=kind):
                text = read(source)
                ids, errs = phase_table(text, source, kind)
                self.assertNoProblems(errs + check_tracks(text, source, kind, set(ids)))


class CitationTests(DocConsistencyCase):
    def test_section_citations_resolve(self) -> None:
        """Every §N.N in tracked markdown exists in the /bmad relay-config, with a
        matching title where one is given."""
        sections = relay_sections(read(SECTION_SOURCE), SECTION_SOURCE)
        self.assertTrue(sections, f"{SECTION_SOURCE}: no '### §N.N Title' headings")
        problems: list[str] = []
        for rel in tracked_markdown():
            problems += check_citations(read(rel), rel, sections)
        self.assertNoProblems(problems)

    def test_scan_fails_outside_an_avengers_checkout(self) -> None:
        """An unrelated git repo (or no repo) fails clearly instead of passing vacuously."""
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(os.path.realpath(tmp))
            env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
                   "GIT_CEILING_DIRECTORIES": str(base.parent)}
            (base / "notes.md").write_text("see §3.8\n", encoding="utf-8")
            (base / "references" / "bmad").mkdir(parents=True)
            (base / SECTION_SOURCE).write_text("### §3.8 KB Lifecycle\n", encoding="utf-8")
            for label, setup in (("no repo", []),
                                 ("unrelated repo", [["git", "init", "-q"],
                                                     ["git", "add", "notes.md"]])):
                for cmd in setup:
                    subprocess.run(cmd, cwd=base, env=env, check=True, capture_output=True)
                with self.subTest(case=label), \
                        mock.patch.dict(os.environ, env, clear=True):
                    with self.assertRaises(AssertionError) as ctx:
                        tracked_markdown(base)
                    self.assertIn("not a git checkout of avengers-dev; § scan needs "
                                  "git ls-files", str(ctx.exception))

    def test_only_bmad_relay_config_defines_sections(self) -> None:
        """No other markdown (notably references/sdd/relay-config.md) defines § headings."""
        problems: list[str] = []
        for rel in tracked_markdown():
            if rel != SECTION_SOURCE:
                problems += check_no_foreign_sections(read(rel), rel)
        self.assertNoProblems(problems)


class EquipmentTests(DocConsistencyCase):
    def test_registries_match_equipment_files(self) -> None:
        """Equip skills and every registry table name exactly the equipment/<type>/ files."""
        for kind, (word, skill, plural) in EQUIPMENT.items():
            expected = {p.stem for p in (ROOT / "equipment" / kind).glob("*.md")}
            origin = f"equipment/{kind}/*.md"
            with self.subTest(equipment=kind):
                self.assertTrue(expected, f"{origin}: no files")
                rel = f"skills/{skill}/SKILL.md"
                problems = check_equip_skill(read(rel), rel, plural, expected, origin)
                for reg in EQUIPMENT_REGISTRIES:
                    problems += check_registry(read(reg), reg, word, expected, origin)
                self.assertNoProblems(problems)


class SkillTests(DocConsistencyCase):
    def skills(self) -> dict[str, Path]:
        return {p.parent.name: p for p in sorted((ROOT / "skills").glob("*/SKILL.md"))}

    def test_skill_names_match_directories(self) -> None:
        """Each SKILL.md frontmatter name equals its directory."""
        problems: list[str] = []
        for dirname, path in self.skills().items():
            problems += check_skill_name(path.read_text(encoding="utf-8"),
                                         str(path.relative_to(ROOT)), dirname)
        self.assertNoProblems(problems)

    def test_claude_md_lists_every_user_skill(self) -> None:
        """CLAUDE.md's User-Invoked Skills list covers every non-equip skill."""
        self.assertNoProblems(check_skill_list(read("CLAUDE.md"), "CLAUDE.md",
                                               set(self.skills())))


class MetadataTests(DocConsistencyCase):
    def test_ensure_bmad_expected_files(self) -> None:
        """ensure-bmad.py checks exactly the shipped references/bmad/*.md files."""
        script = ROOT / "skills" / "avengers-init" / "scripts" / "ensure-bmad.py"
        spec = importlib.util.spec_from_file_location("ensure_bmad", script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        actual = {p.name for p in (ROOT / "references" / "bmad").glob("*.md")}
        self.assertNoProblems(check_expected_files(list(module.EXPECTED_FILES), actual,
                                                   str(script.relative_to(ROOT))))

    def test_versions_agree(self) -> None:
        """plugin.json, marketplace.json and avengers-init's SETTINGS_TEMPLATE agree."""
        sources = {
            ".claude-plugin/plugin.json": plugin_json_version,
            ".claude-plugin/marketplace.json": marketplace_version,
            "skills/avengers-init/scripts/avengers-init.py": settings_template_version,
        }
        versions: dict[str, str | None] = {}
        problems: list[str] = []
        for rel, parse in sources.items():
            versions[rel], errs = parse(read(rel), rel)
            problems += errs
        self.assertNoProblems(problems + check_versions(versions))


class SharedRuleTests(DocConsistencyCase):
    def test_design_standard_is_identical(self) -> None:
        """Captain, Hulk and Thor carry one byte-identical design standard paragraph."""
        texts = {rel: read(rel) for rel in DESIGN_STANDARD_COPIES}
        self.assertNoProblems(check_shared_paragraph(texts, DESIGN_STANDARD_LEAD))

    def test_no_mid_run_agent_messaging(self) -> None:
        """No agent, persona, skill, equipment, reference or rule doc tells an agent to
        message another agent mid-run."""
        scanned = [rel for rel in tracked_markdown() if in_messaging_scope(rel)]
        self.assertIn("agents/thor.md", scanned)
        problems: list[str] = []
        for rel in scanned:
            problems += check_no_agent_messaging(read(rel), rel)
        self.assertNoProblems(problems)


# -- mutation tests: every check reports injected drift ------------------------------------------

BMAD_SKILL = """\
| Phase | Real skill(s) invoked | Owner | Tracks |
| ----- | --------------------- | ----- | ------ |
| 0 KB check | `x` | main loop | all |
| 1a Discovery | `x` | main loop | standard |
| 4.5 Spec Hardening | `x` | Captain | standard |
| — | **BOUNDARY** | IronMan | **hard gate** |
| 9 KB Refresh | `x` | main loop | all |
| Quick track | `bmad-quick-dev` | main loop | quick |

| Track | Phases | Use when |
| ----- | ------ | -------- |
| `quick` | 0 → quick-dev → Captain diff review → 9 | small |
| `standard` | 0 → 1a (conditional) → 4.5 → gate → 9 | default |
| `full` | as standard, plus ATDD | tests first |
"""

SDD_SKILL = """\
| Phase | Tool / procedure | Owner | Tracks |
| ----- | ---------------- | ----- | ------ |
| 0 Preflight | `a` | main loop | quick |
| E Explore (optional) | `a` | main loop | standard |
| P Propose | `a` | main loop | quick |
| Full track | `/bmad` | `/bmad` | full |

| Track | Engine | Phases | Use when |
| ----- | ------ | ------ | -------- |
| `quick` | OpenSpec | 0 → P (lite) | small |
| `standard` | OpenSpec | 0 → E (optional) → P → gate | default |
"""

LISTS = """\
### BMAD Methodology (Full Initiative)
1. **Phase 0 KB check** -> status
2. **Phase 1a Discovery** -> doc
3. **Phase 4.5 Spec Hardening** -> captain
4. **HARD GATE** -> gate
5. **Phase 9 KB Refresh** -> refresh

### Spec-Driven Change (/sdd)
1. **0 Preflight** -> preflight
2. **E Explore** (optional) and **P Propose** -> new
3. **HARD GATE** -> gate
"""

RELAY = """\
### §3.6 Design-Implementation Boundary (Hard Gate)
### §3.8 KB Lifecycle
"""


class MutationTests(unittest.TestCase):
    """Each checker returns nothing on a clean fixture and reports injected drift."""

    def test_clean_fixtures_pass(self) -> None:
        bmad_ids, errs = phase_table(BMAD_SKILL, "b.md", "bmad")
        self.assertEqual(errs, [])
        self.assertEqual(set(bmad_ids), {"0", "1a", "4.5", "9"})
        sdd_ids, errs = phase_table(SDD_SKILL, "s.md", "sdd")
        self.assertEqual(errs, [])
        self.assertEqual(set(sdd_ids), {"0", "E", "P"})
        self.assertEqual(check_phase_tables({"a.md": BMAD_SKILL, "b.md": BMAD_SKILL}, "bmad"), [])
        self.assertEqual(check_list_copy(set(bmad_ids), LISTS, "L.md", "bmad"), [])
        self.assertEqual(check_list_copy(set(sdd_ids), LISTS, "L.md", "sdd"), [])
        self.assertEqual(check_tracks(BMAD_SKILL, "b.md", "bmad", set(bmad_ids)), [])
        self.assertEqual(check_tracks(SDD_SKILL, "s.md", "sdd", set(sdd_ids)), [])
        sections = relay_sections(RELAY, "r.md")
        self.assertEqual(check_citations(
            "see §3.8 (KB Lifecycle) and\n| §3.6 Design-Implementation Boundary | x |\n",
            "c.md", sections), [])

    def test_phase_table_drift(self) -> None:
        drifted = BMAD_SKILL.replace("| 4.5 Spec Hardening", "| 4.6 Spec Hardening")
        problems = check_phase_tables({"a.md": BMAD_SKILL, "b.md": drifted}, "bmad")
        self.assertTrue(any(p.startswith("b.md:5: phase 4.6") for p in problems), problems)
        self.assertTrue(any("phase 4.5" in p and "missing" in p for p in problems), problems)

    def test_phase_table_bad_row_and_missing_table(self) -> None:
        drifted = BMAD_SKILL.replace("| 9 KB Refresh", "| Nine KB Refresh")
        _, problems = phase_table(drifted, "b.md", "bmad")
        self.assertTrue(any(p.startswith("b.md:7:") and "Nine" in p for p in problems), problems)
        _, problems = phase_table("no tables here\n", "x.md", "sdd")
        self.assertTrue(problems and "expected exactly one /sdd phase table" in problems[0])

    def test_numbered_list_drift(self) -> None:
        missing = LISTS.replace("3. **Phase 4.5 Spec Hardening** -> captain\n", "")
        problems = check_list_copy({"0", "1a", "4.5", "9"}, missing, "L.md", "bmad")
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith("L.md:1:") and "phase 4.5" in problems[0])
        extra = LISTS.replace("**P Propose**", "**Q Propose**")
        problems = check_list_copy({"0", "E", "P"}, extra, "L.md", "sdd")
        self.assertTrue(any("no item for phase P" in p for p in problems), problems)
        self.assertTrue(any(p.startswith("L.md:10:") and "phase Q" in p for p in problems),
                        problems)

    def test_track_drift(self) -> None:
        drifted = SDD_SKILL.replace("0 → E (optional) → P → gate", "0 → E (optional) → X → gate")
        problems = check_tracks(drifted, "s.md", "sdd", {"0", "E", "P"})
        self.assertTrue(any(p.startswith("s.md:11:") and "step 'X'" in p for p in problems),
                        problems)
        self.assertTrue(any("skips phase P" in p for p in problems), problems)

    def test_citation_drift(self) -> None:
        sections = relay_sections(RELAY, "r.md")
        problems = check_citations("one\nsee §3.9 here\n", "c.md", sections)
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith("c.md:2: cites §3.9"), problems)
        problems = check_citations("see §3.8 (Knowledge Base)\n", "c.md", sections)
        self.assertTrue(problems and "titles it 'KB Lifecycle'" in problems[0], problems)
        problems = check_citations("| §3.6 Hard Gate | x |\n", "c.md", sections)
        self.assertTrue(problems and "cites §3.6 as 'Hard Gate'" in problems[0], problems)
        wrapped = check_citations("see §3.8 (KB\nLifecycle) for more\n", "c.md", sections)
        self.assertEqual(wrapped, [])

    def test_citation_in_code_is_ignored(self) -> None:
        sections = relay_sections(RELAY, "r.md")
        text = "inline `§9.9` and\n```\n§9.9 in a fence\n```\n"
        self.assertEqual(check_citations(text, "c.md", sections), [])

    def test_foreign_section_heading(self) -> None:
        problems = check_no_foreign_sections("# SDD\n### §3.6 Gate\n", "references/sdd/rc.md")
        self.assertEqual(len(problems), 1)
        self.assertTrue(problems[0].startswith("references/sdd/rc.md:2:"), problems)

    def test_equipment_drift(self) -> None:
        expected = {"security", "adversarial"}
        stale = "| Captain | **Lenses** | Focus | `security`, `adversarial`, `ui-ux` |\n"
        problems = check_registry(stale, "R.md", "Lenses", expected, "equipment/lenses/*.md")
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith("R.md:1:") and "ui-ux" in problems[0])
        persona = "| Captain | Lenses | `/equip-lens` | security |\n"
        problems = check_registry(persona, "P.md", "Lenses", expected, "e")
        self.assertTrue(problems and "missing ['adversarial']" in problems[0], problems)
        skill = ('---\nname: equip-lens\nargument-hint: "security | adversarial"\n---\n'
                 "Valid lenses: `security`.\n")
        problems = check_equip_skill(skill, "S.md", "lenses", expected, "e")
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith("S.md:5:"), problems)

    def test_skill_drift(self) -> None:
        problems = check_skill_name("---\nname: bmad-x\n---\n", "skills/bmad/SKILL.md", "bmad")
        self.assertTrue(problems and problems[0].startswith("skills/bmad/SKILL.md:2:"))
        listing = ("### User-Invoked Skills\n- **/avengers-test** - x\n- **/ghost** - y\n"
                   "## Next\n- **/late** - z\n")
        problems = check_skill_list(listing, "CLAUDE.md",
                                    {"avengers-test", "avengers-uninstall", "equip-lens"})
        self.assertEqual(len(problems), 2, problems)
        self.assertTrue(any("missing /avengers-uninstall" in p for p in problems))
        self.assertTrue(any(p.startswith("CLAUDE.md:3:") and "/ghost" in p for p in problems))

    def test_ensure_bmad_drift(self) -> None:
        problems = check_expected_files(["a.md", "b.md", "b.md"], {"a.md", "c.md"}, "e.py")
        self.assertEqual(len(problems), 3, problems)

    def test_version_drift(self) -> None:
        v, errs = settings_template_version('SETTINGS_TEMPLATE = {\n    "version": "1.3.0",\n}',
                                            "i.py")
        self.assertEqual((v, errs), ("1.3.0", []))
        problems = check_versions({"plugin.json": "1.2.0", "i.py": v})
        self.assertEqual(len(problems), 1)
        self.assertIn("i.py='1.3.0'", problems[0])
        _, errs = marketplace_version('{"plugins": [{"name": "other", "version": "1"}]}', "m")
        self.assertEqual(len(errs), 1)

    def test_shared_paragraph_drift(self) -> None:
        lead = "**Rule.**"
        clean = "# A\n\n**Rule.** Do one thing\nwell.\n\n## Next\n"
        self.assertEqual(check_shared_paragraph({"a.md": clean, "b.md": clean}, lead), [])
        drifted = "# B\n\nintro\n\n**Rule.** Do one thing\nbadly.\n"
        problems = check_shared_paragraph({"a.md": clean, "b.md": drifted}, lead)
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith("b.md:5: the **Rule.** paragraph differs "
                                               "from a.md"), problems)
        rewrapped = clean.replace("thing\nwell.", "thing well.")
        self.assertEqual(len(check_shared_paragraph({"a.md": clean, "c.md": rewrapped},
                                                    lead)), 1)
        problems = check_shared_paragraph({"a.md": clean, "d.md": "# D\n"}, lead)
        self.assertTrue(problems and problems[0].startswith("d.md:1: 0 paragraphs"), problems)
        problems = check_shared_paragraph({"a.md": clean + "\n" + clean}, lead)
        self.assertTrue(problems and "2 paragraphs" in problems[0], problems)

    def test_agent_messaging_drift(self) -> None:
        clean = ("# Thor\n\nLook facts up yourself, then stop and return the Blocked "
                 "Report.\nAsk the user only through IronMan's re-dispatch.\n")
        self.assertEqual(check_no_agent_messaging(clean, "t.md"), [])
        drifted = clean + "\n**Quick questions** -> Message Blackwidow directly\n"
        problems = check_no_agent_messaging(drifted, "t.md")
        self.assertEqual(len(problems), 1, problems)
        self.assertTrue(problems[0].startswith("t.md:6: 'Message Blackwidow'"), problems)
        for line in ("then ask\nIronMan", "ping Black Widow", "contact the user? no: contact "
                     "Hulk", "Trust Thor and BlackWidow to communicate directly"):
            with self.subTest(line=line):
                self.assertEqual(len(check_no_agent_messaging(line, "t.md")), 1)
        self.assertTrue(in_messaging_scope("agents/thor.md"))
        self.assertTrue(in_messaging_scope(".claude/rules/ironman-delegation.md"))
        self.assertTrue(in_messaging_scope("README.md"))
        self.assertFalse(in_messaging_scope("specs/stories/agent-escalation-path.md"))
        self.assertFalse(in_messaging_scope("tests/README.md"))


if __name__ == "__main__":
    unittest.main()
