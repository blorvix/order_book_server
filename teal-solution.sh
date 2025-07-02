#!/bin/bash

set -e

# Default values
TARGET_ORDINAL=10000
DEPTH=100

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --ob-id)
            TARGET_ORDINAL="$2"
            shift 2
            ;;
        --depth)
            DEPTH="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [--ob-id ORDINAL] [--depth DEPTH]"
            echo "  --ob-id ORDINAL    Target Order Book ordinal ID (default: 10000)"
            echo "  --depth DEPTH      Order Book depth (default: 100)"
            echo "  -h, --help         Show this help message"
            exit 0
            ;;
        *)
            # If no --ob-id is provided, treat the first argument as the ordinal
            if [[ "$TARGET_ORDINAL" == "10000" && "$1" =~ ^[0-9]+$ ]]; then
                TARGET_ORDINAL="$1"
            else
                echo "Unknown argument: $1"
                echo "Use -h or --help for usage information"
                exit 1
            fi
            shift
            ;;
    esac
done

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not installed"
    exit 1
fi

# Check if required packages are installed
python3 -c "import aiohttp, websockets" 2>/dev/null || {
    echo "Installing required Python packages..."
    pip3 install -r requirements.txt
}

# Check if server is running
if ! docker ps | grep -q teal-assignment-server; then
    echo "Warning: Order Book server is not running"
    echo "Please start the server first using: ./scripts/run-server.sh"
    echo "Or run with a custom delay: ./scripts/run-server.sh 1500"
fi

echo "Starting Order Book client with target ordinal: $TARGET_ORDINAL, depth: $DEPTH"

# Run the Python client
exec python3 order_book_client.py --ob-id "$TARGET_ORDINAL" --depth "$DEPTH" 