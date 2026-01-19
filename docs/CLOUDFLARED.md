# Cloudflare Tunnel Setup

We’ll use Cloudflare Tunnel with two stable subdomains:

- `nancy-bot.yourdomain.com` → your laptop port `3000` (Slack hits this)
- `nancy-brain.yourdomain.com` → your laptop port `8000` (optional public API)

## 1) Create a Cloudflare Tunnel (on the laptop running Docker)
Install cloudflared:

- macOS (Homebrew): `brew install cloudflare/cloudflare/cloudflared`

Login and create a tunnel:
- `cloudflared tunnel login`
- `cloudflared tunnel create nancy`

This prints a tunnel UUID. Keep it.

## 2) Create DNS records in Cloudflare (automatic)
Replace `yourdomain.com` with your domain:

- `cloudflared tunnel route dns nancy nancy-bot.yourdomain.com`
- `cloudflared tunnel route dns nancy nancy-brain.yourdomain.com`

Cloudflare will create CNAMEs that point to the tunnel.

## 3) Create the tunnel config file
Create `~/.cloudflared/config.yml` on the laptop:

```yml
tunnel: <YOUR_TUNNEL_UUID>
credentials-file: /Users/<you>/.cloudflared/<YOUR_TUNNEL_UUID>.json

ingress:
  - hostname: nancy-bot.yourdomain.com
    service: http://localhost:3000
  - hostname: nancy-brain.yourdomain.com
    service: http://localhost:8000
  - service: http_status:404
```

(If you’re on Linux, the `credentials-file` path is usually `/home/<you>/.cloudflared/<UUID>.json`.)

## 4) Run the tunnel
In a terminal:
- `cloudflared tunnel run nancy`

Leave it running for now.

## 5) Point Slack at the stable URL (this is the part that makes Nancy “respond”)
In the Slack app portal:

- Event Subscriptions → Request URL:
  - `https://nancy-bot.yourdomain.com/slack/events`
- Interactivity & Shortcuts → Request URL:
  - `https://nancy-bot.yourdomain.com/slack/interactive`
- Slash Commands (if you use `/status`) → Request URL:
  - `https://nancy-bot.yourdomain.com/slack/commands`

Make sure all three use the SAME host `nancy-bot.yourdomain.com`.

## 6) Quick verification
From anywhere:
- `curl -i https://nancy-bot.yourdomain.com/health`
- `curl -i https://nancy-brain.yourdomain.com/health`

And locally:
- `docker-compose logs -f nancy-bot`
Then mention `@Nancy hello` in Slack; you should see `/slack/events` traffic.

## About “public nancy-brain for custom GPTs”
You *can* expose it, but it still runs on your hardware (so it’s still “on your dime” in compute). What you can do:
- Require an API key (already supported by MCP endpoints; keep `MCP_API_KEY` strong)
- Add Cloudflare Access later if you want “only approved users” (stronger than an API key)

If you paste your domain (just the hostname, not secrets), I’ll give you the exact three Slack URLs and the exact `config.yml` filled in with your chosen subdomains.