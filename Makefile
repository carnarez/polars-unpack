SHELL := /bin/bash

FLAGS = --rm \
        --tty \
        --user "$$(id -u)":"$$(id -g)" \
        --volume /etc/group:/etc/group:ro \
        --volume /etc/passwd:/etc/passwd:ro \
        --volume /etc/shadow:/etc/shadow:ro \
        --volume $(PWD)/samples:/usr/src/samples \
        --volume $(PWD)/tests:/usr/src/tests \
        --volume $(PWD)/unpack.py:/usr/src/unpack.py \
        --workdir /usr/src

env:
	@docker build --tag polars-unpack .
	@docker run --interactive $(FLAGS) polars-unpack /bin/bash

test:
	@docker build --tag polars-unpack/tests tests
	@docker run --env COLUMNS=$(COLUMNS) \
	            $(FLAGS) \
	            polars-unpack/tests \
	                python -m pytest --capture=no \
	                                 --color=yes \
	                                 --cov=unpack \
	                                 --cov-report term-missing \
	                                 --override-ini="cache_dir=/tmp/pytest" \
	                                 --verbose \
	                                 --verbose

clean:
	-@rm -fr $$(find . -name __pycache__)
