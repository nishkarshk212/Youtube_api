# Render Deployment Guide

This guide will help you deploy the YouTube Music API to Render.

## Prerequisites

- GitHub account with the repository uploaded (already done: https://github.com/nishkarshk212/Youtube_api.git)
- Render account (free at render.com)

## Step 1: Create Render Account

1. Go to [render.com](https://render.com)
2. Sign up or log in
3. Connect your GitHub account

## Step 2: Deploy the Web Service

1. Click **"New +"** button
2. Select **"Web Service"**
3. Connect your GitHub repository: `nishkarshk212/Youtube_api`
4. Configure the service:

### Build & Deploy Settings
- **Name**: `youtube-music-api`
- **Region**: Select nearest region (e.g., Oregon)
- **Branch**: `main`
- **Runtime**: `Python`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### Environment Variables
Add the following environment variables:

```
API_HOST=0.0.0.0
API_PORT=$PORT
ENVIRONMENT=production
REDIS_HOST=your-redis-host
REDIS_PORT=6379
REDIS_DB=0
ENABLE_CACHE=false
LOG_LEVEL=INFO
```

**Note**: We'll set up Redis in the next step.

5. Click **"Create Web Service"**

## Step 3: Add Redis Service

1. Click **"New +"** button
2. Select **"Redis"**
3. Configure:
   - **Name**: `youtube-music-redis`
   - **Region**: Same as your web service
   - **Plan**: Free (or paid for production)

4. Click **"Create Redis"**

## Step 4: Update Web Service with Redis URL

1. Go to your web service dashboard
2. Click **"Environment"** tab
3. Update the environment variables:
   - Remove `REDIS_HOST` and `REDIS_PORT`
   - Add: `REDIS_URL=${REDIS_URL}` (Render automatically provides this)
   - Set `ENABLE_CACHE=true`

4. Click **"Save Changes"**
5. Click **"Manual Deploy"** → **"Clear build cache & deploy"**

## Step 5: Configure API Keys (Optional)

If you want to use API key authentication:

1. Go to your web service dashboard
2. Click **"Environment"** tab
3. Add: `API_KEYS=your-api-key-1,your-api-key-2`
4. Click **"Save Changes"** and redeploy

## Step 6: Access Your API

Once deployed, Render will provide:
- **API URL**: `https://youtube-music-api.onrender.com`
- **Dashboard**: `https://youtube-music-api.onrender.com/`
- **API Docs**: `https://youtube-music-api.onrender.com/docs`
- **Health Check**: `https://youtube-music-api.onrender.com/api/health`

## Step 7: Test the Deployment

```bash
# Test health endpoint
curl https://youtube-music-api.onrender.com/api/health

# Test search endpoint
curl "https://youtube-music-api.onrender.com/api/search?song=Never%20Gonna%20Give%20You%20Up"
```

## Using render.yaml (Alternative Method)

The repository includes a `render.yaml` file for automatic deployment:

1. In Render dashboard, click **"New +"**
2. Select **"Existing repository"**
3. Render will automatically detect `render.yaml`
4. Review and confirm the configuration
5. Click **"Deploy"**

## Monitoring

- View logs in the Render dashboard
- Monitor metrics (CPU, memory, response time)
- Set up alerts for errors or high response times

## Scaling

- **Free Tier**: Limited resources, suitable for testing
- **Starter ($7/month)**: Better performance, more resources
- **Standard ($25/month)**: Production-ready with auto-scaling

## Troubleshooting

### Build Fails
- Check build logs in Render dashboard
- Ensure all dependencies are in `requirements.txt`
- Verify Python version compatibility

### Runtime Errors
- Check runtime logs
- Verify environment variables are set correctly
- Ensure Redis is accessible if caching is enabled

### Slow Performance
- Upgrade to a paid plan for more resources
- Enable Redis caching
- Consider using a CDN for static assets

## Next Steps

1. Set up a custom domain (optional)
2. Configure SSL certificates (automatic on Render)
3. Set up monitoring and alerts
4. Integrate with your Telegram bot

## Support

For issues specific to Render, check their [documentation](https://render.com/docs).
