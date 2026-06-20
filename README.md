# Youtube_api

A production-ready YouTube Music API service optimized for Telegram music bots with high reliability, caching, rate limiting, and automatic fallback extractors.

## Features

- 🎵 **Complete API Endpoints**: Search, play, video details, audio streams, lyrics, playlists, trending, and related videos
- ⚡ **High Performance**: Redis caching with configurable TTL for fast response times
- 🔄 **Auto-Retry & Fallback**: Automatic retry with proxy rotation for maximum reliability
- 🔐 **API Key Authentication**: Secure API key management and rate limiting
- 📊 **Analytics Dashboard**: Real-time statistics and usage monitoring
- 🤖 **Telegram Bot Ready**: Optimized for Pyrogram, Telethon, and other frameworks
- 🌍 **Global Deployment**: Support for Vercel frontend and Render/Railway backend
- 🛡️ **Rate Limiting**: Configurable rate limits per endpoint
- 📦 **Docker Support**: Easy deployment with Docker and Docker Compose
- 🔄 **Auto-Update**: Latest yt-dlp version with automatic extractor updates

## API Endpoints

### Search
```http
GET /api/search?song={song_name}
```
Search for songs on YouTube.

### Play
```http
GET /api/play?song={song_name}
```
Get direct audio information for a song.

### Video Details
```http
GET /api/video?id={video_id}
```
Get detailed video information.

### Audio Stream
```http
GET /api/audio?id={video_id}
```
Get downloadable audio stream URL.

### Lyrics
```http
GET /api/lyrics?song={song_name}
```
Get lyrics for a song.

### Playlist
```http
GET /api/playlist?id={playlist_id}
```
Get playlist information and tracks.

### Trending
```http
GET /api/trending?category={category}
```
Get trending videos (default: music).

### Related Videos
```http
GET /api/related?id={video_id}
```
Get related videos for a given video.

### Health Check
```http
GET /api/health
```
Check API status and health.

## Quick Start

### Using Docker (Recommended)

1. Clone the repository:
```bash
git clone https://github.com/yourusername/youtube-music-api.git
cd youtube-music-api
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Deploy with Docker Compose:
```bash
chmod +x deploy.sh
./deploy.sh
```

Or manually:
```bash
docker-compose up -d
```

4. Access the API:
- Dashboard: http://localhost
- API Docs: http://localhost/docs
- Health Check: http://localhost/api/health

### Using Python

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables:
```bash
export API_HOST=0.0.0.0
export API_PORT=8000
export ENVIRONMENT=development
```

3. Run the server:
```bash
uvicorn app.main:app --reload
```

## Usage Examples

### Python

```python
import requests

API_BASE = "http://localhost:8000/api"
API_KEY = "your-api-key"

headers = {"X-API-Key": API_KEY}

# Search for a song
response = requests.get(
    f"{API_BASE}/search",
    params={"song": "Never Gonna Give You Up"},
    headers=headers
)
results = response.json()
print(results)

# Get audio stream
video_id = results[0]["video_id"]
audio = requests.get(
    f"{API_BASE}/audio",
    params={"id": video_id},
    headers=headers
).json()
print(f"Stream URL: {audio['url']}")
```

### JavaScript/Node.js

```javascript
const API_BASE = "http://localhost:8000/api";
const API_KEY = "your-api-key";

async function searchSong(songName) {
    const response = await fetch(
        `${API_BASE}/search?song=${encodeURIComponent(songName)}`,
        { headers: { "X-API-Key": API_KEY } }
    );
    return await response.json();
}

const results = await searchSong("Never Gonna Give You Up");
console.log(results);
```

### cURL

```bash
# Search for a song
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/search?song=Never%20Gonna%20Give%20You%20Up"

# Get video details
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/video?id=dQw4w9WgXcQ"

# Get audio stream
curl -H "X-API-Key: your-api-key" \
  "http://localhost:8000/api/audio?id=dQw4w9WgXcQ"
```

## Telegram Bot Integration

### Pyrogram

```python
from pyrogram import Client, filters
import requests

API_BASE = "http://localhost:8000/api"
API_KEY = "your-api-key"

app = Client("my_bot", api_id=12345, api_hash="your_api_hash")

@app.on_message(filters.command("play"))
async def play_song(client, message):
    song_name = " ".join(message.command[1:])
    
    # Search for song
    response = requests.get(
        f"{API_BASE}/search",
        params={"song": song_name},
        headers={"X-API-Key": API_KEY}
    )
    results = response.json()
    
    if not results:
        await message.reply("Song not found!")
        return
    
    video = results[0]
    
    # Get audio stream
    audio = requests.get(
        f"{API_BASE}/audio",
        params={"id": video["video_id"]},
        headers={"X-API-Key": API_KEY}
    ).json()
    
    # Send audio to chat
    await message.reply_audio(
        audio["url"],
        title=video["title"],
        duration=video["duration"],
        thumb=video["thumbnail"]
    )

app.run()
```

### Telethon

```python
from telethon import TelegramClient, events
import requests

API_BASE = "http://localhost:8000/api"
API_KEY = "your-api-key"

client = TelegramClient("my_bot", api_id=12345, api_hash="your_api_hash")

