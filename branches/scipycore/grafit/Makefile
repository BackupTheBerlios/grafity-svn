all: graph_render.so

graph_render.so: graph_render.pyx
	@echo compiling 'graph_render' pyrex extension...
	@pyrexc graph_render.pyx
	python setup.py build_ext -i -t /tmp
	@chmod -x graph_render.so
	@rm graph_render.c

clean:
	@rm -f graph_render.so
	@rm -f *.pyc
