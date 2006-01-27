.SUFFIXES: .txt .html .tex .pdf

all: worksheet.html
pdf: worksheet.pdf

clean:
	@rm -f *.aux *.log *.tex *.out

cleanall: clean
	@rm -f *.html *.pdf

.txt.html:
	rest2html --stylesheet=style.css --embed-stylesheet $(@:.html=.txt) $@

.txt.tex:
	rest2latex $(@:.tex=.txt) $@

.tex.pdf:
	pdflatex $(@:.pdf=.tex)
