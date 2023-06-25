SHELL := /bin/bash

build:
	@docker build --tag polars-json .

env: build
	@docker run --interactive \
	            --rm \
	            --tty \
	            --user "$$(id -u)":"$$(id -g)" \
	            --volume /etc/group:/etc/group:ro \
	            --volume /etc/passwd:/etc/passwd:ro \
	            --volume /etc/shadow:/etc/shadow:ro \
	            --volume $(PWD):/usr/src \
	            --workdir /usr/src \
	            polars-json \
	                /bin/bash

test: build
	@docker run --env COLUMNS=$(COLUMNS) \
	            --rm \
	            --tty \
	            --user "$$(id -u)":"$$(id -g)" \
	            --volume /etc/group:/etc/group:ro \
	            --volume /etc/passwd:/etc/passwd:ro \
	            --volume /etc/shadow:/etc/shadow:ro \
	            --volume $(PWD):/usr/src \
	            --workdir /usr/src \
	            polars-json \
	                python -m pytest --capture=no \
	                                 --color=yes \
	                                 --cov=flatten_json \
	                                 --cov-report term-missing \
	                                 --override-ini="cache_dir=/tmp/pytest" \
	                                 --verbose

clean:
	-@rm -fr __pycache__ */__pycache__
