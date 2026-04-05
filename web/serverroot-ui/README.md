# ServerRoot.net Web Interface

## Overview

ServerRoot.net is the ultimate AI-powered ransomware defense and incident response platform. The web interface provides a professional, enterprise-grade dashboard for monitoring and controlling autonomous defense agents across your infrastructure.

## Live Demo

🚀 **Live Access:** https://00ugi.app.super.myninja.ai

## Features

### 🎯 Real-Time Agent Dashboard
- Live monitoring of deployed agents across all platforms (Windows, Linux, macOS, ESXi, Android, IoT)
- Real-time CPU, memory, and resource usage tracking
- Agent status visualization (active, scanning, exploiting, deploying, idle)
- Instant access to agent vulnerabilities and exploit history

### 🛡️ System Statistics
- Total agents deployed and active status
- Vulnerability discovery metrics with severity breakdown
- Exploit execution statistics
- AI research report tracking
- System uptime monitoring

### 🔍 Agent Management
- Search and filter agents by hostname, IP, platform, or status
- Detailed agent profiles with resource metrics
- Platform-specific visual indicators (🪟 Windows, 🐧 Linux, 🍎 macOS, ☁️ ESXi, 🤖 Android, 🔌 IoT)
- One-click agent deployment and control

### 📊 Campaign Tracking
- Monitor active defense campaigns in real-time
- Track targets scanned, vulnerabilities found, agents deployed
- Campaign status and progress visualization
- Historical campaign completion data

### 🚨 Critical Vulnerabilities
- CVE database integration
- Severity classification (critical, high, medium, low)
- Exploit availability tracking
- Affected system counts

### ⚠️ Threat Intelligence
- Real-time threat detection and alerting
- Threat classification (ransomware, APT, exploit, malware)
- IOC (Indicators of Compromise) tracking
- Threat source attribution

### 🔬 AI Research Lab
- Track AI-powered vulnerability research
- Zero-day exploit generation progress
- Novel persistence mechanism discovery
- Evasion technique development

## Technology Stack

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **Tailwind CSS** - Utility-first styling
- **Heroicons** - Beautiful SVG icons

### Design Features
- Dark mode cyber-themed UI
- Glass morphism effects with backdrop blur
- Real-time animated updates
- Responsive design (mobile, tablet, desktop)
- Professional enterprise-grade aesthetics

## Project Structure

```
web/serverroot-ui/
├── src/
│   ├── app/
│   │   ├── globals.css          # Global styles and animations
│   │   ├── layout.tsx           # Root layout component
│   │   └── page.tsx             # Main page with navigation
│   ├── components/
│   │   ├── Header.tsx           # Navigation header
│   │   ├── Dashboard.tsx        # Main dashboard component
│   │   ├── Agents.tsx           # Agent management interface
│   │   └── StatsCard.tsx        # Statistics card component
│   ├── lib/
│   │   ├── mockData.ts          # Mock data for demonstration
│   │   └── utils.ts             # Utility functions
│   └── types/
│       └── index.ts             # TypeScript type definitions
├── public/                      # Static assets
├── next.config.js               # Next.js configuration
├── tailwind.config.js           # Tailwind CSS configuration
├── tsconfig.json                # TypeScript configuration
└── package.json                 # Dependencies and scripts
```

## Getting Started Locally

### Prerequisites
- Node.js 18.x or higher
- npm or yarn

### Installation

1. Clone the repository:
```bash
cd web/serverroot-ui
```

2. Install dependencies:
```bash
npm install
```

3. Start the development server:
```bash
npm run dev
```

4. Open your browser and navigate to:
```
http://localhost:3000
```

### Build for Production

```bash
npm run build
npm start
```

## Integration with ServerRoot.net Backend

### API Endpoints

The web interface is designed to connect to the ServerRoot.net backend API running on port 8443:

```typescript
// API rewrites configured in next.config.js
async rewrites() {
  return [
    {
      source: '/api/:path*',
      destination: 'http://localhost:8443/api/:path*',
    },
  ]
}
```

### WebSocket Connection

For real-time updates, the interface connects to the ServerRoot.net WebSocket server:

```typescript
import { io } from 'socket.io-client';

const socket = io('http://localhost:8443', {
  transports: ['websocket'],
  reconnection: true,
});

socket.on('agent_update', (agent: Agent) => {
  // Update agent in real-time
});

socket.on('threat_detected', (threat: Threat) => {
  // Display threat alert
});
```

## Features in Development

### Coming Soon
- **Vulnerabilities Module** - Comprehensive CVE management and exploitation
- **Threat Intelligence** - Real-time threat detection and analysis
- **Campaign Manager** - Automated defense campaign orchestration
- **AI Research Lab** - Zero-day discovery and exploit generation interface
- **Command Center** - Agent command and control console

### Planned Enhancements
- Multi-tenant support with role-based access control
- Audit trail and compliance reporting
- SIEM integration (Jira, ServiceNow)
- Automated report generation and export
- Mobile-optimized application
- Dark/light theme toggle
- Customizable dashboard widgets

## Customization

### Branding

Update the branding in `src/app/layout.tsx`:

```typescript
export const metadata: Metadata = {
  title: 'ServerRoot.net - AI Defense Platform',
  description: 'Ultimate AI-powered ransomware defense and incident response platform',
}
```

### Theme Colors

Customize the theme colors in `tailwind.config.js`:

```javascript
theme: {
  extend: {
    colors: {
      'serverroot': {
        // Customize ServerRoot brand colors
      },
      'cyber': {
        green: '#00ff41',
        red: '#ff0033',
        yellow: '#fbbf24',
      }
    },
  },
}
```

## Security Considerations

- All API communications should use HTTPS in production
- Implement authentication and authorization
- Use environment variables for sensitive configuration
- Enable CSRF protection
- Implement rate limiting
- Regular security updates for dependencies

## Performance Optimization

- Next.js automatic code splitting
- Image optimization with next/image
- Lazy loading for performance
- WebSocket for real-time data instead of polling
- Efficient state management with React hooks

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## License

Proprietary - ServerRoot.net Enterprise Edition

## Support

For support and updates:
- Email: support@serverroot.net
- Web: https://serverroot.net
- Documentation: https://docs.serverroot.net

---

**ServerRoot.net - Changing the World, One System at a Time** 🌍🛡️