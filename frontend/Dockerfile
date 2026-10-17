FROM node:22-alpine

WORKDIR /app

COPY package*.json ./

RUN npm ci --no-audit --no-fund

COPY . .

ARG BACKEND_PROXY_ORIGIN
ENV BACKEND_PROXY_ORIGIN=$BACKEND_PROXY_ORIGIN

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start"]