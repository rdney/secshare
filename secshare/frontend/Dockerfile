# Build stage
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . .
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Copy built files
COPY --from=builder /app/dist ./dist

# Install serve globally
RUN npm install --global serve@14.2.4

# Use Railway's PORT variable with shell form to allow variable substitution
CMD sh -c "serve dist --single --listen ${PORT:-8080}"
