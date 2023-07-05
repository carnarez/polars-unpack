SHELL := /bin/bash

FLAGS = --rm \
        --tty \
        --user "$$(id -u)":"$$(id -g)" \
        --volume /etc/group:/etc/group:ro \
        --volume /etc/passwd:/etc/passwd:ro \
        --volume /etc/shadow:/etc/shadow:ro \
        --volume $(PWD):/usr/src \
        --workdir /usr/src

env:
	@docker build --tag polars-unpack .
	@docker run --interactive $(FLAGS) polars-unpack /bin/bash

serve:
	@cp README.md web/index.md
	@docker build --tag polars-unpack/web web
	@rm -fr web/index.md
	@docker run --interactive \
	            --name polars-unpack-web \
	            --publish 8000:80 \
	            --rm \
	            --tty \
	            polars-unpack/web

test:
	@docker build --tag polars-unpack/tests tests
	@docker run --env COLUMNS=$(COLUMNS) \
	            $(FLAGS) \
	            polars-unpack/tests \
	                python -m pytest --capture=no \
	                                 --color=yes \
	                                 --cov=polars_unpack \
	                                 --cov-report term-missing \
	                                 --override-ini="cache_dir=/tmp/pytest" \
	                                 --verbose \
	                                 --verbose

clean:
	-@rm -fr $$(find . -name __pycache__)
