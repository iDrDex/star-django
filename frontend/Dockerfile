FROM kkarczmarczyk/node-yarn:7.1
RUN yarn global add webpack
RUN yarn global add webpack-dev-server
RUN mkdir -p /app/user/
WORKDIR /app
ADD package.json ./package.json
RUN yarn
ADD . /app/user/
WORKDIR /app/user/
