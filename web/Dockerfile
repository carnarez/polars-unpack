# render markdown to html

FROM python:slim as render

WORKDIR /usr/src

RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install --no-install-recommends --yes git \
 && pip install -U pip \
 && pip install --no-cache-dir git+https://github.com/carnarez/astdocs@master \
                               git+https://github.com/carnarez/markdown-extension-astdocs@master \
                               git+https://github.com/carnarez/markdown-extension-img@master \
                               git+https://github.com/carnarez/markdown-extension-insert@master \
                               git+https://github.com/carnarez/markdown-extension-script@master \
                               git+https://github.com/carnarez/markdown-render@master \
                               jinja2 \
                               lunr \
                               markdown \
                               pymdown-extensions \
                               pyyaml

COPY . .

RUN git clone --filter=blob:none --quiet https://github.com/carnarez/polars-unpack.git \
 && mkdir api tests \
 && mv polars-unpack/README.md index.md \
 && mv polars-unpack/polars_unpack/unpack.py api \
 && mv polars-unpack/tests/test_*.py tests \
 && ( \
      cd api; \
      ASTDOCS_WITH_LINENOS=1 astdocs unpack.py > index.md; \
      mv *.py ..; \
    ) \
 && ( \
      cd tests; \
      ASTDOCS_WITH_LINENOS=1 astdocs . > index.md; \
      mv *.py ..; \
    ) \
 && rm -fr polars-unpack \
 && find . -name "*.md" | grep -e front-matter.md -e toc.md -v | while read f; do \
      mkdir -p /var/www/`dirname $f`; \
      cat front-matter.md $f > /tmp/md; \
      mv /tmp/md $f; \
    done \
 && render-markdown --prefix=/var/www `find . -name "*.md" | grep -e front-matter.md -e toc.md -v` \
 && python unpack_logo.py polars-logo.svg > /var/www/splash.svg


# minify everything in place

FROM node:alpine as bundle

WORKDIR /var/www

COPY --from=render /var/www .

COPY generator/script.js generator/script.js
COPY generator/style.css generator/style.css

RUN rm `find . -name "*.md"` \
 && apk --no-cache add git \
 && npm config set update-notifier false \
 && npm install --global --no-audit --no-fund autoprefixer \
                                              clean-css-cli \
                                              html-minifier \
                                              postcss-cli \
                                              terser \
    | grep -v ^$ \
 && git clone --depth=1 https://github.com/carnarez/markdown-render-styling.git \
 && cat markdown-render-styling/style.css markdown-render-styling/style-*.css | grep -v '@import ".*"' > _bundle.css \
 && rm -fr markdown-render-styling \
 && cat *.css > bundle.css_ \
 && rm *.css \
 && mv bundle.css_ style.css \
 && find . -name "*.css" | while read f; do \
      postcss $f --replace --use autoprefixer; \
      cleancss --output $f $f; \
    done \
 && find . -name "*.html" | while read f; do \
      html-minifier --collapse-boolean-attributes \
                    --collapse-whitespace \
                    --minify-css true \
                    --minify-js true \
                    --output $f \
                    --remove-attribute-quotes \
                    --remove-comments \
                    --remove-empty-attributes \
                    --remove-optional-tags \
                    --remove-redundant-attributes \
                    --remove-script-type-attributes \
                    --remove-style-link-type-attributes \
                    --use-short-doctype \
                    $f; \
    done \
 && find . -name "*.js" | while read f; do \
      terser --compress --mangle --module --output $f $f; \
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
