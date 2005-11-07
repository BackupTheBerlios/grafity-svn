all: odr install clean

odr:
	@tar zxvf odr-0.6.tar.gz
	@cd odr-0.6 && patch -p1 <../odr-g.patch
	@cd odr-0.6 && python setup.py build
install:
	mkdir ../../grafit/lib/odr
	cp odr-0.6/odrpack.py ../../grafit/lib/odr/__init__.py
	cp odr-0.6/build/lib.linux-i686-2.4/__odrpack.so ../../grafit/lib/odr/__odrpack.so
clean:
	@rm -rf odr-0.6
