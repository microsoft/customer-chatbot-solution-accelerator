# Multi-stage build for React frontend
FROM mcr.microsoft.com/azurelinux/base/nodejs:20 AS builder
 
# Set working directory
WORKDIR /app
 
# Copy package files
COPY package*.json ./
 
# Install dependencies with legacy peer deps for React 19 compatibility
RUN npm ci --legacy-peer-deps
 
# Copy source code (excluding node_modules)
COPY . .
 
# Build the application
RUN npm run build
 
# Production stage
FROM mcr.microsoft.com/azurelinux/base/nginx:1.25
 
# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html
 
# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf
 
# Copy startup script
COPY startup.sh /docker-entrypoint.d/startup.sh
RUN chmod +x /docker-entrypoint.d/startup.sh
RUN sed -i 's/\r$//' /docker-entrypoint.d/startup.sh
 
# Expose port 80
EXPOSE 80
 
# Start with custom script that injects environment variables
CMD ["/bin/sh", "-c", "/docker-entrypoint.d/startup.sh"]