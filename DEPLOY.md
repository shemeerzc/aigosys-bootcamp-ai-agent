# Deploy Campus Agent API (systemd + Nginx + SSL)

Same pattern as the certificate app.

| Item | Value |
|------|--------|
| Server | `178.236.185.179` |
| Domain | `agent.aigosys.com` (change if you prefer) |
| App path | `/home/deploy/campus-agent` |
| API port | `8070` (localhost only) |
| Service | `campus-agent` |

---

## 0. DNS

In Cloudflare / DNS, add:

| Type | Name | Value |
|------|------|--------|
| A | `agent` | `178.236.185.179` |

Check:

```bash
dig +short agent.aigosys.com
# should print 178.236.185.179
```

---

## 1. Clone / pull on server

```bash
sudo mkdir -p /home/deploy
sudo chown -R deploy:deploy /home/deploy   # if needed

su - deploy   # or stay as root but use deploy paths carefully
cd /home/deploy

# first time:
git clone https://github.com/YOUR_USER/YOUR_REPO.git campus-agent
cd campus-agent

# later updates:
# cd /home/deploy/campus-agent && git pull
```

Use your real GitHub URL (the repo you just pushed).

---

## 2. Python venv + packages

```bash
cd /home/deploy/campus-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

---

## 3. Create `.env` on server

```bash
nano /home/deploy/campus-agent/.env
```

```bash
OPENAI_API_KEY=sk-your-real-key
CERT_API_BASE=https://certificate.aigosys.com
```

```bash
chmod 600 /home/deploy/campus-agent/.env
chown deploy:deploy /home/deploy/campus-agent/.env
```

Init DB once (creates `campus.db`):

```bash
cd /home/deploy/campus-agent
source .venv/bin/activate
python db.py
```

---

## 4. systemd service

```bash
sudo nano /etc/systemd/system/campus-agent.service
```

Paste:

```ini
[Unit]
Description=Aigosys Campus Agent API
After=network.target

[Service]
Type=simple
User=deploy
Group=deploy
WorkingDirectory=/home/deploy/campus-agent
Environment="PATH=/home/deploy/campus-agent/.venv/bin"
EnvironmentFile=/home/deploy/campus-agent/.env
ExecStart=/home/deploy/campus-agent/.venv/bin/uvicorn api:app --host 127.0.0.1 --port 8070
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Start it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable campus-agent
sudo systemctl start campus-agent
sudo systemctl status campus-agent
curl http://127.0.0.1:8070/api/health
```

Logs:

```bash
sudo journalctl -u campus-agent -f
```

---

## 5. Nginx site

```bash
sudo nano /etc/nginx/sites-available/campus-agent
```

Paste:

```nginx
server {
    listen 80;
    server_name agent.aigosys.com;

    location / {
        proxy_pass http://127.0.0.1:8070;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Important for agent SSE streaming
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 3600s;
    }
}
```

Enable:

```bash
sudo ln -sf /etc/nginx/sites-available/campus-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 6. HTTPS (Let’s Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d agent.aigosys.com
```

Follow prompts. Certbot will update the nginx file for 443.

---

## 7. Test live

```bash
curl https://agent.aigosys.com/api/health

curl -N -X POST https://agent.aigosys.com/api/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What AI events are there?"}'
```

Swagger (optional): https://agent.aigosys.com/docs

---

## Update after new git push

```bash
cd /home/deploy/campus-agent
git pull
source .venv/bin/activate
pip install -r requirements.txt
sudo systemctl restart campus-agent
curl http://127.0.0.1:8070/api/health
```

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `status` failed | `sudo journalctl -u campus-agent -n 50` |
| 502 Bad Gateway | service down / wrong port — check `curl 127.0.0.1:8070/api/health` |
| OpenAI errors | check `.env` key; `EnvironmentFile=` path |
| No stream in browser | ensure `proxy_buffering off;` in nginx |
| Permission denied on db | `chown deploy:deploy campus.db` |

---

## Endpoints

| Method | URL |
|--------|-----|
| GET | `https://agent.aigosys.com/api/health` |
| POST | `https://agent.aigosys.com/api/agent/chat` body: `{"message":"..."}` |
