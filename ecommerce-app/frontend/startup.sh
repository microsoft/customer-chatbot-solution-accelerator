#!/bin/sh

if [ -z "$VITE_API_BASE_URL" ]; then
  host="${WEBSITE_HOSTNAME:-}"
  case "$host" in
    app-ecom-*.*)
      suf="${host#app-ecom-}"
      VITE_API_BASE_URL="https://api-ecom-${suf}"
      ;;
  esac
fi

if [ -z "$VITE_CHAT_API_BASE_URL" ]; then
  host="${WEBSITE_HOSTNAME:-}"
  case "$host" in
    app-ecom-*.*)
      suf="${host#app-ecom-}"
      VITE_CHAT_API_BASE_URL="https://api-chat-${suf}"
      ;;
  esac
fi

if [ -z "$VITE_SCENARIO" ]; then
  VITE_SCENARIO="${DEPLOYMENT_SCENARIO:-ecommerce}"
fi

cat > /usr/share/nginx/html/runtime-config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: '${VITE_API_BASE_URL}',
  VITE_CHAT_API_BASE_URL: '${VITE_CHAT_API_BASE_URL}',
  VITE_CHAT_WIDGET_THEME: '${VITE_CHAT_WIDGET_THEME}',
  VITE_SCENARIO: '${VITE_SCENARIO}',
  VITE_HOST_APP_TITLE: '${VITE_HOST_APP_TITLE}'
};
EOF

nginx -g "daemon off;"
