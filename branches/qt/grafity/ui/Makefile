.SUFFIXES: .ui .py

all: main.py graph_data.py graph_style.py

.ui.py:
	pyuic $(@:.py=.ui) -o $@
