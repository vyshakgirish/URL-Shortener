
# Containerized URL Shortener

A lightweight URL shortening application deployed using Podman
and Compose on Red Hat Enterprise Linux (RHEL).

The application uses Flask for backend logic, Redis for persistent
URL storage, and Nginx as a reverse proxy. A simple web interface
allows users to generate, access and copy shortened URLs.

## Features

- Shortens long URLs into six-character links.
- Provides a browser-based interface for URL shortening.
- Redirects shortened links to their original URLs.
- Stores URL mappings persistently using Redis.
- Deploys three interconnected containers using Compose.
- Uses a custom bridge network for internal communication.
- Supports deployment with rootless Podman.

## Technologies Used

| Technology | Purpose |
|------------|---------|
| RHEL | Linux deployment environment |
| Podman | Container engine |
| Podman Compose | Multi-container orchestration |
| Python / Flask | Backend application and API |
| Gunicorn | WSGI application server |
| Redis | URL mapping and persistent data storage |
| Nginx | Reverse proxy |
| HTML, CSS, JavaScript | Web interface |
| Git and GitHub | Source code management |

## System Architecture

```text
             Web Browser
                  |
          localhost:8080
                  |
                  v
          +---------------+
          |     Nginx     |
          |    Port 80    |
          +-------+-------+
                  |
                  v
          +---------------+
          | Flask/Gunicorn|
          |   Port 8000   |
          +-------+-------+
                  |
                  v
          +---------------+
          |     Redis     |
          |   Port 6379   |
          +-------+-------+
                  |
                  v
          +---------------+
          |  redis-data   |
          |    Volume     |
          +---------------+
```

All three containers communicate through a custom bridge network
named `shortener-net`.

Nginx is the only container with a published host port.
The Flask and Redis services communicate internally using their
service names.

## Project Structure

```text
URL-Shortener/
├── README.md
├── app/
│   ├── Dockerfile
│   ├── app.py
│   ├── requirements.txt
│   └── templates/
│       └── index.html
├── docker-compose.yml
├── nginx/
│   └── nginx.conf
└── test.sh
```

## Prerequisites

The following tools are required on the RHEL system:

- Git
- Podman
- Podman Compose
- Internet access for downloading container images and Python packages

Verify the installation:

```bash
git --version
podman --version
podman-compose --version
```

If the required tools are not installed:

```bash
sudo dnf install -y git podman
sudo dnf install -y podman-compose
```

Depending on the RHEL version and available repositories,
Podman Compose may require an additional repository such as EPEL.

