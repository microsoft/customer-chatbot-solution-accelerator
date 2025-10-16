#!/bin/sh

# Create runtime config script that injects App Service environment variables
cat > /usr/share/nginx/html/runtime-config.js << EOF
// Runtime configuration injected by App Service
window.__RUNTIME_CONFIG__ = {
  VITE_API_BASE_URL: '${VITE_API_BASE_URL}',
  VITE_AZURE_CLIENT_ID: '${VITE_AZURE_CLIENT_ID}',
  VITE_AZURE_TENANT_ID: '${VITE_AZURE_TENANT_ID}',
  VITE_AZURE_AUTHORITY: '${VITE_AZURE_AUTHORITY}',
  VITE_REDIRECT_URI: '${VITE_REDIRECT_URI}',
  VITE_ENVIRONMENT: '${VITE_ENVIRONMENT}'
};
EOF

# Start nginx
nginx -g "daemon off;"
