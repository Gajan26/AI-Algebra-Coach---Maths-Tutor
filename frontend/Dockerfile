# Multi-stage build for AI Algebra Coach frontend
# Build stage
FROM node:20-alpine as builder

WORKDIR /app

# Copy package files
COPY package*.json ./
RUN npm ci

# Copy source code
COPY . .

# Build the Next.js application
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Clean up node_modules and cache
RUN npm prune --production && npm cache clean --force

# Runtime stage
FROM node:20-alpine

WORKDIR /app

# Copy built application and dependencies from builder
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY package.json ./

# Set environment
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD node -e "require('http').get('http://localhost:3000', (r) => {if (r.statusCode !== 200) throw new Error(r.statusCode)})"

# Start the application
CMD ["npm", "start"]
