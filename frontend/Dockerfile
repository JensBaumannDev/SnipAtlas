FROM node:24-alpine AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm install --global npm@11.6.2 && npm ci

COPY . .
RUN npm run build

FROM node:24-alpine

ENV NODE_ENV=production

WORKDIR /app

COPY --from=build /app/dist/snipatlas ./dist/snipatlas

USER node

EXPOSE 4000

CMD ["node", "dist/snipatlas/server/server.mjs"]
