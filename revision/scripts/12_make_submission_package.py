"""Assemble the submission package for the new-submission paper.

Writes revision/submission_package/ (not tracked by git):
  01_manuscript/                  self-contained LaTeX source + main.pdf
  02_supplementary_material/      self-contained LaTeX source + supplement.pdf
  03_figures/                     Figs. 1-4 as separate PDF and 600-dpi PNG files
  04_cover_letter_draft.md        rendered from submission/cover_letter_template.md
  05_highlights.md                rendered from submission/highlights_template.md
  README.md                       contents and the author inputs still pending
  submission_files.zip            01-05 + README
  code_and_data_archive.zip       curated archive for a DOI deposit (tracked files only)
  code_and_data_archive_MANIFEST.txt, SHA256SUMS.txt

Run after `bash paper/build.sh` (run_all.sh does this). Numbers in the cover
letter and highlights come from the same macros as the paper.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eddqn import RESULTS, REVISION_ROOT  # noqa: E402

REPO = REVISION_ROOT.parent
PAPER = REVISION_ROOT / "paper"
TPL = REVISION_ROOT / "submission"
OUT = REVISION_ROOT / "submission_package"

# ------------------------------------------------------------------ archive selection
ARCHIVE_INCLUDE = [
    "DRL_cybersickness_FAST_v2.py",
    "UFFCSData-master_raw_source/DATABASE_SELECTED_DATA/",
    "UFFCSData-master_raw_source/RAW_DATABASE/",
    "UFFCSData-master_raw_source/dataset.csv",
    "UFFCSData-master_raw_source/LICENSE",
    "UFFCSData-master_raw_source/README.md",
    "revision/src/", "revision/scripts/", "revision/configs/", "revision/data/", "revision/results/",
    "revision/paper/", "revision/manuscript/generated/", "revision/supplementary/generated/",
    "revision/reports/01_data_audit.md", "revision/reports/03_rl_formulation.md",
    "revision/run_all.sh", "revision/requirements.txt", "revision/.gitignore",
]
ARCHIVE_EXCLUDE = [
    "revision/paper/SUBMISSION_CHECKLIST.md",   # internal to-do list
]


def macros() -> dict:
    m = {}
    m.update(json.loads((RESULTS / "tables" / "manuscript_macros.json").read_text()))
    m.update(json.loads((RESULTS / "tables" / "posthoc" / "posthoc_macros.json").read_text()))
    m.update(json.loads((RESULTS / "tables" / "search_draw" / "sd_macros.json").read_text()))
    title = re.search(r"\\title\{(.*?)\}\n", (PAPER / "main.tex").read_text(), re.S).group(1)
    m["Title"] = re.sub(r"\s+", " ", title)
    return {k: str(v).replace("$-$", "-") for k, v in m.items()}


def render(src: Path, dst: Path, mac: dict):
    text = src.read_text()
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", text)) - set(mac))
    if missing:
        raise SystemExit(f"{src.name}: no value for {missing}")
    dst.write_text(re.sub(r"\{\{(\w+)\}\}", lambda x: mac[x.group(1)], text))


def copy_tree(src: Path, dst: Path, skip=(".aux", ".log", ".fls", ".fdb_latexmk", ".out", ".blg", ".toc")):
    for p in src.rglob("*"):
        rel = p.relative_to(src)
        if p.is_dir() or p.suffix in skip or rel.parts[0] == "supplement" or p.name in ("build.sh", "SUBMISSION_CHECKLIST.md", ".gitignore"):
            continue
        q = dst / rel
        q.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, q)


def figure1(dst: Path):
    """Fig. 1 (TikZ pipeline) as rendered by paper/build.sh from paper/figs_src/."""
    shutil.copy(PAPER / "figs" / "fig1_pipeline.pdf", dst / "Fig1_pipeline.pdf")


def figures(dst: Path):
    dst.mkdir(parents=True, exist_ok=True)
    figure1(dst)
    for name, src in (("Fig2_roc", PAPER / "figs" / "posthoc_roc.pdf"),
                      ("Fig3_cost_curves", PAPER / "figs" / "posthoc_cost_curves.pdf"),
                      ("Fig4_shap_margin", PAPER / "figs" / "shap_margin.pdf")):
        shutil.copy(src, dst / f"{name}.pdf")
    for pdf in sorted(dst.glob("*.pdf")):
        subprocess.run(["pdftoppm", "-png", "-r", "600", "-singlefile", str(pdf), str(pdf.with_suffix(""))], check=True)


def git_files() -> list[str]:
    out = subprocess.run(["git", "-C", str(REPO), "ls-files"], capture_output=True, text=True, check=True).stdout
    return [f for f in out.splitlines() if any(f == p or (p.endswith("/") and f.startswith(p)) for p in ARCHIVE_INCLUDE)
            and f not in ARCHIVE_EXCLUDE]


def archive(mac: dict):
    files = git_files()
    zpath = OUT / "code_and_data_archive.zip"
    readme_tmp = OUT / "_README_ARCHIVE.md"
    render(TPL / "README_ARCHIVE_template.md", readme_tmp, mac)
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        z.write(readme_tmp, "README.md")
        for f in files:
            z.write(REPO / f, f)
    readme_tmp.unlink()
    (OUT / "code_and_data_archive_MANIFEST.txt").write_text("README.md\n" + "\n".join(files) + "\n")
    return len(files) + 1


def pending_inputs() -> list[str]:
    q = RESULTS / "qc" / "consistency_report.json"
    return json.loads(q.read_text()).get("pending_author_inputs", []) if q.exists() else []


if __name__ == "__main__":
    if not (PAPER / "main.pdf").exists() or not (PAPER / "supplement" / "supplement.pdf").exists():
        raise SystemExit("build the paper first: bash paper/build.sh")
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    mac = macros()
    copy_tree(PAPER, OUT / "01_manuscript")
    copy_tree(PAPER / "supplement", OUT / "02_supplementary_material")
    figures(OUT / "03_figures")
    render(TPL / "cover_letter_template.md", OUT / "04_cover_letter_draft.md", mac)
    render(TPL / "highlights_template.md", OUT / "05_highlights.md", mac)
    for line in (OUT / "05_highlights.md").read_text().splitlines():
        if line.startswith("- ") and len(line[2:]) > 85:
            raise SystemExit(f"highlight longer than 85 characters ({len(line[2:])}): {line[2:]}")
    n_arch = archive(mac)
    pend = pending_inputs()
    readme = [f"# Submission package: {mac['Title']}", "",
              "| Item | Content |", "|---|---|",
              "| `01_manuscript/` | Final manuscript in two layouts from the same sources: `main_access.pdf` (IEEE Access template; `main_access.tex`, class files in `access_template/`) and `main.pdf` (neutral IEEEtran working format); LaTeX sources `sections/`, `refs.bib`, `generated/`, `figs/`, `figs_src/` |",
              "| `02_supplementary_material/` | Supplementary material: `supplement.pdf` and its LaTeX source |",
              "| `03_figures/` | Figures 1–4 as separate PDF (vector) and 600-dpi PNG files, for journals that require separate figure uploads |",
              "| `04_cover_letter_draft.md` | Draft cover letter; complete the [bracketed] parts |",
              "| `05_highlights.md` | Five highlights of at most 85 characters each (Elsevier style) |",
              f"| `code_and_data_archive.zip` | Curated code-and-data archive for a DOI deposit (e.g. Zenodo): {n_arch} files, listed in `code_and_data_archive_MANIFEST.txt` |",
              "", "The paper is still in the neutral IEEE two-column working format; journal-specific formatting is applied after the journal is chosen.", "",
              "## Author inputs still pending in the manuscript", ""]
    readme += [f"- {p}" for p in pend] or ["- none"]
    readme += ["", "## Also before submission", "",
               "- Deposit `code_and_data_archive.zip` (choose a code licence in its README first) and put the DOI into the manuscript and cover letter.",
               "- Confirm the two reference details flagged in `revision/paper/SUBMISSION_CHECKLIST.md`.",
               "- Confirm that no earlier version is under consideration at another journal.", ""]
    (OUT / "README.md").write_text("\n".join(readme))
    with zipfile.ZipFile(OUT / "submission_files.zip", "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(OUT.rglob("*")):
            if p.is_file() and p.suffix != ".zip" and "MANIFEST" not in p.name:
                z.write(p, p.relative_to(OUT))
    sums = subprocess.run(["sha256sum", "submission_files.zip", "code_and_data_archive.zip"], cwd=OUT,
                          capture_output=True, text=True, check=True).stdout
    (OUT / "SHA256SUMS.txt").write_text(sums)
    for p in ("submission_files.zip", "code_and_data_archive.zip"):
        print(f"{p}: {(OUT / p).stat().st_size / 1e6:.1f} MB")
    print(f"pending author inputs: {len(pend)}")
