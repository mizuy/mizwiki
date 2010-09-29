APACHE = /opt/local/apache2/bin/apachectl
## $(APACHE) = /etc/init.d/apache2

WWWUSER = _www
# WWWUSER = www-data

restart:
	$(APACHE) restart

tests:
	environ/bin/nosetests

clearcache:
	rm -rf cache
	mkdir cache
	chmod 770 cache
	chown $(WWWUSER) cache
	rm -rf tmp
	mkdir tmp
	chmod 770 tmp
	chown $(WWWUSER) tmp

clean:
	rm -f *~
	rm -f *.pyc
	rm -f mizwiki/*~
	rm -f mizwiki/*.pyc

prepare:
	cp mizwiki/config.py mizwiki/config.py.example

mimetex:
	if ! [ -f mimetex.zip ]; then wget http://www.forkosh.com/mimetex.zip; fi;
	rm -rf src
	unzip mimetex.zip -d src
	cc -Isrc -DAA src/mimetex.c src/gifsave.c -lm -o mimetex.cgi
	rm -rf src

pdf:
	export LANG=C; a2ps -R --line-numbers=1 --columns=2 --medium=A4 --highlight-level=normal --borders no --file-align=virtual --header= --left-footer= --right-footer= --footer="%s. of %s#" --prologue=fixed mizwiki/*.py -o - | ps2pdf - source.pdf
