# DateSpot Aggregator - Docker Guide

This guide explains how to run the DateSpot Aggregator using Docker Desktop.

## Prerequisites

1. **Docker Desktop** installed and running
2. **Git** (to clone the repository)

## Quick Start

### 1. First-Time Setup

```bash
# Create environment file with your API keys
./docker-run.sh setup

# Edit the .env file with your actual API keys
nano .env
```

### 2. Build the Docker Image

```bash
./docker-run.sh build
```

### 3. Run Once (Manual Execution)

```bash
./docker-run.sh run
```

### 4. Start Scheduled Runner (Automatic Daily Runs)

```bash
./docker-run.sh schedule
```

## Available Commands

| Command | Description |
|---------|-------------|
| `./docker-run.sh setup` | Create .env file from example (first time setup) |
| `./docker-run.sh build` | Build the Docker image |
| `./docker-run.sh run` | Run the aggregator once and exit |
| `./docker-run.sh schedule` | Start the scheduler (runs daily at 2 AM) |
| `./docker-run.sh stop` | Stop all running containers |
| `./docker-run.sh logs` | Show logs from the aggregator |
| `./docker-run.sh shell` | Open a shell in the container |
| `./docker-run.sh clean` | Remove containers and images |
| `./docker-run.sh status` | Show status of containers |

## Configuration

### Environment Variables Required

All API keys must be provided via environment variables. The application will not run without them.

### Setting Up API Keys

1. Create your `.env` file:
   ```bash
   ./docker-run.sh setup
   ```

2. Edit `.env` with your actual API keys:
   ```bash
   nano .env
   ```

3. Required values:
   ```bash
   # Google Maps Geocoding API Key
   GOOGLE_MAPS_API_KEY=your_actual_google_maps_key
   
   # Visual Crossing Weather API Key  
   WEATHER_API_KEY=your_actual_weather_key
   
   # Anthropic Claude AI API Key
   ANTHROPIC_API_KEY=your_actual_anthropic_key
   
   # GitHub Personal Access Token
   GITHUB_TOKEN=your_actual_github_token
   ```

### Security Note

- The `.env` file is automatically excluded from git commits
- Never commit API keys to version control
- Each user must create their own `.env` file

## Docker Compose Services

### datespot-aggregator
- **Purpose**: One-time execution of the workflow
- **Usage**: `./docker-run.sh run`

### datespot-scheduler
- **Purpose**: Automatic daily execution at 2 AM
- **Usage**: `./docker-run.sh schedule`

## File Structure

```
datespot-aggregator/
├── Dockerfile              # Container definition
├── docker-compose.yml      # Service orchestration
├── docker-run.sh          # Management script
├── scheduler.py            # Scheduled execution
├── .dockerignore          # Files to exclude from build
└── DOCKER_README.md       # This file
```

## Usage Examples

### Daily Automation
```bash
# Build and start the scheduler
./docker-run.sh build
./docker-run.sh schedule

# Check that it's running
./docker-run.sh status

# View logs
./docker-run.sh logs
```

### Manual Runs
```bash
# Build the image
./docker-run.sh build

# Run once
./docker-run.sh run

# View logs from the run
./docker-run.sh logs
```

### Development/Debugging
```bash
# Open a shell in the container
./docker-run.sh shell

# View real-time logs
./docker-run.sh logs

# Check container status
./docker-run.sh status
```

## Logs

Logs are automatically captured and can be viewed with:
```bash
./docker-run.sh logs
```

The enhanced logging now shows:
- **Step-by-step progress** (🔵 STEP X/8)
- **Detailed timing** for each step
- **Success/failure indicators** (✅/❌/⚠️)
- **Data flow statistics** at each stage
- **Sub-step progress** with emojis and timestamps

For persistent logs, the containers mount a `./logs` directory.

## Networking

The containers use a dedicated Docker network (`datespot-network`) for isolation and security.

## Security Features

- **Non-root user**: Containers run as a dedicated `datespot` user
- **Environment variables**: API keys are passed securely via environment
- **Network isolation**: Containers use a dedicated network
- **Minimal base image**: Uses Python slim image for reduced attack surface

## Troubleshooting

### Container won't start
```bash
# Check Docker Desktop is running
docker info

# Check container status
./docker-run.sh status

# View logs for errors
./docker-run.sh logs
```

### API key issues
```bash
# Open shell and check environment
./docker-run.sh shell
env | grep -E "(GOOGLE|WEATHER|ANTHROPIC|GITHUB)"
```

### Rebuild after changes
```bash
# Stop and clean
./docker-run.sh stop
./docker-run.sh clean

# Rebuild
./docker-run.sh build
```

## Stopping Services

### Stop all containers
```bash
./docker-run.sh stop
```

### Complete cleanup (removes images too)
```bash
./docker-run.sh clean
```

## Integration with Docker Desktop

- View containers in Docker Desktop GUI
- Monitor resource usage
- Access logs through the interface
- Start/stop containers from the GUI

The containers will appear as:
- `datespot-aggregator` (for one-time runs)
- `datespot-scheduler` (for scheduled runs)
