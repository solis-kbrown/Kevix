# ServerRoot.net Web Interface - Quick Start Guide

## 🚀 Getting Started in 5 Minutes

### Step 1: Access the Live Demo

Simply open your browser and navigate to:
```
https://00ugi.app.super.myninja.ai
```

No installation required! The interface is already running with demo data.

### Step 2: Explore the Dashboard

When you first load the page, you'll see the **Dashboard** with:

1. **Stats Cards** - 4 key metrics at the top
2. **Active Agents Panel** - Real-time agent monitoring
3. **Active Campaigns Panel** - Campaign tracking
4. **Critical Vulnerabilities** - CVE database view
5. **Recent Threats** - Threat intelligence feed
6. **AI Research Activity** - Research progress tracking

### Step 3: Navigate the Interface

Use the navigation bar at the top to switch between sections:

- **Dashboard** - Overview and statistics
- **Agents** - Detailed agent management
- **Vulnerabilities** - CVE management (coming soon)
- **Threats** - Threat intelligence (coming soon)
- **Campaigns** - Campaign orchestration (coming soon)
- **AI Research** - Research lab (coming soon)
- **Commands** - Command center (coming soon)

## 📱 Using the Agent Management Interface

### Viewing Agents

1. Click on the **"Agents"** tab in the navigation
2. You'll see all deployed agents in a grid layout
3. Each agent card shows:
   - Platform icon and hostname
   - IP address
   - Current status (color-coded)
   - CPU and memory usage
   - Vulnerability count
   - Exploits executed
   - Uptime

### Filtering Agents

1. Use the **search bar** to find agents by hostname or IP
2. Use the **platform dropdown** to filter by:
   - Windows
   - Linux
   - macOS
   - ESXi
   - Android
   - IoT
3. Use the **status dropdown** to filter by:
   - Active
   - Scanning
   - Exploiting
   - Deploying
   - Idle

### Agent Actions

Each agent card has three action buttons:

- **Start** - Activate an idle agent
- **Stop** - Halt agent operations
- **Details** - View comprehensive agent information

## 🎯 Understanding the Dashboard

### Stats Cards

The four stats cards show:

1. **Total Agents**
   - Current number of deployed agents
   - Active agent count in green
   - Updates automatically

2. **Vulnerabilities Found**
   - Total vulnerabilities discovered
   - Critical count in red/yellow
   - Real-time updates

3. **Exploits Executed**
   - Successful exploit count
   - Hourly change indicator
   - Trend tracking

4. **AI Research Reports**
   - Research report count
   - Currently generating reports
   - Progress tracking

### Agent Status Colors

- 🟢 **Green** - Active and operating normally
- 🔵 **Blue** - Working (scanning, exploiting, deploying)
- 🟡 **Yellow** - Idle or paused
- 🔴 **Red** - Error or stopped

### Platform Indicators

- 🪟 **Windows** - Microsoft Windows systems
- 🐧 **Linux** - Linux distributions
- 🍎 **macOS** - Apple macOS systems
- ☁️ **ESXi** - VMware ESXi hypervisors
- 🤖 **Android** - Android devices
- 🔌 **IoT** - Internet of Things devices

## 🔍 Interpreting Data

### Vulnerability Severity

- 🔴 **Critical** - Immediate action required
- 🟠 **High** - Address within 24 hours
- 🟡 **Medium** - Address within 72 hours
- 🟢 **Low** - Address in next maintenance cycle

### Threat Types

- **Ransomware** - Malicious software encryption
- **APT** - Advanced Persistent Threats
- **Exploit** - Vulnerability exploitation attempts
- **Malware** - General malicious software

### Agent Operations

- **Active** - Agent is operational and monitoring
- **Scanning** - Agent is actively scanning network
- **Exploiting** - Agent is executing exploits
- **Deploying** - Agent is spreading to new systems
- **Idle** - Agent is waiting for commands

## ⚡ Real-Time Features

The interface updates automatically every 3-5 seconds:

- Agent CPU and memory usage fluctuations
- Statistics increments
- New threats detection
- Research progress updates
- Campaign status changes

Watch for the **pulse animation** on active agents to see live updates!

## 🎨 Customizing the View

### Responsive Design

The interface adapts automatically to your screen size:

- **Desktop (>1024px)** - Full-featured layout
- **Tablet (768-1024px)** - Optimized grid
- **Mobile (<768px)** - Single column layout

### Navigation

On mobile devices, use horizontal scrolling in the navigation bar to access all tabs.

## 🔧 Troubleshooting

### Interface Not Loading

1. Clear your browser cache
2. Try refreshing the page
3. Check your internet connection
4. Try a different browser (Chrome, Firefox, Safari, Edge)

### Data Not Updating

1. Wait 3-5 seconds for automatic updates
2. Check that your connection is stable
3. Refresh the page if needed

### Mobile Display Issues

1. Ensure you're using a modern browser
2. Try landscape orientation
3. Clear browser cache

## 📊 Understanding Mock Data

The live demo uses mock data to simulate:

- 5 deployed agents across different platforms
- Real-time resource usage fluctuations
- 4 active campaigns
- 3 critical vulnerabilities
- 3 recent threats
- 2 AI research reports (1 generating, 1 completed)

This allows you to explore all features without needing a backend connection.

## 🚀 Next Steps

### For Developers

To run locally or contribute:
```bash
cd web/serverroot-ui
npm install
npm run dev
```

See [README.md](README.md) for full documentation.

### For Users

1. Explore all tabs in the navigation
2. Try filtering agents by different criteria
3. Watch the real-time updates
4. Check the status colors and indicators
5. Read the tooltips and hover effects

### For Integrations

The interface is designed to connect to:
- ServerRoot.net backend API (port 8443)
- WebSocket for real-time updates
- Multiple data providers
- External threat intelligence sources

## 📞 Support

- 🌐 Live Demo: https://00ugi.app.super.myninja.ai
- 📧 Email: support@serverroot.net
- 📚 Documentation: https://docs.serverroot.net
- 🐛 Issues: https://github.com/serverrootnet/issues

## 🔐 Security Notes

- The live demo uses mock data and is securely isolated
- No real vulnerabilities are exploited
- No live threats are monitored
- Perfect for testing and evaluation without risk

---

**Start exploring ServerRoot.net now and experience the future of AI-powered cybersecurity defense!** 🛡️✨