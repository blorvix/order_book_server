#!/bin/bash

set -e

TARGET_ORDINAL=${1:-10000}

echo "**VALIDATING SERVER WITH TARGET ORDINAL: $TARGET_ORDINAL**"

if ! docker info > /dev/null 2>&1; then
    echo "**ERROR: Docker is not running**"
    exit 1
fi

# Check if server is running
if ! docker ps | grep -q teal-assignment-server; then
    echo "**ERROR: Server container 'teal-assignment-server' is not running**"
    echo "**Run run-server.sh first**"
    exit 1
fi

EXIT_STATUS=0
docker run --rm \
    -v "$(pwd)/server:/app" \
    --workdir /app \
    --network host \
    openjdk:21-jdk-slim \
    java -cp server.jar co.goteal.interviewtester.SolutionImpl1Kt "$TARGET_ORDINAL" || EXIT_STATUS=$?

echo "**CONTAINER EXIT STATUS: $EXIT_STATUS**"

ASSERTION_RESPONSE=$(curl -s http://localhost:9090/assertion 2>/dev/null || echo "ERROR: Could not connect to server")

if [ "$ASSERTION_RESPONSE" = "ERROR: Could not connect to server" ]; then
    echo "**ERROR: Could not fetch assertion from server**"
    echo "**Make sure the server is running on localhost:9090**"
else
    echo "**ASSERTION RESULT:**"
    echo "$ASSERTION_RESPONSE" | jq . 2>/dev/null || echo "$ASSERTION_RESPONSE"
fi

if [ $EXIT_STATUS -eq 0 ]; then
    echo "**VALIDATION COMPLETED SUCCESSFULLY**"
else
    echo "**VALIDATION FAILED WITH EXIT STATUS: $EXIT_STATUS**"
fi

exit $EXIT_STATUS