FROM cgr.dev/chainguard/node:latest-dev

WORKDIR /app

COPY package*.json ./
RUN npm ci --no-audit --no-fund

COPY index.html ./
COPY src ./src

EXPOSE 5173
ENTRYPOINT ["npm","run","dev"]
