FROM python:3.12.4 AS builder

WORKDIR /app


# add 1.1.1.1 and 1.0.0.1 to /etc/resolv.conf
RUN sudo echo "nameserver 1.1.1.1" >> /etc/resolv.conf && \
    sudo echo "nameserver 1.0.0.1" >> /etc/resolv.conf
COPY . .
RUN python3 hothousejazz.py


FROM nginx:latest

# Copy the static files from the build stage
COPY --from=builder /app/public /usr/share/nginx/html

# Expose port 80 to the outside world
EXPOSE 80
