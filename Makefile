

genhtml: html show
altgen: runaltgen show
plot: runplot show

runplot:
	python -m markdown -x plot -f out/out.html examples/simple-scatter.mkd
html:
	python -m markdown -x genhtml -f out/out.html examples/arbitrary-python.mkd
runaltgen:
	python -m markdown -x genhtml -c alt-headers/config.json -f out/out.html examples/arbitrary-python.mkd
show:
	firefox out/out.html



release:
	- rm -r genhtml_markdown.egg-info __pycache__
	fullrelease
