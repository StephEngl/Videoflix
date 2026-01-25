FROM python:3.12-alpine as base

LABEL maintainer="stephanie.englberger@icloud.com"
LABEL version="1.0"
LABEL description="Python 3.14.0a7 Alpine 3.21"

WORKDIR /app

COPY --link backend.entrypoint.sh .
RUN chmod +x backend.entrypoint.sh

RUN apk update && \
    apk add --no-cache --upgrade bash && \
    apk add --no-cache postgresql-client ffmpeg && \
    apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
    apk del .build-deps

# Development stage - don't copy files, rely on volume mount
FROM base as development

COPY --link backend.development-entrypoint.sh .
RUN chmod +x backend.development-entrypoint.sh

EXPOSE 8000
ENTRYPOINT [ "./backend.development-entrypoint.sh" ]

# Production stage - copy all files
FROM base as production
COPY . .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    chmod +x backend.entrypoint.sh
EXPOSE 8000
ENTRYPOINT [ "./backend.entrypoint.sh" ]
