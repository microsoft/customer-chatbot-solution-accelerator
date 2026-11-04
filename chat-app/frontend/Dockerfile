# Multi-stage build for React frontend
FROM mcr.microsoft.com/azurelinux/base/nodejs:24 AS builder
 
# Set working directory
WORKDIR /app
 
# Copy package files and npm registry config (Microsoft proxy feed)
COPY package*.json .npmrc ./
 
# Install dependencies with legacy peer deps for React 19 compatibility
RUN npm ci --legacy-peer-deps
 
# Copy source code (excluding node_modules)
COPY . .
 
# Build the application
RUN npm run build
 
# Production stage
FROM mcr.microsoft.com/azurelinux/base/nginx:1.28.3-8-azl3.0.20260722

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

# Create empty api-proxy conf (overwritten at startup for WAF/private deployments)
RUN mkdir -p /etc/nginx/conf.d && touch /etc/nginx/conf.d/api-proxy.conf

COPY startup.sh /docker-entrypoint.d/startup.sh
RUN chmod +x /docker-entrypoint.d/startup.sh
RUN sed -i 's/\r$//' /docker-entrypoint.d/startup.sh
 
# Expose port 80
EXPOSE 80
 
# Start with custom script that injects environment variables
CMD ["/bin/sh", "-c", "/docker-entrypoint.d/startup.sh"]