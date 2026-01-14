# Deploy settings
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files (relative to root context)
COPY src/ui/web/package*.json ./

# Install dependencies
RUN npm ci

# Copy source (relative to root context)
COPY src/ui/web/ .

# Build arguments
ARG REACT_APP_VERSION
ARG REACT_APP_GIT_SHA
ARG REACT_APP_BUILD_TIME
ARG REACT_APP_API_URL

# Build
RUN npm run build

# Nginx stage
FROM nginx:alpine

# Copy build artifacts
COPY --from=builder /app/build /usr/share/nginx/html

# Copy nginx config (relative to root context)
COPY deploy/docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
