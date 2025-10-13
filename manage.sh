#!/bin/bash

PROJECT_DIR="$HOME/music-monitor"
cd "$PROJECT_DIR" 2>/dev/null || { echo "Error: Project not found at $PROJECT_DIR"; exit 1; }

case "$1" in
    start)
        echo "🚀 Starting music monitor system..."
        docker-compose up -d
        echo "✅ Monitor started"
        ;;
    stop)
        echo "🛑 Stopping monitor..."
        docker-compose down
        echo "✅ Monitor stopped"
        ;;
    restart)
        echo "🔄 Restarting monitor..."
        docker-compose restart
        echo "✅ Monitor restarted"
        ;;
    status)
        echo "📊 Monitor Status:"
        docker-compose ps
        echo ""
        echo "Recent activity:"
        docker-compose logs --tail=20
        ;;
    logs)
        if [ "$2" == "-f" ]; then
            echo "📜 Following logs (Ctrl+C to exit)..."
            docker-compose logs -f
        else
            echo "📜 Recent logs:"
            docker-compose logs --tail=50
        fi
        ;;
    update)
        echo "🔄 Updating monitor..."
        docker-compose pull
        docker-compose up -d --build
        echo "✅ Monitor updated"
        ;;
    config)
        echo "⚙️  Opening config file..."
        nano config/config.json
        echo "Restart monitor to apply changes: ./manage.sh restart"
        ;;
    artists)
        echo "🎤 Currently monitored artists:"
        cat config/config.json | grep -A 20 '"bandsintown_artists"' | grep '"' | sed 's/.*"\(.*\)".*/  - \1/'
        ;;
    add-artist)
        if [ -z "$2" ]; then
            echo "Usage: $0 add-artist \"Artist Name\""
            exit 1
        fi
        echo "Adding artist: $2"
        # This is a simple approach - for production, use jq
        echo "Please edit config/config.json manually and add: \"$2\""
        echo "Then restart: ./manage.sh restart"
        ;;
    *)
        echo "🎵 Music Monitor System - Management Script"
        echo ""
        echo "Usage: $0 {start|stop|restart|status|logs|update|config|artists|add-artist}"
        echo ""
        echo "Commands:"
        echo "  start           - Start the monitor"
        echo "  stop            - Stop the monitor"
        echo "  restart         - Restart the monitor"
        echo "  status          - Show monitor status and recent activity"
        echo "  logs            - Show recent logs (use -f to follow)"
        echo "  update          - Update and rebuild the monitor"
        echo "  config          - Edit configuration file"
        echo "  artists         - List monitored artists"
        echo "  add-artist NAME - Add an artist to monitor"
        exit 1
        ;;
esac
