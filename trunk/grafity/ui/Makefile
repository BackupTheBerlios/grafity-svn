.SUFFIXES: .ui .py

all: main.py graph_data.py graph_style.py graph_axes.py graph_fit.py functions.py fitoptions.py

.ui.py:
	pyuic $(@:.py=.ui) -o $@
