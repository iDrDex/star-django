FROM node:7-alpine
RUN yarn global add webpack
RUN yarn global add webpack-dev-server
RUN mkdir -p /app/user/
WORKDIR /app
ADD package.json ./package.json
ADD yarn.lock ./yarn.lock
RUN yarn
ADD . /app/user/
WORKDIR /app/user/
