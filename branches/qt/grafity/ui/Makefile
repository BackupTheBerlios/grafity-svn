.SUFFIXES: .ui .py

all: main.py graph_data.py graph_style.py graph_axes.py graph_fit.py

.ui.py:
	pyuic $(@:.py=.ui) -o $@
