"""Builds the LaTeX paper from paper/paper.md, so the two cannot diverge.

paper.md is the source of record and its figures are checked against
run_all.py's output. This turns it into the main.tex that Overleaf compiles.

Usage: python scripts/make_paper.py [output.tex]
"""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "paper" / "paper.md"
DEFAULT_OUT = ROOT.parent / "tgdc-research-paper" / "main.tex"

PREAMBLE = r"""\documentclass[10pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage[british]{babel}
\usepackage[margin=2.0cm]{geometry}
\usepackage{booktabs}
\usepackage{microtype}
\usepackage{titlesec}
\usepackage[hidelinks]{hyperref}
\titlespacing*{\section}{0pt}{1.0em}{0.35em}
\titlespacing*{\subsection}{0pt}{0.8em}{0.25em}
\setlength{\parskip}{0.35em}
\setlength{\parindent}{0pt}
\title{\vspace{-1.6em}\textbf{%s}\vspace{-0.4em}}
\author{\textbf{Cajetan Songwae} \\
  \small{\href{mailto:songwae2000@gmail.com}{songwae2000@gmail.com}} \\
  \small{TGDC case study, research track}}
\date{}
\begin{document}
\maketitle
\vspace{-2.2em}
"""


def escape(text):
    # a leading minus on a percentage becomes a real minus sign, and this has
    # to happen before the percent sign is escaped or the pattern stops matching
    text = re.sub(r"(?<![\d\w])-(\d+%)", r"MINUS\1", text)
    text = text.replace("%", r"\%").replace("&", r"\&")
    text = re.sub(r"MINUS([\d.]+\\%)", r"$-\1$", text)

    text = re.sub(r"`([^`]+)`",
                  lambda m: r"\texttt{" + m.group(1).replace("_", r"\_") + "}", text)
    return re.sub(r"\*\*([^*]+)\*\*", r"\\textbf{\1}", text)


def table(rows):
    header = [c.strip() for c in rows[0].strip("|").split("|")]
    body = [[c.strip() for c in r.strip("|").split("|")] for r in rows[2:]]
    align = "l" * 2 + "r" * (len(header) - 2) if len(header) > 3 else \
        "l" + "r" * (len(header) - 1)

    out = [r"\begin{center}\small", r"\begin{tabular}{" + align + "}", r"\toprule",
           " & ".join(escape(h) for h in header) + r" \\", r"\midrule"]
    out += [" & ".join(escape(c) for c in row) + r" \\" for row in body]
    return out + [r"\bottomrule", r"\end{tabular}", r"\end{center}"]


def convert(markdown):
    lines = markdown.splitlines()
    title = lines[0].lstrip("# ").strip()

    out, i = [], 1
    while i < len(lines):
        line = lines[i]
        if line.startswith("### "):
            out.append(r"\subsection*{" + escape(line[4:]) + "}")
        elif line.startswith("## "):
            out.append(r"\section*{" + escape(line[3:]) + "}")
        elif line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i])
                i += 1
            out += table(block)
            continue
        else:
            out.append(escape(line) if line.strip() else "")
        i += 1

    return (PREAMBLE % title) + "\n".join(out) + "\n\n\\end{document}\n"


if __name__ == "__main__":
    destination = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_OUT
    destination.write_text(convert(SOURCE.read_text()))
    print(f"wrote {destination}")
