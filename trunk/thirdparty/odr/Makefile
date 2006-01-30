all: odr install clean

odr:
	@tar zxvf odr-0.6.1.tar.gz
	@cd odr-0.6.1 && patch -p1 <../odr-g.patch
	@cd odr-0.6.1 && python setup.py build
install:
	cp odr-0.6.1/odrpack.py __init__.py
	cp odr-0.6.1/build/lib.linux-i686-2.4/__odrpack.so __odrpack.so
clean:
	@rm -rf odr-0.6.1 *.pyc

cleanall: clean
	@rm -f __odrpack.so __init__.py
