.SUFFIXES: .txt .html

all: worksheet.html

.txt.html:
	rest2html --stylesheet=effbot.css --embed-stylesheet $(@:.html=.txt) $@
