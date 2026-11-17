set -eu
mkdir -p /output/paper
cp /input/paper/* /output/paper/
cd /output/paper
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex > step1-pdflatex.log 2>&1
bibtex paper > step2-bibtex.log 2>&1
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex > step3-pdflatex.log 2>&1
pdflatex -recorder -no-shell-escape -interaction=nonstopmode -halt-on-error paper.tex > step4-pdflatex.log 2>&1
pdftotext -layout paper.pdf paper.txt
python -I -B /input/check_pdf.py
pdftoppm -f 1 -singlefile -scale-to 1200 -png paper.pdf /output/template-first-page > /output/render.stdout.log 2> /output/render.stderr.log
