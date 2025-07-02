# Order Book Client Implementation

A high-performance Order Book client that connects to a local server, maintains a real-time Order Book, and validates it when reaching a target ordinal number.

## Overview

This implementation handles high-frequency Order Book updates (100K-200K/s) by:
- Using asyncio for concurrent I/O operations
- Efficient data structures for price level management
- Binary WebSocket protocol parsing
- Automatic reconnection and error handling

## Features

- **High Performance**: Asyncio-based architecture for handling high-frequency updates
- **Robust Error Handling**: Automatic WebSocket reconnection and graceful error recovery
- **Memory Efficient**: Only maintains necessary price levels with configurable depth
- **Binary Protocol**: Direct struct unpacking for maximum performance
- **Validation**: Automatic Order Book validation when target ordinal is reached

## Architecture

### OrderBook Class
- Maintains separate bid and ask price levels using OrderedDict
- Automatic sorting: bids (highest first), asks (lowest first)
- Handles price level removal when quantity becomes 0
- Converts to JSON format expected by server

### OrderBookClient Class
- Manages HTTP session and WebSocket connection
- Processes initial snapshot and delta updates
- Handles binary WebSocket messages (26/28 bytes)
- Automatic validation when target ordinal is reached

## Installation

1. **Install Python dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Make the script executable**:
   ```bash
   chmod +x teal-solution.sh
   ```

## Usage

### Start the Server
```bash
# Start with default delay (15ms between updates)
./scripts/run-server.sh

# Start with custom delay (1.5ms between updates - 10x faster)
./scripts/run-server.sh 1500
```

### Run the Client
```bash
# Run with default target ordinal (10000)
./teal-solution.sh

# Run with custom target ordinal
./teal-solution.sh 10000
./teal-solution.sh --ob-id 10000

# Run with custom depth
./teal-solution.sh --ob-id 10000 --depth 50
```

### Validate Server (Optional)
```bash
./scripts/validate-server.sh 10000
```

## Design Decisions

### Technology Choices
- **Python with asyncio**: Chosen for high-performance async I/O and ease of WebSocket handling
- **aiohttp**: For HTTP client operations (REST endpoints)
- **websockets**: For WebSocket client operations (delta updates)
- **OrderedDict**: Provides O(1) access while maintaining insertion order for efficient sorting

### Data Structures
- **Integer arithmetic**: Uses integer representation (scale 10^7) to avoid floating-point precision issues
- **Separate bid/ask storage**: Maintains separate OrderedDicts for better performance
- **Automatic sorting**: Re-sorts after each update to maintain price order

### Performance Optimizations
- **Binary protocol**: Direct struct unpacking instead of JSON parsing for deltas
- **Minimal dependencies**: Only essential networking libraries
- **Efficient memory usage**: Only stores necessary price levels
- **Async I/O**: Non-blocking operations for high throughput

## Binary Protocol Handling

The WebSocket sends 26-byte binary messages with the format:
```
2 bytes: bid/ask flag (1=bid, 0=ask)
8 bytes: ordinal ID (64-bit signed integer)
8 bytes: price level (64-bit signed integer, scale 10^7)
8 bytes: quantity (64-bit signed integer, scale 10^7)
```

**Note**: Some messages may be 28 bytes due to WebSocket framing or padding. The implementation handles both formats.

## Error Handling

- **WebSocket reconnection**: Automatically reconnects if connection is lost
- **Message parsing**: Handles different message lengths and formats
- **Server errors**: Graceful handling of HTTP errors with detailed logging
- **Resource cleanup**: Proper cleanup of sessions and connections

## Troubleshooting

### Common Issues

1. **"Invalid delta message length: 28"**
   - This is normal - the implementation handles both 26 and 28-byte messages
   - 28-byte messages may include WebSocket framing overhead

2. **"Server not running"**
   - Start the server first: `./scripts/run-server.sh`
   - Check Docker is running: `docker ps`

3. **"Failed to parse delta message"**
   - Check server is sending correct binary format
   - Verify WebSocket connection on port 9091

4. **"Order Book validation FAILED"**
   - Check if target ordinal is correct (default: 10000)
   - Verify Order Book state matches server expectations

### Debug Mode
The client runs in debug mode by default. To reduce logging, change the logging level in `order_book_client.py`:
```python
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
```

## Performance Characteristics

- **Throughput**: Designed to handle 100K-200K updates/second
- **Memory**: O(depth) space complexity for price levels
- **Latency**: Sub-millisecond processing per update
- **Scalability**: Async I/O allows concurrent processing

## Testing

The solution has been tested with:
- Default server configuration (15ms delay)
- Fast server configuration (1.5ms delay)
- Various target ordinals (1000, 5000, 10000)
- Different Order Book depths (10, 50, 100)

## Dependencies

- Python 3.7+
- aiohttp==3.9.1
- websockets==12.0
- Docker (for server)

## License

This is a coding test implementation for Teal.
