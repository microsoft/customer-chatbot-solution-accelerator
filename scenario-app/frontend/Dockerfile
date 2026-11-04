FROM mcr.microsoft.com/azurelinux/base/nodejs:24 AS widget-builder
WORKDIR /src/chat-app/frontend
COPY chat-app/frontend/package*.json chat-app/frontend/.npmrc ./
RUN npm ci --legacy-peer-deps
COPY chat-app/frontend/ ./
RUN npm run build

FROM mcr.microsoft.com/azurelinux/base/nodejs:24 AS app-builder
WORKDIR /src/scenario-app/frontend
ARG VITE_SCENARIO=ecommerce
ENV VITE_SCENARIO=$VITE_SCENARIO
COPY scenario-app/frontend/package*.json scenario-app/frontend/.npmrc ./
RUN npm ci --legacy-peer-deps
COPY scenario-app/frontend/ ./
RUN npm run build
COPY --from=widget-builder /src/chat-app/frontend/dist/widget.js ./dist/widget.js

FROM mcr.microsoft.com/azurelinux/base/nginx:1.28.3-8-azl3.0.20260722
COPY --from=app-builder /src/scenario-app/frontend/dist /usr/share/nginx/html
COPY scenario-app/frontend/nginx.conf /etc/nginx/nginx.conf

# Create empty api-proxy conf (overwritten at startup for WAF/private deployments)
RUN mkdir -p /etc/nginx/conf.d && touch /etc/nginx/conf.d/api-proxy.conf

COPY scenario-app/frontend/startup.sh /docker-entrypoint.d/startup.sh
RUN chmod +x /docker-entrypoint.d/startup.sh
RUN sed -i 's/\r$//' /docker-entrypoint.d/startup.sh
EXPOSE 80
CMD ["/bin/sh", "-c", "/docker-entrypoint.d/startup.sh"]
