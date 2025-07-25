#!/usr/bin/env python3
"""
Test script to check if we can query custom input names from Onkyo receiver.
"""

import asyncio
import sys
import pyeiscp
from custom_components.onkyo_ng.const import InputSource, PYEISCP_COMMANDS

async def test_query_input_names(host: str = "192.168.1.100"):
    """Test querying custom input names from receiver."""
    
    print(f"Attempting to connect to receiver at {host}...")
    
    # Store received messages
    received_messages = []
    
    def on_connect(origin: str):
        print(f"Connected to {origin}")
    
    def on_update(message: tuple, origin: str):
        print(f"Received message: {message} from {origin}")
        received_messages.append(message)
    
    try:
        # Create connection
        conn = await pyeiscp.Connection.create(
            host=host,
            connect_callback=on_connect,
            update_callback=on_update,
            auto_connect=False
        )
        
        await conn.connect()
        await asyncio.sleep(2)  # Wait for connection
        
        # Test querying input names for common inputs
        input_ids = ['00', '01', '02', '03', '10', '23', '24']  # Common input IDs
        
        print("\nTesting input name queries...")
        
        for input_id in input_ids:
            try:
                input_source = InputSource(input_id)
                print(f"\nTesting input {input_id} ({input_source.value_meaning}):")
                
                # Method 1: Try to query using IRN command directly
                try:
                    # Query by sending just the input ID to IRN
                    conn.send("main", "IRN", input_id)
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  IRN query failed: {e}")
                
                # Method 2: Try query_property if it supports IRN
                try:
                    conn.query_property("main", "input-selector-rename-input-function-rename")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  query_property failed: {e}")
                    
            except ValueError:
                print(f"  Input {input_id} not recognized")
                continue
        
        await asyncio.sleep(2)  # Wait for responses
        
        print(f"\nReceived {len(received_messages)} messages:")
        for msg in received_messages:
            print(f"  {msg}")
            
        conn.close()
        
    except Exception as e:
        print(f"Connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
    asyncio.run(test_query_input_names(host))