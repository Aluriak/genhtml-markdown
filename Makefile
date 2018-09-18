

all: run show
test: run run_test


run:
	python -m markdown -x plot -f out/out.html examples/simple-scatter.mkd
show:
	xdg-open out/out.html
run_test:
	echo "RESULTS"
	wc out.html

