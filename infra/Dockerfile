FROM node:18-alpine AS builder

WORKDIR /app
COPY infra/nginx.conf /etc/nginx/nginx.conf
COPY frontend/package*.json ./
RUN npm install --legacy-peer-deps
COPY frontend/ .
RUN npm run build

FROM nginx:1.25-alpine
COPY --from=builder /app/build /usr/share/nginx/html
