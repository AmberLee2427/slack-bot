FROM python:3.12-alpine AS builder

WORKDIR /docs

RUN pip install --no-cache-dir "mkdocs>=1.6,<2" "mkdocs-material>=9,<10"

COPY hosted_docs/mkdocs.yml ./mkdocs.yml
COPY hosted_docs/docs ./docs

RUN mkdocs build --strict

FROM nginx:1.29-alpine

COPY --from=builder /docs/site /usr/share/nginx/html

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O /dev/null http://localhost/ || exit 1

