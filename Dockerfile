FROM python:3-alpine

# Getting things ready
WORKDIR /usr/src/whoaremyrepresentatives
COPY Pipfile.lock Pipfile ./

# Install dependencies & configure machine
ARG GF_UID="500"
ARG GF_GID="500"
RUN apk update && \
	apk add bash && \
	pip install pipenv && \
	pipenv install --system --deploy && \
	addgroup --system -g $GF_GID appgroup && \
	adduser appuser --system --uid $GF_UID -G appgroup

# Install Shynet
COPY src .

# Launch
USER appuser
EXPOSE 8080
ENTRYPOINT [ "gunicorn", "server:app", "--bind", "0.0.0.0:8080" ]
