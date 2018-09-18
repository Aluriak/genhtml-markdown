

all: make-examples show-all

make-examples:  scatter arbitrary
scatter:
	python -m markdown -x genhtml -f examples/simple-scatter.html examples/simple-scatter.mkd
arbitrary:
	python -m markdown -x genhtml -f examples/arbitrary-python.html examples/arbitrary-python.mkd
arbitrary-alt:
	python -m markdown -x genhtml -c alt-headers/config.json -f examples//arbitrary-python.html examples/arbitrary-python.mkd

show-all:
	firefox examples/*.html



release:
	- rm -r genhtml_markdown.egg-info __pycache__
	fullrelease
