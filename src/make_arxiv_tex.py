"""Generate the arXiv LaTeX source (paper/arxiv/main.tex) from paper/paper_draft.md.

The Markdown draft stays the single source of truth; re-run this script after
any edit to it. Figures are copied from results/figures/ into paper/arxiv/figures/.

    python src/make_arxiv_tex.py

Handles only the Markdown this paper uses: title, author line, ## / ### headings,
paragraphs, "- " lists, pipe tables, **bold**, *italic*, `code`, and the
reference list. Compiles with pdflatex (TeX Live, as used by arXiv).
"""
import pathlib
import re
import shutil

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "paper" / "paper_draft.md"
OUT = ROOT / "paper" / "arxiv"
FIGS = ["risk_coverage_haiku", "risk_coverage_sonnet", "risk_coverage_opus",
        "calibration_haiku", "calibration_sonnet", "calibration_opus"]
REPO_URL = "https://github.com/arshhn/Honest-Finance-Q-A-research-"

UNICODE = {
    "\u2014": "---", "\u2013": "--", "\u00a7": r"\S{}", "\u2264": r"$\leq$", "\u2265": r"$\geq$",
    "\u2248": r"$\approx$", "\u00d7": r"$\times$", "\u03ba": r"$\kappa$", "\u2076": r"$^{6}$",
    "\u00b3": r"$^{3}$", "\u00b7": r"\textperiodcentered{}", "\u2192": r"$\rightarrow$",
}
ASCII = {"\\": r"\textbackslash{}", "%": r"\%", "&": r"\&", "#": r"\#", "_": r"\_", "$": r"\$",
         "~": r"$\sim$", "^": r"\^{}", "{": r"\{", "}": r"\}", "<": r"$<$", ">": r"$>$"}

FIG_AFTER = {
    "### 4.3": ("fig:rc", "risk_coverage",
                "Risk--coverage on FinanceBench with gold evidence (left to right: Haiku 4.5, Sonnet 5, Opus 5). "
                "The line sweeps the M1 verbalized-confidence threshold; the square and triangle are the single "
                "operating points of M2 (paraphrase self-agreement, valid pairs only) and M3 (evidence-presence "
                "check, numeric-gold questions only). Dashed and dotted lines mark the 10\\% and 5\\% risk targets. "
                "Full-sample curves; held-out operating points are in \\S4.4."),
    "### 4.4": ("fig:cal", "calibration",
                "Reliability of M1 verbalized confidence on answered gold-evidence questions (left to right: "
                "Haiku 4.5, $n=138$; Sonnet 5, $n=143$; Opus 5, $n=149$). Points are decile bins of stated "
                "confidence, annotated with bin counts; the dashed line is perfect calibration. Bins are small, "
                "so we claim aggregate calibration only (\\S4.3)."),
}


def esc(text):
    out = []
    for ch in text:
        out.append(ASCII.get(ch, UNICODE.get(ch, ch)))
    return "".join(out)


def inline(text):
    """Escape a Markdown text span and convert its inline markup."""
    text = text.replace("github.com/arshhn/Honest-Finance-Q-A-research-", "\x00URL\x00")
    parts = re.split(r"(`[^`]+`)", text)
    res = []
    for p in parts:
        if p.startswith("`") and p.endswith("`") and len(p) > 1:
            code = p[1:-1]
            if code.isascii() and not re.search(r"[{}%#\\]", code):
                res.append(r"\path{" + code + "}")
            else:
                code = code.replace("–", "\x01")  # en dash: '--' does not ligature in typewriter fonts
                res.append(r"\texttt{" + esc(code).replace(r"$<$", r"\textless{}").replace(r"$>$", r"\textgreater{}")
                           .replace("\x01", r"\textendash{}") + "}")
            continue
        p = esc(p)
        p = re.sub(r'(^|[\s(\[])"', r"\1``", p)
        p = p.replace('"', "''")
        p = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", p)
        p = re.sub(r"(?<![\\\w])\*(?!\s)(.+?)(?<!\s)\*", r"\\emph{\1}", p)
        res.append(p)
    out = "".join(res).replace("\x00URL\x00", r"\url{" + REPO_URL + "}")
    return out.replace("$$", "")  # merge adjacent inline-math snippets, e.g. $^{6}$$\times$


def table(rows):
    cells = [[c.strip() for c in r.strip().strip("|").split("|")] for r in rows]
    header, body = cells[0], [r for r in cells[1:] if not re.fullmatch(r"[-: ]+", "".join(r))]
    spec = "l" + "c" * (len(header) - 1)
    lines = [r"\begin{center}\small", r"\begin{adjustbox}{max width=\linewidth}",
             r"\begin{tabular}{" + spec + "}", r"\toprule",
             " & ".join(inline(c) for c in header) + r" \\", r"\midrule"]
    lines += [" & ".join(inline(c) for c in r) + r" \\" for r in body]
    lines += [r"\bottomrule", r"\end{tabular}", r"\end{adjustbox}", r"\end{center}"]
    return lines


