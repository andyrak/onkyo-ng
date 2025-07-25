"""
Helper functions for querying custom input names from Onkyo receivers.
"""

import asyncio
import logging
from typing import Dict, Optional
import pyeiscp
from custom_components.onkyo_ng.const import InputSource

_LOGGER = logging.getLogger(__name__)

async def query_custom_input_names(host: str, port: int = 60128, timeout: int = 10) -> Dict[InputSource, str]:
    """
    Query custom input names from an Onkyo receiver.
    
    Args:
        host: Receiver IP address
        port: Receiver port (default 60128)
        timeout: Query timeout in seconds
        
    Returns:
        Dictionary mapping InputSource enums to their custom names
    """
    custom_names = {}
    received_names = {}
    
    def on_connect(origin: str):
        _LOGGER.debug(f"Connected to {origin} for input name query")
    
    def on_update(message: tuple, origin: str):
        """Process received messages looking for input rename responses."""
        if len(message) >= 3:
            zone, command, value = message[:3]
            _LOGGER.debug(f"Received: zone={zone}, command={command}, value={value}")
            
            # Check if this is an IRN (Input Rename) response
            if command == "input-selector-rename-input-function-rename":
                try:
                    # IRN response format: "iixxxxxxxxxx" where ii=input_id, xxxxxxxxxx=name
                    if isinstance(value, str) and len(value) >= 2:
                        input_id = value[:2]
                        custom_name = value[2:].strip()
                        
                        if custom_name:  # Only store non-empty names
                            received_names[input_id] = custom_name
                            _LOGGER.debug(f"Found custom name for input {input_id}: {custom_name}")
                            
                except Exception as e:
                    _LOGGER.debug(f"Error parsing IRN response: {e}")
    
    try:
        # Create connection
        conn = await pyeiscp.Connection.create(
            host=host,
            port=port,
            connect_callback=on_connect,
            update_callback=on_update,
            auto_connect=False
        )
        
        await conn.connect()
        await asyncio.sleep(1)  # Wait for connection to establish
        
        # Query input names for all known input sources
        for input_source in InputSource:
            try:
                input_id = input_source.value
                _LOGGER.debug(f"Querying custom name for input {input_id}")
                
                # Try different methods to query the input name
                
                # Method 1: Send IRN command with just the input ID
                try:
                    conn.send("main", "IRN", input_id)
                    await asyncio.sleep(0.2)
                except Exception as e:
                    _LOGGER.debug(f"IRN send failed for {input_id}: {e}")
                
                # Method 2: Send IRN query using the full command name
                try:
                    conn.send("main", "input-selector-rename-input-function-rename", input_id)
                    await asyncio.sleep(0.2)
                except Exception as e:
                    _LOGGER.debug(f"IRN full command failed for {input_id}: {e}")
                    
            except Exception as e:
                _LOGGER.debug(f"Failed to query input {input_source}: {e}")
                continue
        
        # Wait for responses
        await asyncio.sleep(timeout)
        
        # Map received names to InputSource enums
        for input_id, custom_name in received_names.items():
            try:
                input_source = InputSource(input_id)
                custom_names[input_source] = custom_name
            except ValueError:
                _LOGGER.debug(f"Unknown input ID received: {input_id}")
        
        conn.close()
        
    except Exception as e:
        _LOGGER.error(f"Failed to query custom input names: {e}")
    
    _LOGGER.info(f"Found {len(custom_names)} custom input names")
    return custom_names


async def get_input_display_names(host: str, port: int = 60128) -> Dict[InputSource, str]:
    """
    Get display names for inputs, preferring custom names over defaults.
    
    Args:
        host: Receiver IP address
        port: Receiver port
        
    Returns:
        Dictionary mapping InputSource to display names (custom or default)
    """
    # Start with default names
    display_names = {source: source.value_meaning for source in InputSource}
    
    # Try to get custom names
    try:
        custom_names = await query_custom_input_names(host, port)
        
        # Override defaults with custom names where available
        for source, custom_name in custom_names.items():
            if custom_name.strip():  # Only use non-empty custom names
                display_names[source] = custom_name
                
    except Exception as e:
        _LOGGER.warning(f"Could not query custom input names: {e}")
    
    return display_names


if __name__ == "__main__":
    # Test the functionality
    import sys
    
    async def test():
        host = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
        names = await get_input_display_names(host)
        
        print("Input Display Names:")
        for source, name in names.items():
            print(f"  {source.value} ({source.value_meaning}): {name}")
    
    asyncio.run(test())