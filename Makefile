APACHE = /opt/local/apache2/bin/apachectl
## $(APACHE) = /etc/init.d/apache2

restart:
	$(APACHE) restart

clearcache:
	rm -rf cache
	mkdir cache
	chmod 700 cache
	chown www-data:www-data cache

clean:
	rm -rf tmp
	mkdir tmp
	chmod 700 tmp
	chown www-data:www-data tmp
	rm -f lib/*~
	rm -f lib/*.pyc

mimetex:
	if ! [ -f mimetex.zip ]; then wget http://www.forkosh.com/mimetex.zip; fi;
	rm -rf src
	unzip mimetex.zip -d src
	cc -Isrc -DAA src/mimetex.c src/gifsave.c -lm -o mimetex.cgi
	rm -rf src

pdf:
	export LANG=C; a2ps -R --line-numbers=1 --columns=2 --medium=A4 --highlight-level=normal --borders no --file-align=virtual --header= --left-footer= --right-footer= --footer="%s. of %s#" --prologue=fixed lib/*.py -o - | ps2pdf - source.pdf

setup:
	if ! [ -d /var/www/w/ ]; then mkdir /var/www/w/; fi;
	cp .htaccess /var/www/w/
	cp -r theme /var/www/w/
