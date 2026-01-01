#!/bin/bash
# MBV Africa Project Management Script
# Usage: ./manage.sh [command]

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
DJANGO_DIR="$PROJECT_DIR/mbv_africa"

show_help() {
    echo "MBV Africa - Project Management"
    echo ""
    echo "Usage: ./manage.sh [command]"
    echo ""
    echo "Docker Commands:"
    echo "  start         Start all Docker services"
    echo "  stop          Stop all Docker services"
    echo "  restart       Restart all Docker services"
    echo "  logs          Show logs from all services"
    echo "  status        Show status of all services"
    echo "  clean         Stop and remove all containers and volumes"
    echo ""
    echo "Hive Commands:"
    echo "  ingest        Load data into Hive (requires healthy services)"
    echo "  hive-shell    Open Hive CLI in container"
    echo ""
    echo "Django Commands:"
    echo "  django        Run Django management command (e.g., ./manage.sh django migrate)"
    echo "  runserver     Start Django development server locally"
    echo "  load-data     Load sample data from CSV into SQLite"
    echo "  shell         Open Django shell"
    echo ""
    echo "Development:"
    echo "  setup         Initial project setup (install deps, migrate)"
    echo "  test          Run tests"
    echo ""
}

case "$1" in
    start)
        echo "Starting Docker services..."
        docker-compose up -d
        echo "Waiting for services to be healthy..."
        echo "Check status with: ./manage.sh status"
        ;;
    
    stop)
        echo "Stopping Docker services..."
        docker-compose down
        ;;
    
    restart)
        echo "Restarting Docker services..."
        docker-compose down
        docker-compose up -d
        ;;
    
    logs)
        docker-compose logs -f ${2:-}
        ;;
    
    status)
        docker-compose ps
        ;;
    
    clean)
        echo "Stopping and removing all containers and volumes..."
        docker-compose down -v --remove-orphans
        ;;
    
    ingest)
        ./ingest_data.sh
        ;;
    
    hive-shell)
        docker exec -it hive-server beeline -u jdbc:hive2://localhost:10000
        ;;
    
    django)
        shift
        cd "$DJANGO_DIR" && python manage.py "$@"
        ;;
    
    runserver)
        cd "$DJANGO_DIR" && python manage.py runserver ${2:-8000}
        ;;
    
    load-data)
        cd "$DJANGO_DIR" && python manage.py load_sample_data ${@:2}
        ;;
    
    shell)
        cd "$DJANGO_DIR" && python manage.py shell
        ;;
    
    setup)
        echo "Setting up project..."
        cd "$DJANGO_DIR"
        pip install -r requirements.txt
        python manage.py migrate
        echo "Setup complete!"
        ;;
    
    test)
        cd "$DJANGO_DIR" && python manage.py test ${@:2}
        ;;
    
    *)
        show_help
        ;;
esac
