FROM --platform=$BUILDPLATFORM node:20.18.0-alpine AS base

WORKDIR /usr/src/app

FROM base AS deps
COPY package*.json ./
RUN npm ci

FROM base AS builder
COPY --from=deps /usr/src/app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM base AS production
ENV PORT=7000
USER node

COPY --chown=node:node --from=deps /usr/src/app/node_modules ./node_modules
COPY --chown=node:node . .


EXPOSE 7000

CMD ["node", "server.js"]