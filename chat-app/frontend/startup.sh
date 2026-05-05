#!/bin/sh

cat > /usr/share/nginx/html/runtime-config.js << EOF
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: '${VITE_API_BASE_URL}'
};
EOF

nginx -g "daemon off;"
