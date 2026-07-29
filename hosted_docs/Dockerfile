FROM python:3.12-alpine AS builder

WORKDIR /docs

RUN pip install --no-cache-dir "mkdocs>=1.6,<2" "mkdocs-material>=9,<10"

COPY hosted_docs/mkdocs.yml ./mkdocs.yml
COPY hosted_docs/docs ./docs
COPY ref/nancy-brain/site/nancy-brain2.png ./docs/assets/nancy-brain2.png
COPY ref/nancy-brain/site/nancy-brain.png ./docs/assets/nancy-brain.png
COPY ["ref/nancy-brain/docs/20250803_1719_Wise Animated Portrait_remix_01k1rwq22nfw9r7md82nrv3vjw.png", "./docs/assets/nancy-portrait.png"]

RUN mkdocs build --strict

FROM nginx:1.29-alpine

COPY --from=builder /docs/site /usr/share/nginx/html

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD wget -q -O /dev/null http://localhost/ || exit 1