## Installation and Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/prithvi-s1/URL-Shortener.git
cd URL-Shortener
```

### 2. Build and Start the Containers

```bash
podman-compose up -d --build
```

This command:

- Builds the Flask application image using its Dockerfile.
- Pulls the Redis and Nginx images if required.
- Creates the custom container network.
- Creates the persistent Redis volume if it does not exist.
- Starts the three application containers.

### 3. Verify the Deployment

```bash
podman ps
```

All three containers should be running.

Additional verification commands:

```bash
podman images
podman network ls
podman volume ls
podman-compose ps
```

### 4. Access the Application

Open the following address in a browser on the RHEL system:

```text
http://localhost:8080
```

The web interface allows users to:

1. Enter a valid HTTP or HTTPS URL.
2. Click the Shorten URL button.
3. Access the generated shortened URL.
4. Copy the shortened URL using the Copy Link button.

The shortened link redirects the user to the original website.

## Application Workflow

1. The user enters a long URL in the web interface.
2. JavaScript sends a POST request to `/api/shorten`.
3. Nginx forwards the request to the Flask application.
4. Flask validates the URL and generates a random six-character code.
5. Redis stores the code and original URL as a key-value pair.
6. Flask returns the shortened URL to the browser.
7. When the shortened URL is accessed, Flask retrieves the original
   URL from Redis and returns an HTTP 302 redirect.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Displays the web interface |
| POST | `/api/shorten` | Generates a shortened URL |
| GET | `/{code}` | Redirects to the original URL |
| GET | `/healthz` | Checks connectivity to Redis |
| GET | `/api/stats/{code}` | Returns URL information and hit count |

The statistics endpoint is retained in the backend but is not
displayed in the web interface.

### Example API Request

```bash
curl -X POST http://localhost:8080/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"url":"https://www.redhat.com"}'
```

Example response:

```json
{
  "code": "aB3xYz",
  "short_url": "http://localhost:8080/aB3xYz",
  "url": "https://www.redhat.com"
}
```

The generated code will differ for each request.

### Test Redirection

Replace `aB3xYz` with the generated code:

```bash
curl -i http://localhost:8080/aB3xYz
```

The response should contain an HTTP 302 status and a Location
header pointing to the original URL.

### Health Check

```bash
curl http://localhost:8080/healthz
```

Expected response:

```json
{"status":"ok"}
```

### Run the Test Script

The repository includes a shell script for basic API testing.

```bash
bash test.sh http://localhost:8080
```

The script checks Redis connectivity, generates a shortened link,
tests redirection and retrieves the hit count.

## Persistent Storage

Redis uses a named volume called `redis-data`, mounted at `/data`.

Append-only file persistence is enabled using:

```text
redis-server --appendonly yes
```

To verify persistence:

1. Generate a shortened URL and save it.
2. Remove the application containers:

```bash
podman-compose down
```

3. Verify that the Redis volume still exists:

```bash
podman volume ls
```

4. Recreate the containers:

```bash
podman-compose up -d
```

5. Access the previously generated shortened URL.

The link should continue to work because its data is stored in
the persistent Redis volume.

Warning: Running `podman-compose down -v` removes the named
volume and deletes the stored URL mappings.

## Container Networking

The project uses a custom bridge network named `shortener-net`.

Internal communication:

| Source | Destination | Address |
|--------|-------------|---------|
| Browser | Nginx | localhost:8080 |
| Nginx | Flask | app:8000 |
| Flask | Redis | redis:6379 |

Only Nginx publishes a port to the host.

The port mapping `8080:80` allows rootless Podman to expose
the application without requiring privileged port access under
the usual Linux configuration.

## SELinux Compatibility

The Nginx configuration file is mounted using:

```yaml
volumes:
  - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro,Z
```

The `ro` option makes the configuration read-only inside the
container.

The `Z` option applies a private SELinux label so that the
container can access the mounted configuration file.

SELinux can remain in enforcing mode during deployment.

## Updating the Application

After making changes to the source code on GitHub:

```bash
git pull
podman-compose down
podman-compose up -d --build
```

The updated application image is built and deployed while the
existing Redis volume is preserved.

## Useful Commands

| Command | Purpose |
|---------|---------|
| `podman ps` | List running containers |
| `podman ps -a` | List all containers |
| `podman images` | List available images |
| `podman network ls` | List container networks |
| `podman volume ls` | List persistent volumes |
| `podman-compose logs app` | View application logs |
| `podman-compose logs nginx` | View reverse proxy logs |
| `podman-compose logs redis` | View Redis logs |
| `podman-compose restart` | Restart the services |
| `podman-compose down` | Stop and remove the containers |

## Troubleshooting

### Application Not Accessible

Verify that all containers are running:

```bash
podman ps
```

Check whether port 8080 is already in use:

```bash
ss -tln | grep :8080
```

### Container Build Failure

Check the build output:

```bash
podman-compose build
```

Ensure that the system has access to the container registry
and Python package repository.

### Application or Proxy Errors

Inspect the relevant container logs:

```bash
podman-compose logs app
podman-compose logs nginx
podman-compose logs redis
```

### Access from Another Machine

When accessing the application remotely, update `BASE_URL`
in `docker-compose.yml` to the RHEL system's reachable IP
address or hostname, including port 8080.

For example:

```yaml
BASE_URL: http://192.168.1.100:8080
```

If required, allow TCP port 8080 through the RHEL firewall:

```bash
sudo firewall-cmd --permanent --add-port=8080/tcp
sudo firewall-cmd --reload
```

Recreate the containers after changing the configuration.

## Limitations and Future Enhancements

The current application is intended for educational and
development purposes.

Possible enhancements include:

- HTTPS support.
- Custom shortened URL aliases.
- Automatic link expiration.
- User authentication.
- Rate limiting.
- Automated build and deployment using CI/CD.

## Project Objective

This project demonstrates the deployment of a multi-container
application on Red Hat Enterprise Linux using Podman.

The main concepts implemented are container image creation,
multi-container orchestration, container networking, reverse
proxying, persistent storage and SELinux-compatible deployment.

Developed as part of the Linux and Container Technologies course.
