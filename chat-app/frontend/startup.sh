#!/bin/sh

# WAF/private networking deployment: BACKEND_API_URL is set when the backend API
# is private. The SPA then calls its own origin (nginx reverse-proxies /api/ to
# the private backend over the VNet).
if [ -n "${BACKEND_API_URL}" ]; then
cat > /usr/share/nginx/html/runtime-config.js << 'RUNTIMEEOF'
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: window.location.origin
};
RUNTIMEEOF
else
  if [ -z "$VITE_API_BASE_URL" ]; then
    host="${WEBSITE_HOSTNAME:-}"
    case "$host" in
      app-chat-*.*)
        suf="${host#app-chat-}"
        VITE_API_BASE_URL="https://api-chat-${suf}"
        ;;
    esac
  fi

cat > /usr/share/nginx/html/runtime-config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: '${VITE_API_BASE_URL}'
};
EOF
fi

# Generate the API reverse proxy config for WAF/private networking deployments.
# When BACKEND_API_URL is set the backend API is private and this frontend's
# nginx proxies /api/ requests to it over the VNet.
if [ -n "${BACKEND_API_URL}" ]; then
  # Strip any trailing slash so proxy_pass + the /api/ location prefix don't produce a malformed path.
  BACKEND_API_URL="${BACKEND_API_URL%/}"
  BACKEND_HOST=$(printf '%s' "${BACKEND_API_URL}" | sed 's|https\?://||; s|/.*||')
  cat > /etc/nginx/conf.d/api-proxy.conf << PROXYEOF
# Reverse proxy for backend API - WAF private networking deployment
location /api/ {
    resolver 168.63.129.16 valid=30s;
    set \$backend "${BACKEND_API_URL}";
    proxy_pass \$backend;
    proxy_set_header Host "${BACKEND_HOST}";
    proxy_set_header Authorization \$http_x_backend_authorization;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_ssl_server_name on;
    proxy_read_timeout 300s;
    proxy_connect_timeout 60s;
    proxy_buffering off;

    proxy_redirect ~^https?://${BACKEND_HOST}/(.*)\$ /\$1;


    # WebSocket support (needed for /api/voice/ws/... connections)
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
}
PROXYEOF
else
  # Empty file for non-WAF deployments (ensures the nginx include does not error)
  > /etc/nginx/conf.d/api-proxy.conf
fi

exec nginx -g "daemon off;"
