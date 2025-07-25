# Custom Input Names Feature

## Overview

The Onkyo integration now supports querying and displaying user-defined input source names from the receiver, rather than just using the built-in constants.

## How It Works

### 1. EISCP Command Discovery
- Uses the `IRN` (Input Selector Rename / Input Function Rename) command
- Format: `iixxxxxxxxxx` where `ii` = input ID, `xxxxxxxxxx` = custom name (max 10 chars)
- Queries common input IDs: 00, 01, 02, 03, 04, 05, 10, 23, 24, 25, 26

### 2. Integration Points

#### Receiver Interview (`receiver.py`)
- `async_query_custom_input_names()`: Connects to receiver and queries IRN for each input
- `ReceiverInfo.custom_input_names`: New field storing dict of input_id -> custom_name
- `async_interview()`: Now queries custom names during discovery

#### Config Flow (`config_flow.py`)
- `get_configure_schema()`: Dynamically generates schema with custom names
- `parse_input_display_name()`: Parses "Custom Name (Original Name)" format back to meanings
- Input sources now display as "Custom Name (Original Meaning)" when custom names exist

### 3. User Experience

#### Before (Built-in names only):
```
Input Sources:
- VIDEO1 ··· VCR/DVR ··· STB/DVR
- VIDEO2 ··· CBL/SAT  
- DVD ··· BD/DVD
- CD ··· TV/CD
```

#### After (With custom names):
```
Input Sources:
- Apple TV (VIDEO1 ··· VCR/DVR ··· STB/DVR)
- Cable Box (VIDEO2 ··· CBL/SAT)
- Blu-ray (DVD ··· BD/DVD)  
- CD ··· TV/CD  # No custom name, shows default
```

## Technical Details

### Query Process
1. During receiver interview, establish temporary connection
2. Send `IRN` command with each input ID to query custom names
3. Parse responses in format: `zone="main", command="input-selector-rename-input-function-rename", value="00Apple TV"`
4. Store input_id -> custom_name mapping in `ReceiverInfo`

### Config Flow Enhancement
1. When showing input source selection, check for custom names
2. If custom name exists, display as "Custom Name (Default Name)"
3. When user selects, parse back to original meaning for processing
4. Maintain backward compatibility with existing configurations

### Error Handling
- Connection failures gracefully fall back to default names
- Invalid IRN responses are logged and ignored
- Empty custom names are filtered out
- Unknown input IDs are handled gracefully

## Testing

### Manual Testing
1. Use `test_input_names.py` to test connection and IRN queries
2. Use `input_name_helper.py` for standalone testing of the query function

### Integration Testing
```python
# Test the receiver interview process
info = await async_interview("192.168.1.100")
print(f"Custom names found: {info.custom_input_names}")

# Test config flow with custom names
# The config flow will automatically use custom names when available
```

## Limitations

1. **Receiver Support**: Only works with Onkyo receivers that support the IRN command
2. **Name Length**: Custom names limited to 10 characters (EISCP protocol limitation)
3. **Query Time**: Adds ~5 seconds to receiver interview process
4. **Network Dependency**: Requires network connection to receiver during setup

## Future Enhancements

1. **Caching**: Store custom names and refresh periodically
2. **Zone Support**: Extend to query custom names for other zones
3. **Real-time Updates**: Listen for IRN changes during operation
4. **User Override**: Allow users to override both custom and default names