# DEV: simpler; npm is a normal binary
FROM node:20
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 5173
