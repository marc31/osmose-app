# Front dockerfile

# Build app stage
FROM node:16-alpine3.13 as build-app

WORKDIR /opt

COPY frontend/package.json .

RUN npm install

COPY frontend .

RUN PUBLIC_URL=/app npm run build

# Build website stage
FROM node:16-alpine3.13 as build-website

WORKDIR /opt

COPY website/package.json .

RUN npm install

COPY website .

RUN npm run build

# Deploy stage
FROM nginxinc/nginx-unprivileged:1.20-alpine

ARG UID=101
ARG GID=101

COPY ./dockerfiles/nginx.conf.template /etc/nginx/templates/default.conf.template

COPY --from=build-app /opt/dist /usr/share/nginx/app
COPY --from=build-website /opt/build /usr/share/nginx/website

USER 0

RUN apk --no-cache add shadow # needed to use usermod and groupmod
RUN usermod -u $UID -o nginx
RUN groupmod -g $GID -o nginx
RUN find / -user 101 -exec chown -h nginx {} \;
RUN find / -group 101 -exec chgrp -h nginx {} \;

USER $UID
