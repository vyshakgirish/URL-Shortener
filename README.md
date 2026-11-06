# URL Shortener (Flask + Redis + Nginx)

Three containers on a custom network, orchestrated with Compose:

| Container | Role | Exposed? |
|-----------|------|----------|
| nginx | Reverse proxy, the only public entry point (port 80) | Yes |
| app | Flask app served by Gunicorn | No (internal) |
| redis | Stores links + hit counters, data in the `redis-data` volume | No (internal) |

## Project structure

```
url-shortener/
├── docker-compose.yml
├── test.sh
├── README.md
├── app/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
└── nginx/
    └── nginx.conf
```

## 1. Prerequisites on RHEL (8/9)

RHEL ships Podman. Pick ONE option.

### Option A: Podman

```bash
sudo dnf install -y podman
sudo dnf install -y epel-release      # or enable EPEL per Red Hat docs
sudo dnf install -y podman-compose
```

Use `podman-compose` wherever this README says `docker compose`.
Rootless Podman cannot bind port 80 by default. Either run with `sudo`,
change the port mapping in docker-compose.yml to `"8080:80"`, or run:

```bash
sudo sysctl -w net.ipv4.ip_unprivileged_port_start=80
```

### Option B: Docker CE

```bash
sudo dnf install -y dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/rhel/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
sudo systemctl enable --now docker
sudo usermod -aG docker $USER         # log out and back in afterward
```

### Open the firewall

```bash
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --reload
```

Keep SELinux enforcing. The `:Z` flag on the Nginx bind mount handles labeling.

## 2. Run it

```bash
unzip url-shortener.zip
cd url-shortener
docker compose up -d --build          # or: podman-compose up -d --build
docker compose ps                     # all three should be Up
```

Set `BASE_URL` in docker-compose.yml (service `app`) to your server's
hostname or IP so returned short URLs are correct.

## 3. Use it

Run the bundled smoke test:

```bash
./test.sh
```

Or manually:

```bash
# Create a short link
curl -s -X POST http://localhost/api/shorten \
  -H 'Content-Type: application/json' \
  -d '{"url":"https://www.redhat.com"}'

# Follow it (replace aB3xYz with your code)
curl -i http://localhost/aB3xYz

# View hit count
curl -s http://localhost/api/stats/aB3xYz
```

You can also open `http://<server-ip>/<code>` in a browser.

## 4. Verify persistence

```bash
docker compose down        # removes containers, KEEPS the volume
docker compose up -d
curl -i http://localhost/<code>    # still redirects
```

`docker compose down -v` deletes the volume and all stored links.

## 5. Useful commands

```bash
docker compose logs -f app                      # app logs
docker compose logs -f nginx                    # proxy logs
docker compose exec redis redis-cli keys '*'    # inspect stored keys
docker compose restart app                      # restart one service
docker compose down                             # stop everything
```

## 6. Troubleshooting

- **Not reachable from another machine:** check firewalld (`sudo firewall-cmd --list-all`).
- **Nginx permission denied on config:** SELinux label issue; re-run `compose up -d`, and check `sudo ausearch -m avc -ts recent`.
- **Port 80 in use:** `sudo ss -tlnp | grep :80`, or change the mapping to `8080:80`.
- **App can't reach Redis:** confirm `docker compose ps` shows redis healthy.

## API reference

| Method | Path | Description |
|--------|------|-------------|
| POST | /api/shorten | Body `{"url": "https://..."}`, returns code and short URL |
| GET | /{code} | 302 redirect to the original URL, increments hit counter |
| GET | /api/stats/{code} | Returns original URL and hit count |
| GET | /healthz | Health check (pings Redis) |
