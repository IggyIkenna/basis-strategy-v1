#!/bin/bash
# Generate Caddyfile from template based on environment variables

if [ "$APP_DOMAIN" = "localhost" ]; then
  # Use simple localhost config
  cat > /etc/caddy/Caddyfile <<EOF
localhost:80 {
  handle /api/* {
    reverse_proxy backend:8001
  }
  handle /health/* {
    reverse_proxy backend:8001
  }
  handle {
    root * /usr/share/caddy
    try_files {path} /index.html
    file_server
  }
}
EOF
else
  # Use domain config with TLS
  cat > /etc/caddy/Caddyfile <<EOF
${APP_DOMAIN} {
  tls ${ACME_EMAIL}
  
  handle /api/* {
    reverse_proxy backend:8001 {
      header_up Host {host}
      header_up X-Forwarded-Proto {scheme}
      header_up X-Forwarded-For {remote}
    }
  }
  
  handle /health/* {
    reverse_proxy backend:8001
  }
  
  handle {
    root * /usr/share/caddy
    try_files {path} /index.html
    file_server
  }
}
EOF
fi
