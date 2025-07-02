#!/usr/bin/env python3
"""
Order Book Client Implementation

This client connects to the Order Book server, maintains a local Order Book,
and validates it when reaching the target ordinal number.
"""

import asyncio
import json
import struct
import sys
import argparse
from typing import Dict, List, Tuple, Optional
from collections import OrderedDict
import aiohttp
import websockets
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class OrderBook:
    """Maintains an Order Book with bids and asks sorted by price."""
    
    def __init__(self, depth: int = 100):
        self.depth = depth
        # Use OrderedDict for O(1) access and insertion order
        self.bids: OrderedDict[int, int] = OrderedDict()  # price -> quantity
        self.asks: OrderedDict[int, int] = OrderedDict()  # price -> quantity
        self.last_update_id: int = 0
        
    def update_bid(self, price: int, quantity: int):
        """Update bid price level."""
        if quantity == 0:
            self.bids.pop(price, None)
        else:
            self.bids[price] = quantity
            # Re-sort bids (highest price first)
            self._sort_bids()
            
    def update_ask(self, price: int, quantity: int):
        """Update ask price level."""
        if quantity == 0:
            self.asks.pop(price, None)
        else:
            self.asks[price] = quantity
            # Re-sort asks (lowest price first)
            self._sort_asks()
    
    def _sort_bids(self):
        """Sort bids in descending order (highest price first)."""
        sorted_bids = sorted(self.bids.items(), key=lambda x: x[0], reverse=True)
        self.bids = OrderedDict(sorted_bids)
        
    def _sort_asks(self):
        """Sort asks in ascending order (lowest price first)."""
        sorted_asks = sorted(self.asks.items(), key=lambda x: x[0])
        self.asks = OrderedDict(sorted_asks)
    
    def to_json(self) -> dict:
        """Convert Order Book to JSON format expected by server."""
        # Convert price and quantity from integers to decimal strings with scale 7
        def format_decimal(value: int) -> str:
            return f"{value / 10_000_000:.7f}"
        
        bids = [[format_decimal(price), format_decimal(qty)] 
                for price, qty in list(self.bids.items())[:self.depth]]
        asks = [[format_decimal(price), format_decimal(qty)] 
                for price, qty in list(self.asks.items())[:self.depth]]
        
        return {
            "lastUpdateId": self.last_update_id,
            "bids": bids,
            "asks": asks
        }
    
    def get_size(self) -> Tuple[int, int]:
        """Get current number of bid and ask levels."""
        return len(self.bids), len(self.asks)

