#!/bin/bash
# Complete deployment script - run this on your GCP VM

echo "🚀 Starting deployment completion..."
echo "   - Uses unified environment file: backend/env.unified"

# Navigate to the project directory
cd ~/basis-strategy-v1/deploy

echo "📝 Creating .env file..."
cat > .env << 'EOF'
APP_DOMAIN=defi-project.odum-research.com
ACME_EMAIL=ikenna@odum-research.com
BASIS_API__CORS_ORIGINS=["https://defi-project.odum-research.com"]
EOF

echo "✅ .env file created"

echo "📝 Configuring backend/env.unified for production..."
cd ../backend
if [ -f "env.unified" ]; then
    # Update environment settings for production
    sed -i 's/BASIS_ENVIRONMENT=dev/BASIS_ENVIRONMENT=production/' env.unified
    sed -i 's/BASIS_DEPLOYMENT=local/BASIS_DEPLOYMENT=cloud/' env.unified
    sed -i 's|BASIS_API__CORS_ORIGINS=\["http://localhost:5173"\]|BASIS_API__CORS_ORIGINS=["https://defi-project.odum-research.com"]|' env.unified
    sed -i 's|BASIS_REDIS__URL=redis://localhost:6379/0|BASIS_REDIS__URL=redis://redis:6379/0|' env.unified
    echo "✅ Updated env.unified for production"
else
    echo "❌ backend/env.unified not found!"
    exit 1
fi
cd ../deploy

echo "🛑 Stopping existing containers..."
docker compose down

echo "🔄 Starting containers with updated configuration..."
docker compose up -d --build

echo "⏳ Waiting for containers to start..."
sleep 15

echo "📋 Checking container status..."
docker ps

echo "📊 Checking backend logs..."
docker logs --tail 20 deploy-backend-1

echo "📊 Checking caddy logs..."
docker logs --tail 20 deploy-caddy-1

echo "🧪 Testing HTTP endpoints..."
echo "Testing health via IP:"
curl -I http://34.38.81.226/health/ || echo "❌ Health check via IP failed"

echo "Testing health via domain:"
curl -I http://defi-project.odum-research.com/health/ || echo "❌ Health check via domain failed"

echo "Testing frontend via domain:"
curl -I http://defi-project.odum-research.com/ || echo "❌ Frontend via domain failed"

echo "🔒 Updating Caddyfile for HTTPS..."
cat > Caddyfile << 'EOF'
defi-project.odum-research.com {
  tls ikenna@odum-research.com

  @api path /api/*
  reverse_proxy @api backend:8001 {
    header_up Host {host}
    header_up X-Forwarded-Proto {scheme}
    header_up X-Forwarded-For {remote}
  }

  @health path /health/*
  reverse_proxy @health backend:8001

  root * /usr/share/caddy
  try_files {path} /index.html
  file_server
}
EOF

echo "🔄 Restarting Caddy with HTTPS..."
docker compose up -d caddy

echo "⏳ Waiting for HTTPS to initialize..."
sleep 30

echo "📊 Checking caddy logs for HTTPS..."
docker logs --tail 30 deploy-caddy-1

echo "🧪 Testing HTTPS endpoints..."
echo "Testing HTTPS health:"
curl -I https://defi-project.odum-research.com/health/ || echo "❌ HTTPS health check failed"

echo "Testing HTTPS frontend:"
curl -I https://defi-project.odum-research.com/ || echo "❌ HTTPS frontend failed"

echo "🎉 Deployment complete!"
echo "🌐 Your site should be available at: https://defi-project.odum-research.com/"
echo ""
echo "If there are any issues, check the logs with:"
echo "  docker logs deploy-caddy-1"
echo "  docker logs deploy-backend-1"
