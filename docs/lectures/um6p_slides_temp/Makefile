TARGET = main
FIG = $(wildcard *.fig */*.fig)
EPS = $(FIG:.fig=.eps)
PDF = $(FIG:.fig=.pdf)

.suffixes: .tex .bib .bbl .dvi .fig .eps .ps .gz .pdf

all: $(TARGET).pdf 

$(TARGET).dvi : *.tex *.bib $(EPS)
$(TARGET).ps : $(TARGET).dvi


$(PDF): $(FIG)
	./fig.sh

%.dvi: %.tex
	latex $<
	latex $<

%.pdf: *.tex $(PDF) $(FIG) 
	pdflatex $(@:.pdf=.tex)
	pdflatex $(@:.pdf=.tex)


%.ps: %.dvi
	dvips -o $@ $<

%.ps.gz: %.ps
	gzip -f $<

clean:
	rm -f *~ *.bak *.log *.toc *.aux *.ilg \#*\# *.dvi 
	rm -f *.ind *.idx *.bbl *.blg *.out *.nav *.snm

distclean: clean
	rm -f $(TARGET).ps $(TARGET).ps.gz $(TARGET).pdf $(TARGET).dvi fig/*pdf
