#!/usr/bin/env bash
# Compile paper/main.tex to PDF
# Requires: pdflatex (TeX Live / MiKTeX) or tectonic
# Usage: ./paper/compile.sh [--tectonic]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

USE_TECTONIC=false
if [[ "${1:-}" == "--tectonic" ]]; then
  USE_TECTONIC=true
fi

# Check available compiler
if $USE_TECTONIC; then
  if ! command -v tectonic &>/dev/null; then
    echo "tectonic not found. Install: cargo install tectonic"
    echo "Falling back to pdflatex..."
    USE_TECTONIC=false
  fi
fi

if ! $USE_TECTONIC && ! command -v pdflatex &>/dev/null; then
  echo "pdflatex not found."
  echo ""
  echo "Options to compile:"
  echo "  1. Install TeX Live: https://tug.org/texlive/"
  echo "  2. Use Overleaf (online): https://www.overleaf.com"
  echo "     - Create new project, upload paper/main.tex, click Compile"
  echo "  3. Install tectonic (single-binary LaTeX): https://tectonic-typesetting.github.io"
  echo "     then run: ./compile.sh --tectonic"
  echo ""
  echo "For Zenodo submission, Overleaf is the fastest option."
  exit 1
fi

for TEX in main.tex e1-path-a-obstruction.tex proofctl-methodology.tex; do
  if [[ ! -f "$TEX" ]]; then
    echo "Skipping $TEX (not found)"
    continue
  fi

  BASE="${TEX%.tex}"
  echo "Compiling $TEX..."

  if $USE_TECTONIC; then
    HTTPS_PROXY="${HTTPS_PROXY:-}" tectonic "$TEX"
    echo "  -> $BASE.pdf (tectonic)"
  else
    # Two passes for cross-references
    pdflatex -interaction=nonstopmode "$TEX" > /dev/null 2>&1
    pdflatex -interaction=nonstopmode "$TEX" > /dev/null 2>&1
    echo "  -> $BASE.pdf (pdflatex, 2 passes)"
  fi

  if [[ -f "$BASE.pdf" ]]; then
    echo "  Size: $(du -h "$BASE.pdf" | cut -f1)"
  else
    echo "  ERROR: $BASE.pdf not produced"
    exit 1
  fi
done

echo ""
echo "Done. PDF files in paper/:"
ls -lh *.pdf 2>/dev/null || echo "  (none produced)"

echo ""
echo "Next steps for Zenodo submission:"
echo "  1. Upload main.pdf to https://zenodo.org/uploads/new"
echo "  2. Fill metadata from paper/ZENODO_METADATA.txt"
echo "  3. Publish -> get DOI"
echo "  4. Add DOI to endorsement emails"
