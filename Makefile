

genhtml: html show
plot: runplot show

runplot:
	python -m markdown -x plot -f out/out.html examples/simple-scatter.mkd
html:
	python -m markdown -x genhtml -f out/out.html examples/arbitrary-python.mkd
show:
	firefox out/out.html

