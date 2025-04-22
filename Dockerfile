FROM python:3.13.3 AS builder


RUN pip install uv

WORKDIR /app

COPY uv.lock pyproject.toml ./
RUN uv sync
COPY . .
RUN uv run python3 hothousejazz.py


FROM nginx:latest

# Copy the static files from the build stage
COPY --from=builder /app/public /usr/share/nginx/html

# Expose port 80 to the outside world
EXPOSE 80
