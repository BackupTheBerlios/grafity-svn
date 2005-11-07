all:
	@make -C lib-sources/mimetex
	@make -C lib-sources/odr
	@make cleansrc -C lib-sources/mimetex

clean: 
	@find . -name "*.pyc" -exec rm -rf {} \;
	@find . -name ".grafit-birds" -exec rm -rf {} \;
	@rm -r grafit/lib/odr grafit/lib/mimetex

