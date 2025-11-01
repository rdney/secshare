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

# Install serve globally (create package.json first to avoid warnings)
RUN echo '{}' > package.json && \
    npm install -g serve@14.2.4 && \
    rm package.json

# Use Railway's PORT variable
CMD serve dist --single --listen ${PORT:-8080}
