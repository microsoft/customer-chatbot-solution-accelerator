#!/bin/sh

# Escape a value for safe inclusion inside a single-quoted JS string literal
# (handles backslashes and single quotes, e.g. a title like "Bob's Shop").
js_escape() {
  printf '%s' "$1" | sed "s/\\\\/\\\\\\\\/g; s/'/\\\\'/g"
}

if [ -z "$VITE_SCENARIO" ]; then
  VITE_SCENARIO="${DEPLOYMENT_SCENARIO:-ecommerce}"
fi

# WAF/private networking deployment: BACKEND_API_URL is set when the scenario
# backend API is private. The SPA then calls its own origin (nginx reverse-proxies
# /api/ to the private scenario backend over the VNet). The embedded chat widget
# uses /chat-api/ on the same origin, which proxies to the private chat backend.
if [ -n "${BACKEND_API_URL}" ]; then
if [ -n "${CHAT_BACKEND_API_URL}" ]; then
  CHAT_API_BASE_CONFIG="window.location.origin + '/chat-api'"
else
  CHAT_API_BASE_CONFIG="'$(js_escape "${VITE_CHAT_API_BASE_URL}")'"
fi
cat > /usr/share/nginx/html/runtime-config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: window.location.origin,
  VITE_CHAT_API_BASE_URL: ${CHAT_API_BASE_CONFIG},
  VITE_CHAT_WIDGET_THEME: '$(js_escape "${VITE_CHAT_WIDGET_THEME}")',
  VITE_SCENARIO: '$(js_escape "${VITE_SCENARIO}")',
  VITE_HOST_APP_TITLE: '$(js_escape "${VITE_HOST_APP_TITLE}")'
};
EOF
else
  if [ -z "$VITE_API_BASE_URL" ]; then
    host="${WEBSITE_HOSTNAME:-}"
    case "$host" in
      app-scenario-*.*)
        suf="${host#app-scenario-}"
        VITE_API_BASE_URL="https://api-scenario-${suf}"
        ;;
    esac
  fi

  if [ -z "$VITE_CHAT_API_BASE_URL" ]; then
    host="${WEBSITE_HOSTNAME:-}"
    case "$host" in
      app-scenario-*.*)
        suf="${host#app-scenario-}"
        VITE_CHAT_API_BASE_URL="https://api-chat-${suf}"
        ;;
    esac
  fi

cat > /usr/share/nginx/html/runtime-config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: '$(js_escape "${VITE_API_BASE_URL}")',
  VITE_CHAT_API_BASE_URL: '$(js_escape "${VITE_CHAT_API_BASE_URL}")',
  VITE_CHAT_WIDGET_THEME: '$(js_escape "${VITE_CHAT_WIDGET_THEME}")',
  VITE_SCENARIO: '$(js_escape "${VITE_SCENARIO}")',
  VITE_HOST_APP_TITLE: '$(js_escape "${VITE_HOST_APP_TITLE}")'
};
EOF
fi

# Generate the API reverse proxy config for WAF/private networking deployments.
# When BACKEND_API_URL is set the scenario backend API is private and this
# frontend's nginx proxies /api/ requests to it over the VNet.
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
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_ssl_server_name on;
    proxy_read_timeout 300s;
    proxy_connect_timeout 60s;
    proxy_buffering off;

    # WebSocket support (needed for /api/voice/ws/... connections)
    proxy_http_version 1.1;
    proxy_set_header Upgrade \$http_upgrade;
    proxy_set_header Connection "upgrade";
}

location /chat-api/ {
    resolver 168.63.129.16 valid=30s;
    set \$chat_backend "${CHAT_BACKEND_API_URL%/}";
    rewrite ^/chat-api(/.*)\$ \$1 break;
    proxy_pass \$chat_backend;
    proxy_set_header Host "$(printf '%s' "${CHAT_BACKEND_API_URL}" | sed 's|https\?://||; s|/.*||')";
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_ssl_server_name on;
    proxy_read_timeout 300s;
    proxy_connect_timeout 60s;
    proxy_buffering off;
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
