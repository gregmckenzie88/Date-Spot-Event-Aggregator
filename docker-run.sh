#!/bin/bash

# DateSpot Aggregator Docker Runner Script
# This script provides easy commands to manage the Docker containers

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker Desktop."
        exit 1
    fi
}

# Function to check if .env file exists
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error ".env file not found!"
        echo ""
        print_status "To create your .env file:"
        echo "1. Copy the example file:"
        echo "   cp env.example .env"
        echo ""
        echo "2. Edit .env with your actual API keys:"
        echo "   - Google Maps API key"
        echo "   - Weather API key" 
        echo "   - Anthropic API key"
        echo "   - GitHub token"
        echo ""
        print_warning "The application cannot run without proper API keys in .env file."
        exit 1
    fi
}

# Function to show usage
show_usage() {
    echo "DateSpot Aggregator Docker Management"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  setup         Create .env file from example (first time setup)"
    echo "  build         Build the Docker image"
    echo "  run           Run the aggregator once and exit"
    echo "  schedule      Start the scheduler (runs daily at 2 AM)"
    echo "  stop          Stop all running containers"
    echo "  logs          Show logs from the aggregator"
    echo "  shell         Open a shell in the container"
    echo "  clean         Remove containers and images"
    echo "  status        Show status of containers"
    echo ""
    echo "Examples:"
    echo "  $0 setup         # First time setup"
    echo "  $0 build         # Build the image"
    echo "  $0 run           # Run once"
    echo "  $0 schedule      # Start scheduler"
    echo "  $0 logs          # View logs"
}

# Setup environment file
setup_env() {
    if [ -f ".env" ]; then
        print_warning ".env file already exists!"
        read -p "Do you want to overwrite it? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_status "Setup cancelled."
            return
        fi
    fi
    
    if [ ! -f "env.example" ]; then
        print_error "env.example file not found!"
        exit 1
    fi
    
    print_status "Creating .env file from env.example..."
    cp env.example .env
    print_success ".env file created!"
    echo ""
    print_warning "IMPORTANT: Edit the .env file with your actual API keys:"
    echo "  - Google Maps API key"
    echo "  - Weather API key"
    echo "  - Anthropic API key" 
    echo "  - GitHub token"
    echo ""
    print_status "You can edit it with: nano .env"
    echo ""
    print_warning "The .env file is ignored by git and will not be committed."
}

# Build the Docker image
build_image() {
    print_status "Building DateSpot Aggregator Docker image..."
    check_env_file
    docker-compose build
    print_success "Docker image built successfully!"
}

# Run the aggregator once
run_once() {
    print_status "Running DateSpot Aggregator (one-time execution)..."
    check_env_file
    docker-compose up --remove-orphans datespot-aggregator
    print_success "Aggregator execution completed!"
}

# Start the scheduler
start_scheduler() {
    print_status "Starting DateSpot Aggregator Scheduler..."
    check_env_file
    docker-compose --profile scheduler up -d datespot-scheduler
    print_success "Scheduler started! It will run daily at 2 AM."
    print_status "Use '$0 logs' to view scheduler logs."
}

# Stop all containers
stop_containers() {
    print_status "Stopping all DateSpot Aggregator containers..."
    docker-compose --profile scheduler down
    print_success "All containers stopped!"
}

# Show logs
show_logs() {
    print_status "Showing DateSpot Aggregator logs..."
    if docker-compose ps | grep -q "datespot-scheduler"; then
        docker-compose --profile scheduler logs -f datespot-scheduler
    elif docker-compose ps | grep -q "datespot-aggregator"; then
        docker-compose logs -f datespot-aggregator
    else
        print_warning "No running containers found. Recent logs:"
        docker-compose --profile scheduler logs --tail=50 datespot-scheduler 2>/dev/null || \
        docker-compose logs --tail=50 datespot-aggregator 2>/dev/null || \
        print_warning "No logs available."
    fi
}

# Open shell in container
open_shell() {
    print_status "Opening shell in DateSpot Aggregator container..."
    if docker-compose ps | grep -q "datespot-scheduler.*Up"; then
        docker-compose --profile scheduler exec datespot-scheduler /bin/bash
    else
        print_status "Starting temporary container for shell access..."
        docker-compose run --rm datespot-aggregator /bin/bash
    fi
}

# Clean up containers and images
clean_up() {
    print_warning "This will remove all DateSpot Aggregator containers and images."
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_status "Cleaning up containers and images..."
        docker-compose --profile scheduler down --rmi all --volumes --remove-orphans
        print_success "Cleanup completed!"
    else
        print_status "Cleanup cancelled."
    fi
}

# Show container status
show_status() {
    print_status "DateSpot Aggregator Container Status:"
    echo ""
    docker-compose --profile scheduler ps
    echo ""
    print_status "Docker images:"
    docker images | grep -E "(datespot|REPOSITORY)" || print_warning "No DateSpot images found."
}

# Main script logic
case "${1:-}" in
    setup)
        setup_env
        ;;
    build)
        check_docker
        build_image
        ;;
    run)
        check_docker
        run_once
        ;;
    schedule)
        check_docker
        start_scheduler
        ;;
    stop)
        check_docker
        stop_containers
        ;;
    logs)
        check_docker
        show_logs
        ;;
    shell)
        check_docker
        open_shell
        ;;
    clean)
        check_docker
        clean_up
        ;;
    status)
        check_docker
        show_status
        ;;
    help|--help|-h)
        show_usage
        ;;
    "")
        print_error "No command specified."
        echo ""
        show_usage
        exit 1
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_usage
        exit 1
        ;;
esac
