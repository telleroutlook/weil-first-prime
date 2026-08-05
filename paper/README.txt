To compile the paper:

  pdflatex main.tex
  pdflatex main.tex   # second pass for cross-references

Or with latexmk:

  latexmk -pdf main.tex

Required packages (standard TeX Live / MiKTeX distributions):
  amsmath, amssymb, amsthm, mathtools, hyperref, cleveref, enumitem, geometry

The paper covers Theorems 1–6 plus two corollaries. It does NOT claim to
prove FP-0.35 or imply RH. Section 6 states FP-0.35 as a conjecture and
documents the remaining O2 obligations.

arXiv submission notes:
- Primary category: math.NT (Number Theory)
- Cross-list: math.FA (Functional Analysis), math.SP (Spectral Theory)
- MSC: 11M26, 47B32, 65G20