def figure(label, stem, caption):
    subs = "\n".join(
        r"\includegraphics[width=0.32\linewidth]{" + f"{stem}_{m}.png" + "}"
        for m in ("haiku", "sonnet", "opus"))
    return [r"\begin{figure}[tb]", r"\centering", subs, r"\caption{" + caption + "}",
            r"\label{" + label + "}", r"\end{figure}", ""]


def main():
    md = SRC.read_text(encoding="utf-8").replace("\r\n", "\n").split("\n")
    title = md[0].lstrip("# ").strip()
    author = next(l for l in md if l.startswith("**Author:**"))
    m = re.match(r"\*\*Author:\*\*\s*(.+?)\s*\((.+?)\)\s*\u00b7\s*(\S+@\S+)", author)
    name, affil, email = m.groups()

    tex = [r"\documentclass[11pt]{article}",
           r"\usepackage[utf8]{inputenc}", r"\usepackage[T1]{fontenc}", r"\usepackage{lmodern}",
           r"\usepackage[margin=1in]{geometry}", r"\usepackage{amsmath,amssymb}",
           r"\usepackage{booktabs}", r"\usepackage{adjustbox}", r"\usepackage{graphicx}",
           r"\usepackage{microtype}", r"\usepackage{url}", r"\usepackage[hidelinks]{hyperref}",
           r"\usepackage[font=small]{caption}",
           r"\graphicspath{{figures/}{./}}  % figures may sit in figures/ or beside main.tex (e.g. on Overleaf)",
           "", r"\title{" + inline(title) + "}",
           r"\author{" + inline(name) + r" \\ " + inline(affil.capitalize()) + r" \\ \texttt{" + esc(email) + "}}",
           r"\date{November 2026}", "", r"\begin{document}", r"\maketitle", ""]

    i, n = 0, len(md)
    in_abstract = in_refs = False
    bib = []
    while i < n:
        line = md[i]
        s = line.strip()
        if i == 0 or s.startswith("**Author:**") or s.startswith("**Status:"):
            i += 1
            continue
        for key, (label, stem, cap) in FIG_AFTER.items():
            if s.startswith(key):
                if in_abstract:
                    tex.append(r"\end{abstract}")
                    in_abstract = False
                tex += figure(label, stem, cap)
        if s.startswith("## "):
            if in_abstract:
                tex.append(r"\end{abstract}")
                in_abstract = False
            head = s[3:].strip()
            if head == "Abstract":
                tex.append(r"\begin{abstract}")
                in_abstract = True
            elif head == "References":
                in_refs = True
            else:
                tex += ["", r"\section{" + inline(re.sub(r"^\d+\.\s*", "", head)) + "}"]
            i += 1
            continue
        if s.startswith("### "):
            tex += ["", r"\subsection{" + inline(re.sub(r"^\d+\.\d+\s*", "", s[4:].strip())) + "}"]
            i += 1
            continue
        if in_refs:
            if s.startswith("- "):
                bib.append(s[2:])
            i += 1
            continue
        if s.startswith("|"):
            rows = []
            while i < n and md[i].strip().startswith("|"):
                rows.append(md[i])
                i += 1
            tex += table(rows) + [""]
            continue
        if s.startswith("- "):
            tex.append(r"\begin{itemize}")
            while i < n and md[i].strip().startswith("- "):
                tex.append(r"\item " + inline(md[i].strip()[2:]))
                i += 1
            tex += [r"\end{itemize}", ""]
            continue
        tex.append(inline(s) if s else "")
        i += 1
    if in_abstract:
        tex.append(r"\end{abstract}")

    # Unnumbered, hanging-indent reference list: the text cites author-year, so numeric labels would be unused.
    tex += ["", r"\section*{References}\begin{list}{}{\setlength{\leftmargin}{1.5em}"
                r"\setlength{\itemindent}{-1.5em}\setlength{\itemsep}{2pt}}", r"\small"]
    tex += [r"\item " + inline(b) for b in bib]
    tex += [r"\end{list}", "", r"\end{document}", ""]

    (OUT / "figures").mkdir(parents=True, exist_ok=True)
    for f in FIGS:
        shutil.copyfile(ROOT / "results" / "figures" / f"{f}.png", OUT / "figures" / f"{f}.png")
    (OUT / "main.tex").write_text("\n".join(tex), encoding="utf-8")
    print(f"wrote {OUT / 'main.tex'} ({len(tex)} lines, {len(bib)} references, {len(FIGS)} figures)")


if __name__ == "__main__":
    main()
