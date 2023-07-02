SHELL := /bin/bash

FLAGS = --rm \
        --tty \
        --user "$$(id -u)":"$$(id -g)" \
        --volume /etc/group:/etc/group:ro \
        --volume /etc/passwd:/etc/passwd:ro \
        --volume /etc/shadow:/etc/shadow:ro \
        --volume $(PWD):/usr/src \
        --workdir /usr/src

build:
	@docker build --tag polars-json .

env: build
	@docker run --interactive $(FLAGS) polars-json /bin/bash

test: build
	@docker run --env COLUMNS=$(COLUMNS) \
	            $(FLAGS) \
	            polars-json \
	                python -m pytest --capture=no \
	                                 --color=yes \
	                                 --cov=unpack \
	                                 --cov-report term-missing \
	                                 --override-ini="cache_dir=/tmp/pytest" \
	                                 --verbose \
	                                 --verbose

clean:
	-@rm -fr __pycache__ */__pycache__
