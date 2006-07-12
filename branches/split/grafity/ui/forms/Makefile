.SUFFIXES: .ui .py

all: main.py graph.py worksheet.py console.py \
	 about.py properties.py qtresources.py mdi.py

.ui.py:
	pyuic4 $(@:.py=.ui) -o $@

qtresources.py: grafity.qrc
	pyrcc4 grafity.qrc -o qtresources.py
