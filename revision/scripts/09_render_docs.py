"""Render Markdown deliverables from templates, filling {{Macro}} placeholders
with the same values the manuscript uses (results/tables/manuscript_macros.json).
Fails if a placeholder has no value, so documents can never show stale numbers.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eddqn import RESULTS, REVISION_ROOT  # noqa: E402

MAC = json.loads((RESULTS / "tables" / "manuscript_macros.json").read_text())
_qc = RESULTS / "qc" / "consistency_report.json"
if _qc.exists():
    q = json.loads(_qc.read_text())
    MAC.update({"QCChecks": str(q["checks"]), "QCFailures": str(len(q["failures"])),
                "QCMacrosUsed": str(q["macros_used_in_text"]),
                "QCStaleMain": str(q["stale_number_occurrences"].get("main.pdf", "n/a")),
                "QCStaleSupp": str(q["stale_number_occurrences"].get("supplement.pdf", "n/a"))})

_cr = RESULTS / "qc" / "clean_rerun.md"
MAC["CleanRerun"] = _cr.read_text() if _cr.exists() else "Not yet run."


def plain(v: str) -> str:
    v = re.sub(r"\\(?:texttt|emph)\{([^}]*)\}", r"\1", v)
    return v.replace("\\_", "_").replace("\\,\\%", " %").replace("\\%", "%").replace("\\,", " ").replace("$", "")


def render(src: Path, dst: Path):
    text = src.read_text()
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", text)) - set(MAC))
    if missing:
        raise SystemExit(f"{src}: no value for {missing}")
    out = re.sub(r"\{\{(\w+)\}\}", lambda m: plain(MAC[m.group(1)]), text)
    header = f"<!-- generated from {src.relative_to(REVISION_ROOT)} by scripts/09_render_docs.py; do not edit -->\n"
    dst.write_text(header + out)
    print("wrote", dst.relative_to(REVISION_ROOT))


if __name__ == "__main__":
    pairs = [("reviewer_response/response_template.md", "reviewer_response/response_to_reviewers.md"),
             ("reports/templates/05_results_template.md", "reports/05_results.md"),
             ("reports/templates/07_quality_control_template.md", "reports/07_quality_control.md")]
    for a, b in pairs:
        if (REVISION_ROOT / a).exists():
            render(REVISION_ROOT / a, REVISION_ROOT / b)
