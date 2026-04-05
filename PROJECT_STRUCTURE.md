# IR Platform - Project Structure

```
ir-platform/
│
├── iroperator.py              # Main orchestration engine
├── quick_start.py             # Setup and demo script
├── config.json                # Configuration file
├── requirements.txt           # Python dependencies
├── README.md                  # Main documentation
│
├── c2/                        # Command & Control
│   └── server.py              # C2 server and console
│
├── scanner/                   # Network scanning
│   └── network_scanner.py     # Scanner with nmap integration
│
├── exploits/                  # Exploitation & Intel
│   ├── ai_assistant.py        # AI-powered analysis (OpenRouter)
│   ├── exploit_executor.py    # Exploit execution & agent deployment
│   └── vuln_intel.py          # Vulnerability intelligence database
│
├── agent/                     # Agent code (deployed to targets)
│   └── (Generated dynamically by executor)
│
├── console/                   # Operator consoles
│   ├── web/                   # Web dashboard (future)
│   └── cli/                   # CLI interface (in c2/server.py)
│
├── data/                      # Data storage
│   ├── intel.db               # Vulnerability intelligence
│   ├── c2_database.db         # C2 server data
│   ├── scans/                 # Scan results (JSON)
│   ├── reports/               # Generated reports
│   ├── agents/                # Agent files
│   └── exploits/              # Exploit scripts
│
├── logs/                      # Operation logs
│   ├── c2_server.log          # C2 server logs
│   └── operations.log         # Operation logs
│
└── static/                    # Static resources
    └── (Web assets, future)
```

## Module Dependencies

### iroperator.py (Main Orchestration)
```
├── scanner.network_scanner
├── exploits.ai_assistant
├── exploits.exploit_executor
├── exploits.vuln_intel
└── c2.server
```

### exploits.exploit_executor
```
├── vuln_intel (for recording)
└── ai_assistant (for exploit generation)
```

### c2.server
```
├── sqlite3 (database)
├── socket (network)
└── threading (concurrency)
```

## Data Flow

```
1. iroperator.py
   ↓
2. network_scanner.py → discovers services
   ↓
3. ai_assistant.py → analyzes vulnerabilities
   ↓
4. exploit_executor.py → executes exploits
   ↓
5. vuln_intel.py → records intelligence
   ↓
6. c2.server.py → manages deployed agents
   ↓
7. Reports generated in data/reports/
```

## Database Schema

### intel.db (Vulnerability Intelligence)
- `vulnerabilities` - CVE information
- `exploits` - Working exploits
- `exploitation_history` - All attempts
- `discovered_targets` - Found during scans
- `ai_analysis` - AI analysis results

### c2_database.db (C2 Server)
- `agents` - Registered agents
- `commands` - Issued commands
- `operations` - IR operations
- `results` - Command execution results