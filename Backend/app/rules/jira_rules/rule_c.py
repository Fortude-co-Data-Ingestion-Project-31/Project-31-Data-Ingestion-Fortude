import re


SENSITIVE_PATTERNS = [
    (r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "email"),
    (r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", "phone"),
    (r"(?i)(api[_\- ]?key|secret|password|token)\s*[:=]\s*\S+", "credential"),
    (r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b", "card_number"),
]

NOISE_PATTERNS = [
    r"^\s*--\s*$",
    r"^\s*Sent from my .*$",
    r"^\s*On .* wrote:\s*$",
    r"^\s*\[bot\]",
    r"^\s*This is an automated message.*$",
]


def _comment_text(c):
    return c.get("body_clean") or c.get("body") or ""


# ---------------------------------------------------------------------------
# C-01 Take only real resolutions
# ---------------------------------------------------------------------------
# A resolution must exist and the last substantial comment must be
# longer than a trivial "fixed". This is a gate, not a filter.
# ---------------------------------------------------------------------------

C01_MIN_SOLUTION_LENGTH = 40


def rule_c_01_real_resolutions_only(ticket):
    resolution = ticket.get("resolution")
    comments = ticket.get("comments", [])

    last_comment = _comment_text(comments[-1]) if comments else ""

    has_resolution = bool(resolution)
    has_substance = len(last_comment.strip()) >= C01_MIN_SOLUTION_LENGTH

    ticket["derived"]["c01_is_real_resolution"] = has_resolution and has_substance
    ticket["derived"]["c01_last_comment_length"] = len(last_comment.strip())
    return ticket


# ---------------------------------------------------------------------------
# C-02 Strip the noise
# ---------------------------------------------------------------------------
# Writes a `body_clean` on each comment. The original `body` is preserved.
# ---------------------------------------------------------------------------

def rule_c_02_strip_noise(ticket):
    for c in ticket.get("comments", []):
        body = c.get("body") or ""
        kept = [
            line for line in body.splitlines()
            if not any(re.match(p, line.strip()) for p in NOISE_PATTERNS)
        ]
        c["body_clean"] = "\n".join(kept).strip()
    return ticket


# ---------------------------------------------------------------------------
# C-03 Remove anything sensitive
# ---------------------------------------------------------------------------
# Destructive on purpose: redaction happens before storage.
# Records only the pattern type found, never the value.
# ---------------------------------------------------------------------------

def rule_c_03_redact_sensitive(ticket):
    findings = []

    def redact(text):
        if not text:
            return text
        for pattern, label in SENSITIVE_PATTERNS:
            for _ in re.finditer(pattern, text):
                findings.append(label)
            text = re.sub(pattern, f"[{label.upper()}_REDACTED]", text)
        return text

    ticket["description"] = redact(ticket.get("description") or "")

    for c in ticket.get("comments", []):
        c["body_clean"] = redact(c.get("body_clean") or "")

    ticket["derived"]["c03_sensitive_found"] = len(findings) > 0
    ticket["derived"]["c03_sensitive_types"] = sorted(set(findings))
    ticket["derived"]["c03_sensitive_count"] = len(findings)
    return ticket


# ---------------------------------------------------------------------------
# C-04 Separate problem from solution
# ---------------------------------------------------------------------------
# Problem comes from description and the first two comments.
# Solution comes from the last substantial comment.
# ---------------------------------------------------------------------------

C04_MIN_SUBSTANTIAL = 40


def rule_c_04_separate_problem_and_solution(ticket):
    problem_parts = []

    if ticket.get("description"):
        problem_parts.append(ticket["description"].strip())

    for c in ticket.get("comments", [])[:2]:
        text = _comment_text(c).strip()
        if text:
            problem_parts.append(text)

    solution = ""
    for c in reversed(ticket.get("comments", [])):
        text = _comment_text(c).strip()
        if len(text) >= C04_MIN_SUBSTANTIAL:
            solution = text
            break

    ticket["derived"]["c04_problem"] = "\n\n".join(problem_parts).strip()
    ticket["derived"]["c04_solution"] = solution
    return ticket


# ---------------------------------------------------------------------------
# C-05 Chunk long text sensibly
# ---------------------------------------------------------------------------
# Overlapping windows, never cut mid-sentence. Guards against the
# infinite loop case where overlap >= chunk_size.
# ---------------------------------------------------------------------------

def rule_c_05_chunk_long_text(ticket, chunk_size=800, overlap=100):
    text = (
        (ticket["derived"].get("c04_problem") or "")
        + "\n\n"
        + (ticket["derived"].get("c04_solution") or "")
    ).strip()

    if not text:
        ticket["derived"]["c05_chunks"] = []
        return ticket

    if overlap >= chunk_size:
        overlap = chunk_size // 4

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        if end < len(text):
            boundary = text.rfind(". ", start, end)
            if boundary != -1 and boundary > start + chunk_size // 2:
                end = boundary + 1

        chunks.append(text[start:end].strip())

        if end >= len(text):
            break

        start = max(end - overlap, start + 1)

    ticket["derived"]["c05_chunks"] = [c for c in chunks if c]
    return ticket


# ---------------------------------------------------------------------------
# C-06 Tag by function and version
# ---------------------------------------------------------------------------

def rule_c_06_tag_function_and_version(ticket):
    ticket["derived"]["c06_function_area"] = ticket.get("function_area")
    ticket["derived"]["c06_m3_version"] = ticket.get("m3_program_code")
    return ticket


# ---------------------------------------------------------------------------
# C-07 Down rank stale answers
# ---------------------------------------------------------------------------
# Compares the asking ticket's M3 version against the answer's version.
# In ERP support, an old answer is often actively wrong.
# ---------------------------------------------------------------------------

def rule_c_07_down_rank_stale(ticket):
    asking = ticket.get("m3_program_code")
    answer = ticket["derived"].get("c06_m3_version")

    ticket["derived"]["c07_is_stale"] = bool(
        asking and answer and asking != answer
    )
    return ticket


# ---------------------------------------------------------------------------
# C-08 Link near duplicates
# ---------------------------------------------------------------------------
# Placeholder. The Vector DB writer fills this after the rules run.
# ---------------------------------------------------------------------------

def rule_c_08_link_near_duplicates(ticket):
    ticket["derived"].setdefault("c08_duplicate_of", None)
    return ticket


# ---------------------------------------------------------------------------
# C-09 Suggest on arrival
# ---------------------------------------------------------------------------
# Placeholder. The Vector DB writer fills this after the rules run.
# ---------------------------------------------------------------------------

def rule_c_09_suggest_on_arrival(ticket):
    ticket["derived"].setdefault("c09_suggested_resolutions", [])
    return ticket


RULES = [
    rule_c_01_real_resolutions_only,
    rule_c_02_strip_noise,
    rule_c_03_redact_sensitive,
    rule_c_04_separate_problem_and_solution,
    rule_c_05_chunk_long_text,
    rule_c_06_tag_function_and_version,
    rule_c_07_down_rank_stale,
    rule_c_08_link_near_duplicates,
    rule_c_09_suggest_on_arrival,
]