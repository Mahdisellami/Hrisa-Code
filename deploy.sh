#!/bin/bash
# Deployment script for Hrisa Code Web UI with Docker

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Hrisa Code - Docker Deployment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}✗ Docker daemon is not running${NC}"
    echo "Please start Docker and try again"
    exit 1
fi

echo -e "${GREEN}✓ Docker daemon is running${NC}"
echo ""

# Parse command line arguments
COMMAND=${1:-"start"}

case $COMMAND in
    start)
        echo -e "${BLUE}[1/3] Building images...${NC}"
        docker-compose build web

        echo ""
        echo -e "${BLUE}[2/3] Starting services...${NC}"
        docker-compose up -d

        echo ""
        echo -e "${BLUE}[3/3] Waiting for services to be healthy...${NC}"
        sleep 5

        # Wait for services to be healthy
        MAX_WAIT=60
        WAITED=0
        while [ $WAITED -lt $MAX_WAIT ]; do
            if docker-compose ps | grep -q "healthy"; then
                echo -e "${GREEN}✓ Services are healthy${NC}"
                break
            fi
            echo -e "${YELLOW}Waiting for services... (${WAITED}s/${MAX_WAIT}s)${NC}"
            sleep 5
            WAITED=$((WAITED + 5))
        done

        echo ""
        echo -e "${GREEN}========================================${NC}"
        echo -e "${GREEN}  Deployment Complete!${NC}"
        echo -e "${GREEN}========================================${NC}"
        echo ""
        echo -e "Web UI: ${BLUE}http://localhost:8000${NC}"
        echo -e "API Docs: ${BLUE}http://localhost:8000/docs${NC}"
        echo ""
        echo "To view logs:"
        echo "  docker-compose logs -f web"
        echo ""
        echo "To stop services:"
        echo "  ./deploy.sh stop"
        echo ""
        ;;

    stop)
        echo -e "${BLUE}Stopping services...${NC}"
        docker-compose down
        echo -e "${GREEN}✓ Services stopped${NC}"
        ;;

    restart)
        echo -e "${BLUE}Restarting services...${NC}"
        docker-compose restart
        echo -e "${GREEN}✓ Services restarted${NC}"
        ;;

    logs)
        docker-compose logs -f web
        ;;

    status)
        echo -e "${BLUE}Service Status:${NC}"
        docker-compose ps
        echo ""
        echo -e "${BLUE}Available Models:${NC}"
        docker exec hrisa-ollama ollama list 2>/dev/null || echo "Ollama not ready yet"
        ;;

    pull-models)
        echo -e "${BLUE}Pulling recommended models...${NC}"
        echo "This may take several minutes depending on your connection."
        echo ""
        docker-compose --profile setup up ollama-pull
        echo ""
        echo -e "${GREEN}✓ Models pulled successfully${NC}"
        ;;

    verify)
        echo -e "${BLUE}Running verification checks...${NC}"
        docker-compose --profile verify run --rm verify
        echo ""
        echo -e "${GREEN}✓ Verification complete${NC}"
        ;;

    check)
        echo -e "${BLUE}Checking system requirements...${NC}"
        echo ""

        # Check Docker
        if command -v docker &> /dev/null; then
            echo -e "${GREEN}✓ Docker installed${NC}"
            docker --version
        else
            echo -e "${RED}✗ Docker not installed${NC}"
        fi

        # Check Docker Compose
        if command -v docker-compose &> /dev/null; then
            echo -e "${GREEN}✓ Docker Compose installed${NC}"
            docker-compose --version
        else
            echo -e "${RED}✗ Docker Compose not installed${NC}"
        fi

        # Check Docker daemon
        if docker info &> /dev/null; then
            echo -e "${GREEN}✓ Docker daemon running${NC}"
        else
            echo -e "${RED}✗ Docker daemon not running${NC}"
        fi

        echo ""
        echo -e "${BLUE}Checking services...${NC}"
        docker-compose ps

        echo ""
        echo -e "${BLUE}Checking models...${NC}"
        docker exec hrisa-ollama ollama list 2>/dev/null || echo -e "${YELLOW}⚠ Ollama not running or no models installed${NC}"

        echo ""
        echo -e "${BLUE}Running full verification...${NC}"
        docker-compose --profile verify run --rm verify 2>/dev/null || echo -e "${YELLOW}⚠ Verification service not available (services may not be running)${NC}"
        ;;

    clean)
        echo -e "${YELLOW}Warning: This will remove all containers and volumes!${NC}"
        read -p "Are you sure? (yes/no): " -r
        if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
            docker-compose down -v
            echo -e "${GREEN}✓ Cleaned up all resources${NC}"
        else
            echo "Cancelled"
        fi
        ;;

    update)
        echo -e "${BLUE}[1/3] Pulling latest code...${NC}"
        git pull

        echo ""
        echo -e "${BLUE}[2/3] Rebuilding images...${NC}"
        docker-compose build --no-cache web

        echo ""
        echo -e "${BLUE}[3/3] Restarting services...${NC}"
        docker-compose up -d

        echo ""
        echo -e "${GREEN}✓ Update complete${NC}"
        ;;

    backup)
        BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
        mkdir -p "$BACKUP_DIR"

        echo -e "${BLUE}Creating backup in ${BACKUP_DIR}...${NC}"

        # Backup volumes
        docker run --rm -v hrisa-code_ollama_data:/data -v $(pwd)/$BACKUP_DIR:/backup \
            ubuntu tar czf /backup/ollama.tar.gz /data 2>/dev/null

        docker run --rm -v hrisa-code_hrisa_config:/data -v $(pwd)/$BACKUP_DIR:/backup \
            ubuntu tar czf /backup/config.tar.gz /data 2>/dev/null

        docker run --rm -v hrisa-code_hrisa_history:/data -v $(pwd)/$BACKUP_DIR:/backup \
            ubuntu tar czf /backup/history.tar.gz /data 2>/dev/null

        echo -e "${GREEN}✓ Backup completed: ${BACKUP_DIR}${NC}"
        ;;

    help)
        echo "Usage: ./deploy.sh [command]"
        echo ""
        echo "Commands:"
        echo "  start         Start all services (default)"
        echo "  stop          Stop all services"
        echo "  restart       Restart all services"
        echo "  logs          View web service logs"
        echo "  status        Show service status"
        echo "  check         Check system requirements and run verification"
        echo "  verify        Run verification checks in container"
        echo "  pull-models   Pull recommended Ollama models"
        echo "  clean         Remove all containers and volumes"
        echo "  update        Pull latest code and rebuild"
        echo "  backup        Backup volumes"
        echo "  help          Show this help message"
        echo ""
        ;;

    *)
        echo -e "${RED}Unknown command: $COMMAND${NC}"
        echo "Run './deploy.sh help' for usage information"
        exit 1
        ;;
esac
