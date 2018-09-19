CASE=arbitrary-python
OPTIONS=


all: make-examples show-all

make-examples:  scatter arbitrary pyception images dot
scatter:
	$(MAKE) example CASE=simple-scatter
arbitrary:
	$(MAKE) example CASE=arbitrary-python
arbitrary-alt:
	$(MAKE) example CASE=arbitrary-python OPTIONS="-c alt-headers/config.json"
pyception:
	$(MAKE) example CASE=pyception
images:
	$(MAKE) example CASE=images
networkx_and_dot:
	$(MAKE) example CASE=networkx_and_dot

example:
	python -m markdown -x genhtml $(OPTIONS) -f examples/$(CASE).html examples/$(CASE).mkd
show-all:
	firefox ./examples/*.html
show:
	firefox ./examples/$(CASE).html



release:
	- rm -r genhtml_markdown.egg-info __pycache__
	fullrelease
