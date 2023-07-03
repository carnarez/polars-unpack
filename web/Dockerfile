# render markdown to html

FROM python:slim as render

WORKDIR /usr/src

COPY front-matter.md .
COPY polars-logo.svg .
COPY unpack.py .

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --yes git wget \
 && pip install -U pip \
 && pip install --no-cache-dir git+https://github.com/carnarez/astdocs@master \
                               git+https://github.com/carnarez/markdown-astdocs@master \
                               git+https://github.com/carnarez/markdown-img@master \
                               git+https://github.com/carnarez/markdown-insert@master \
                               git+https://github.com/carnarez/markdown-script@master \
                               jinja2 \
                               lunr \
                               markdown \
                               pymdown-extensions \
                               pyyaml \
 && wget --quiet https://raw.githubusercontent.com/carnarez/markdown-render/master/build/render.py \
 && wget --quiet https://raw.githubusercontent.com/carnarez/markdown-render/master/build/template.html

RUN wget --quiet https://raw.githubusercontent.com/carnarez/polars-unpack/master/unpack.py \
 && ASTDOCS_WITH_LINENOS=1 astdocs unpack.py > index.md \
 && find . -name "*.md" | grep -v front-matter.md | while read f; do \
      mkdir -p /var/www/`dirname $f`; \
      cat front-matter.md $f > /tmp/md; \
      mv /tmp/md $f; \
    done \
 && python render.py --prefix=/var/www `find . -name "*.md" | grep -v front-matter.md`

RUN python unpack.py polars-logo.svg > /var/www/polars-unpacked.svg


# minify everything in place

FROM node:alpine as bundle

WORKDIR /var/www

COPY --from=render /var/www .

RUN npm config set update-notifier false \
 && npm install --global --no-audit --no-fund autoprefixer clean-css-cli html-minifier postcss-cli | grep -v ^$ \
 && wget --quiet https://raw.githubusercontent.com/carnarez/markdown-render/master/style/style.css \
 && wget --quiet https://raw.githubusercontent.com/carnarez/markdown-render/master/style/style-highlight.css \
 && wget --quiet https://raw.githubusercontent.com/carnarez/markdown-render/master/style/style-markdown.css \
 && wget --quiet https://raw.githubusercontent.com/carnarez/markdown-render/master/style/style-search.css \
 && cat style.css style-*.css | grep -v '@import ".*"' > bundle.css \
 && mv bundle.css style.css \
 && rm style-*.css \
 && find . -name "*.css" | while read f; do \
      postcss $f --replace --use autoprefixer; \
      cleancss --output $f $f; \
    done \
 && find . -name "*.html" | while read f; do \
      html-minifier --collapse-boolean-attributes \
                    --collapse-whitespace \
                    --output $f \
                    --minify-css true \
                    --minify-js true \
                    --remove-attribute-quotes \
                    --remove-comments \
                    --remove-empty-attributes \
                    --remove-optional-tags \
                    --remove-redundant-attributes \
                    --remove-script-type-attributes \
                    --remove-style-link-type-attributes \
                    --use-short-doctype \
                    $f; \
    done


# create an entrypoint.sh to trap the httpd process

FROM busybox

RUN addgroup -S www \
 && adduser -DHS -G www -s /bin/sh www \
 && touch /etc/httpd.conf \
 && echo "/bin/httpd -c /etc/httpd.conf -f -h /var/www -p 0.0.0.0:80" > /usr/sbin/entrypoint.sh \
 && chmod +x /usr/sbin/entrypoint.sh

WORKDIR /var/www

COPY --from=bundle /var/www .

USER www

ENTRYPOINT ["/bin/sh", "-c", "/usr/sbin/entrypoint.sh"]