@client.on(events.NewMessage(pattern='/play'))
async def handler(event):
    song_name = event.message.message.split('/play ')[1]
    
    # Search for song
    response = requests.get(
        f"{API_BASE}/search",
        params={"song": song_name},
        headers={"X-API-Key": API_KEY}
    )
    results = response.json()
    
    if not results:
        await event.reply("Song not found!")
        return
    
    video = results[0]
    
    # Get audio stream
    audio = requests.get(
        f"{API_BASE}/audio",
        params={"id": video["video_id"]},
        headers={"X-API-Key": API_KEY}
    ).json()
    
    # Send audio to chat
    await event.reply(
        f"🎵 {video['title']}\n"
        f"👤 {video['uploader']}\n"
        f"⏱️ {video['duration']}s\n"
        f"🔗 {audio['url']}"
    )

client.start()
client.run_until_disconnected()
```

### Python-Telegram-Bot

```python
from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
import requests

API_BASE = "http://localhost:8000/api"
API_KEY = "your-api-key"

def play(update: Update, context: CallbackContext):
    song_name = " ".join(context.args)
    
    # Search for song
    response = requests.get(
        f"{API_BASE}/search",
        params={"song": song_name},
        headers={"X-API-Key": API_KEY}
    )
    results = response.json()
    
    if not results:
        update.message.reply_text("Song not found!")
        return
    
    video = results[0]
    
    # Get audio stream
    audio = requests.get(
        f"{API_BASE}/audio",
        params={"id": video["video_id"]},
        headers={"X-API-Key": API_KEY}
    ).json()
    
    # Send audio to chat
    update.message.reply_audio(
        audio["url"],
        title=video["title"],
        duration=video["duration"],
        caption=f"🎵 {video['title']}\n👤 {video['uploader']}"
    )

updater = Updater("YOUR_BOT_TOKEN")
updater.dispatcher.add_handler(CommandHandler("play", play))
updater.start_polling()
updater.idle()
```

## Configuration

Environment variables can be configured in the `.env` file:

```env
# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_KEY_SECRET=your-secret-key-change-this
ENVIRONMENT=production

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_PERIOD=60

# Proxy Configuration
HTTP_PROXY=
HTTPS_PROXY=
PROXY_LIST=

# Cache Configuration
CACHE_TTL=3600
ENABLE_CACHE=true

# API Keys (comma-separated for multiple keys)
API_KEYS=key1,key2,key3

# Fallback Servers
FALLBACK_SERVERS=

# Logging
LOG_LEVEL=INFO
```

## Deployment

### Render

1. Create a new web service on Render
2. Connect your GitHub repository
3. Use the `render.yaml` configuration file
4. Set environment variables in the Render dashboard
5. Deploy

### Railway

1. Create a new project on Railway
2. Add a Python service
3. Set environment variables
4. Deploy

### Vercel (Frontend)

1. Install Vercel CLI: `npm i -g vercel`
2. Run: `vercel` in the project directory
3. Follow the prompts to deploy the frontend

### Docker

```bash
# Build and start
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down

# Rebuild
docker-compose up -d --build
```

## API Response Format

### Search Response
```json
[
  {
    "video_id": "dQw4w9WgXcQ",
    "title": "Never Gonna Give You Up",
    "duration": 212,
    "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
    "uploader": "Rick Astley",
    "view_count": 1400000000,
    "upload_date": "20091025",
    "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
  }
]
```

### Video Info Response
```json
{
  "video_id": "dQw4w9WgXcQ",
  "title": "Never Gonna Give You Up",
  "duration": 212,
  "thumbnail": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
  "uploader": "Rick Astley",
  "uploader_id": "UCuAXFkgsw1L7xaCfnd5JJOw",
  "view_count": 1400000000,
  "upload_date": "20091025",
  "webpage_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "description": "...",
  "tags": ["rick", "astley", "never", "gonna", "give", "you", "up"],
  "categories": ["Music"]
}
```

### Audio Stream Response
```json
{
  "url": "https://example.com/audio_stream",
  "format": "140",
  "quality": "medium",
  "filesize": 5242880,
  "ext": "m4a",
  "acodec": "mp4a.40.2",
  "abr": 128
}
```

## Rate Limiting

The API implements rate limiting to ensure fair usage:

- Default: 100 requests per minute per IP
- Customizable via `RATE_LIMIT_REQUESTS` and `RATE_LIMIT_PERIOD` environment variables
- Rate limit headers are included in responses:
  - `X-RateLimit-Limit`: Request limit
  - `X-RateLimit-Remaining`: Remaining requests
  - `X-RateLimit-Reset`: Reset time

## Caching

Responses are cached using Redis for improved performance:

- Default TTL: 1 hour (3600 seconds)
- Stream URLs: 30 minutes (1800 seconds)
- Trending: 30 minutes (1800 seconds)
- Lyrics: 2 hours (7200 seconds)
- Configurable via `CACHE_TTL` environment variable

## Error Handling

The API returns consistent error responses:

```json
{
  "error": "Error type",
  "detail": "Detailed error message",
  "status_code": 400
}
```

Common error codes:
- `400`: Bad Request
- `401`: Unauthorized (missing API key)
- `403`: Forbidden (invalid API key)
- `404`: Not Found
- `429`: Rate Limit Exceeded
- `500`: Internal Server Error

## Monitoring

Access the admin dashboard at `/api/admin/stats` (requires API key) to view:
- Total requests
- Success rate
- Cache hit rate
- Active API keys
- Uptime

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.

## Support

For support, please open an issue on GitHub or contact support@example.com.

## Disclaimer

This API is for educational purposes only. Please respect YouTube's Terms of Service and copyright laws.
