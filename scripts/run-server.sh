#!/bin/bash

set -e

# Configuration
DELAY_MICRO=${1:-15000}  # Default to 15000μs if not provided

echo "**STARTING SERVER**"
echo "Using delay: ${DELAY_MICRO}μs"

if ! docker info > /dev/null 2>&1; then
    echo "**ERROR: Docker is not running**"
    exit 1
fi

# Stop and remove existing container if running
echo "Stopping existing container if running..."
docker stop teal-assignment-server 2>/dev/null || true
docker rm teal-assignment-server 2>/dev/null || true

# Run server using single Docker command with volume mount
echo "Starting server container..."
docker run -d \
    -p 9090:9090 \
    -p 9091:9091 \
    -v "$(pwd)/server:/app" \
    --name teal-assignment-server \
    --workdir /app \
    openjdk:21-jdk-slim \
    java \
    --add-exports=java.base/jdk.internal.ref=ALL-UNNAMED \
    --add-exports=java.base/sun.nio.ch=ALL-UNNAMED \
    --add-exports=jdk.unsupported/sun.misc=ALL-UNNAMED \
    --add-opens=java.base/java.lang=ALL-UNNAMED \
    --add-opens=java.base/java.lang.reflect=ALL-UNNAMED \
    --add-opens=java.base/java.io=ALL-UNNAMED \
    --add-opens=java.base/java.util=ALL-UNNAMED \
    -jar server.jar \
    ./data/orderbook_10K.cq4 ${DELAY_MICRO}

sleep 3

if docker ps | grep -q teal-assignment-server; then
    echo "**SERVER STARTED SUCCESSFULLY**"
else
    echo "**ERROR: Failed to start server container**"
    exit 1
fi