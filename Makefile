SHELL:=/bin/bash

build:
	@docker build --tag polars .

env: build
	@docker run --interactive \
	            --rm \
	            --tty \
	            --user "$$(id -u)":"$$(id -g)" \
	            --volume /etc/group:/etc/group:ro \
	            --volume /etc/passwd:/etc/passwd:ro \
	            --volume /etc/shadow:/etc/shadow:ro \
	            --volume $(PWD):/usr/src/ \
	            --workdir /usr/src \
	            polars \
	                /bin/bash
