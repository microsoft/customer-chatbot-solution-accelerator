#!/bin/sh

# Generate runtime config for React app.
# In WAF mode (BACKEND_API_URL set), VITE_API_BASE_URL is empty so we use
# window.location.origin to make the SPA call its own origin (nginx proxies /api/).
if [ -n "${BACKEND_API_URL}" ]; then
cat > /usr/share/nginx/html/runtime-config.js << 'RUNTIMEEOF'
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: window.location.origin
};
RUNTIMEEOF
else
cat > /usr/share/nginx/html/runtime-config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: '${VITE_API_BASE_URL}'
};
EOF
fi

# Generate API reverse proxy config for WAF/private networking deployments.
# When BACKEND_API_URL is set, the backend API is private and the frontend
# nginx proxies /api/ requests to it over the VNet.
if [ -n "${BACKEND_API_URL}" ]; then
  BACKEND_HOST=$(echo "${BACKEND_API_URL}" | sed 's|https://||; s|http://||; s|/.*||')
  cat > /etc/nginx/conf.d/api-proxy.conf << PROXYEOF
# Reverse proxy for backend API - WAF private networking deployment
location /api/ {
    resolver 168.63.129.16 valid=30s;
    set \$backend "${BACKEND_API_URL}";
    proxy_pass \$backend;
    proxy_set_header Host ${BACKEND_HOST};
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_ssl_server_name on;
    proxy_read_timeout 300s;
    proxy_connect_timeout 60s;
    proxy_buffering off;
}
PROXYEOF
else
  # Empty file for non-WAF deployments (ensures nginx include does not error)
  > /etc/nginx/conf.d/api-proxy.conf
fi

nginx -g "daemon off;"