class OrderBookClient:
    """Client that connects to Order Book server and maintains local Order Book."""
    
    def __init__(self, target_ordinal: int, depth: int = 100):
        self.target_ordinal = target_ordinal
        self.order_book = OrderBook(depth)
        self.session: Optional[aiohttp.ClientSession] = None
        self.websocket: Optional[websockets.WebSocketServerProtocol] = None
        self.running = False
        
    async def start(self):
        """Start the Order Book client."""
        logger.info(f"Starting Order Book client with target ordinal: {self.target_ordinal}")
        
        self.session = aiohttp.ClientSession()
        
        try:
            # Start the server
            await self._start_server()
            
            # Get initial snapshot
            await self._get_snapshot()
            
            # Connect to WebSocket for delta updates
            await self._connect_websocket()
            
        except Exception as e:
            logger.error(f"Error starting client: {e}")
            await self.cleanup()
            raise
    
    async def _start_server(self):
        """Start the Order Book server."""
        logger.info("Starting Order Book server...")
        async with self.session.post("http://localhost:9090/start") as response:
            if response.status != 200:
                raise Exception(f"Failed to start server: {response.status}")
        logger.info("Server started successfully")
    
    async def _get_snapshot(self):
        """Get initial Order Book snapshot."""
        logger.info("Getting initial Order Book snapshot...")
        async with self.session.get("http://localhost:9090/snapshot?depth=100") as response:
            if response.status != 200:
                raise Exception(f"Failed to get snapshot: {response.status}")
            
            data = await response.json()
            await self._process_snapshot(data)
    
    async def _process_snapshot(self, snapshot: dict):
        """Process snapshot data and initialize Order Book."""
        self.order_book.last_update_id = snapshot["lastUpdateId"]
        
        # Clear existing data
        self.order_book.bids.clear()
        self.order_book.asks.clear()
        
        # Process bids
        for bid in snapshot["bids"]:
            price = int(float(bid[0]) * 10_000_000)  # Convert to integer scale
            quantity = int(float(bid[1]) * 10_000_000)
            self.order_book.bids[price] = quantity
        
        # Process asks
        for ask in snapshot["asks"]:
            price = int(float(ask[0]) * 10_000_000)  # Convert to integer scale
            quantity = int(float(ask[1]) * 10_000_000)
            self.order_book.asks[price] = quantity
        
        # Sort the Order Book
        self.order_book._sort_bids()
        self.order_book._sort_asks()
        
        bid_count, ask_count = self.order_book.get_size()
        logger.info(f"Snapshot processed: {bid_count} bids, {ask_count} asks, lastUpdateId: {self.order_book.last_update_id}")
    
    async def _connect_websocket(self):
        """Connect to WebSocket for delta updates."""
        logger.info("Connecting to WebSocket for delta updates...")
        
        self.running = True
        while self.running:
            try:
                async with websockets.connect("ws://localhost:9091/delta") as websocket:
                    self.websocket = websocket
                    logger.info("WebSocket connected successfully")
                    
                    async for message in websocket:
                        if not self.running:
                            break
                        await self._process_delta(message)
                        
            except websockets.exceptions.ConnectionClosed:
                logger.warning("WebSocket connection closed, attempting to reconnect...")
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                if self.running:
                    await asyncio.sleep(1)
    
    async def _process_delta(self, message: bytes):
        """Process delta update from WebSocket."""
        if len(message) != 26:
            logger.warning(f"Invalid delta message length: {len(message)}")
            return
        
        try:
            # Parse binary message: 2 bytes (bid/ask) + 8 bytes (ordinal) + 8 bytes (price) + 8 bytes (quantity)
            is_bid, ordinal_id, price, quantity = struct.unpack('>HQQQ', message)
            
            # Update Order Book
            if is_bid == 1:
                self.order_book.update_bid(price, quantity)
            else:
                self.order_book.update_ask(price, quantity)
            
            self.order_book.last_update_id = ordinal_id
            
            # Log progress every 1000 updates
            if ordinal_id % 1000 == 0:
                bid_count, ask_count = self.order_book.get_size()
                logger.info(f"Update {ordinal_id}: {bid_count} bids, {ask_count} asks")
            
            # Check if we've reached the target ordinal
            if ordinal_id >= self.target_ordinal:
                logger.info(f"Reached target ordinal {self.target_ordinal}, validating Order Book...")
                await self._validate_order_book()
                self.running = False
                
        except struct.error as e:
            logger.error(f"Failed to parse delta message: {e}")
        except Exception as e:
            logger.error(f"Error processing delta: {e}")
    
    async def _validate_order_book(self):
        """Send Order Book for validation."""
        try:
            order_book_json = self.order_book.to_json()
            
            logger.info("Sending Order Book for validation...")
            async with self.session.post(
                "http://localhost:9090/assertion",
                json=order_book_json
            ) as response:
                if response.status == 200:
                    logger.info("✅ Order Book validation PASSED")
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Order Book validation FAILED: {response.status}")
                    logger.error(f"Error details: {error_text}")
                    
        except Exception as e:
            logger.error(f"Error during validation: {e}")
    
    async def cleanup(self):
        """Clean up resources."""
        self.running = False
        
        if self.websocket:
            await self.websocket.close()
        
        if self.session:
            await self.session.close()

async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Order Book Client")
    parser.add_argument("--ob-id", type=int, default=10000, help="Target Order Book ordinal ID")
    parser.add_argument("--depth", type=int, default=100, help="Order Book depth")
    
    args = parser.parse_args()
    
    client = OrderBookClient(args.ob_id, args.depth)
    
    try:
        await client.start()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Application error: {e}")
        sys.exit(1)
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 