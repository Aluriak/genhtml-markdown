CASE=arbitrary-python
OPTIONS=


t: test
test:
	python -m pytest . --doctest-module -vv --ignore=venv --ignore=genhtml/headers --ignore=genhtml/footers

all: make-examples show-all

examples:  all-examples
all-examples:  scatter arbitrary pyception images networkx_and_dot env-management biseau
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
env-management:
	$(MAKE) example CASE=env-management
biseau:
	$(MAKE) example CASE=biseau

example:
	python -m markdown -x genhtml $(OPTIONS) -f examples/$(CASE).html examples/$(CASE).mkd
show-all:
	firefox ./examples/*.html
show:
	firefox ./examples/$(CASE).html



release:
	- rm -r genhtml_markdown.egg-info __pycache__
	fullrelease

clear: clean
clean:
	- rm -r build genhtml_markdown.egg-info


.PHONY: t test examples
