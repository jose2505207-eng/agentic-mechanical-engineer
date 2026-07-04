# Frontend image: Next.js production build.
# IMPORTANT: Next evaluates next.config.mjs rewrites at BUILD time, so
# BACKEND_URL must be set here (compose service DNS name), not just at run.
FROM node:22-alpine

ARG BACKEND_URL=http://backend:8000
ENV BACKEND_URL=$BACKEND_URL

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "start"]
