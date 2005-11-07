all: unzip __mimetex.so install

unzip:
	unzip -od upstrem-src mimetex.zip

__mimetex.so: __mimetex.c upstrem-src/mimetex.c upstrem-src/gifsave.c
	cc -w __mimetex.c upstrem-src/mimetex.c upstrem-src/gifsave.c -DGIF -DAA -Iupstrem-src -I/usr/include/python2.4 -lm -shared -o __mimetex.so

install:
	mkdir ../../grafit/lib/mimetex
	cp __init__.py __mimetex.so ../../grafit/lib/mimetex
	

cleansrc:
	rm -rf upstrem-src

clean: cleansrc
	rm __mimetex.so
