# ServerRoot.net — Intelligence Report
**Scan ID:** SCAN-20260405-104623  
**Date:** 2026-04-05 10:48 UTC  
**Classification:** INTERNAL — PRODUCTION RECON  

---

## 🖥️ Target Environment

| Property | Value |
|----------|-------|
| Hostname | 172.28.137.134 |
| OS | Debian GNU/Linux 12 (bookworm) |
| Network | 172.28.0.0/16 |
| IPs | 127.0.0.1/8, 172.28.137.134/16 |
| Gateway | 172.28.0.1 |

---

## 🔓 Exposed Services (21 Open Ports)

### External-Facing (0.0.0.0)

| Port | Service | Details | Risk |
|------|---------|---------|------|
| 22 | OpenSSH 9.2p1 | Debian-2+deb12u7 — SSH access | MEDIUM |
| 5001 | Flask API | Werkzeug/3.1.8 Python/3.11.14 — ServerRoot API | LOW |
| 5000 | nginx/1.22.1 | **401 Unauthorized** — protected service | MEDIUM |
| 5901 | x11vnc | VNC server exposed on all interfaces | HIGH |
| 6080 | noVNC | Web-based VNC client — browser accessible | HIGH |
| 8080 | FastAPI/uvicorn | Browser automation API — full Swagger UI | CRITICAL |
| 8443 | C2 Server | Python — ServerRoot C2 on TCP | MEDIUM |
| 3222 | nginx | SSH proxy (nginx stream) | MEDIUM |

### Localhost-Only (127.0.0.1)

| Port | Service | Details |
|------|---------|---------|
| 2222 | ttyd | Web terminal (SSH-alt) |
| 4000 | Node.js | Internal code-server |
| 9222 | Chrome DevTools | Remote debugging protocol |
| 18080 | Psiphon tunnel | VPN tunnel local endpoint |
| 18081 | Psiphon tunnel | VPN tunnel local endpoint |

### Other

| Port | Service | Details |
|------|---------|---------|
| 9084 | github-mcp-server | GitHub MCP service |
| 3002 | Next.js | ServerRoot UI dashboard |
| 8002 | FastAPI | Secondary browser automation API |

---

## 🚨 Critical Findings

### FINDING-001: Browser Automation API Exposed (CRITICAL)
- **Port:** 8080 (uvicorn/FastAPI)
- **Swagger UI:** http://172.28.137.134:8080/docs
- **20+ automation endpoints discovered:**
  - `/auth` — password validation + cookie setting
  - `/api/automation/navigate_to` — navigate browser to any URL
  - `/api/automation/click_element` — click any element
  - `/api/automation/input_text` — type into any field
  - `/api/automation/extract_content` — extract page content
  - `/api/automation/execute_script` — execute JavaScript
  - `/api/automation/open_tab` — open browser tabs
  - `/api/automation/search_google` — Google search
- **Risk:** Full browser control API — can be used to steal cookies, perform CSRF, access authenticated sessions
- **Recommendation:** Bind to 127.0.0.1 only, add authentication

### FINDING-002: VNC Server Exposed (HIGH)
- **Port:** 5901 (x11vnc) — all interfaces
- **Port:** 6080 (noVNC web client) — browser-accessible VNC
- **Risk:** Full desktop access if password is weak/absent
- **Recommendation:** Bind to localhost, use SSH tunneling

### FINDING-003: Secondary Browser API (HIGH)
- **Port:** 8002 (FastAPI) — browser automation API
- **Endpoints:** `/api`, `/api/automation/*`
- **Risk:** Same as FINDING-001 — duplicate attack surface

### FINDING-004: Chrome DevTools Remote (MEDIUM)
- **Port:** 9222 (localhost) — Chrome remote debugging
- **Risk:** If accessible, allows full browser control, credential theft
- **Recommendation:** Keep localhost-only, verify no external forwarding

### FINDING-005: Protected nginx Service (MEDIUM)
- **Port:** 5000 — nginx/1.22.1 returns 401
- **Risk:** Unknown service behind auth — need to identify
- **Recommendation:** Identify service, audit access controls

---

## 🔍 DNS Intelligence

### serverroot.net
| Record | Value |
|--------|-------|
| MX | serverroot-net.mail.protection.outlook.com (Microsoft 365) |
| NS | ns1-4.bdm.microsoftonline.com (Microsoft DNS) |
| SPF | include:spf.protection.outlook.com |
| TXT | mscid verification token present |

**Assessment:** serverroot.net is hosted on Microsoft 365/Azure infrastructure. No A record found in this query — domain may not have public web hosting yet.

### github.com
| Record | Value |
|--------|-------|
| A | 140.82.116.3 |
| Subdomains | www → 140.82.116.4, api → 140.82.116.5, admin → 140.82.113.24 |

### google.com
| Record | Value |
|--------|-------|
| A | 142.250.73.110 |
| AAAA | 2607:f8b0:400a:80c::200e |
| MX | smtp.google.com |
| Subdomains | www, mail, api, admin, vpn all resolved |

---

## 🌐 Web Services Discovered

### http://172.28.137.134:5001 (Flask/ServerRoot API)
- **Technology:** Werkzeug/3.1.8 Python/3.11.14
- **Endpoints:** /api/health, /api/swarm/*, /api/swarm/init, /api/swarm/agents, /api/swarm/scale

### http://172.28.137.134:8080 (FastAPI Browser Automation)
- **Technology:** uvicorn
- **Endpoints:** /docs, /openapi.json, /auth, /api/automation/* (20+ endpoints)
- **Auth:** `/auth` endpoint — password-based cookie auth

### http://172.28.137.134:6080 (noVNC)
- **Technology:** noVNC web client
- **Function:** Connects to VNC server at 5901
- **Auth:** Password prompt via browser

---

## 🖥️ Running Services (29 detected)

Key processes identified:
- `supervisord` — process manager (PID 628)
- `nginx` — reverse proxy (PID 636-638)
- `browser_api.py` — browser automation backend (PID 657)
- `server.py` — application server (PID 658)
- `code-server` — VS Code in browser (PID 661, 735)
- `psiphon-tunnel` — VPN tunnel (PID 655)
- `x11vnc` — VNC server (PID 642)
- `python run_api_server.py` — ServerRoot Flask API (PID 14299)
- `next-server` — ServerRoot UI (PID 14915)
- `python run_c2_server.py` — ServerRoot C2 (PID 18867)
- `github-mcp-server` — GitHub MCP integration (PID 16331)
- `chrome` — Headless Chromium (PID 13831)

---

## 📊 Scan Summary

| Metric | Value |
|--------|-------|
| Hosts Discovered | 1 (isolated sandbox) |
| Open Ports Found | 21 |
| Web Services | 4 |
| Critical Findings | 1 |
| High Findings | 2 |
| Medium Findings | 3 |
| DNS Targets | 3 |
| Subdomains Resolved | 9 |

---

## 🔧 Recommendations

1. **IMMEDIATE:** Bind :8080 browser automation API to 127.0.0.1 only
2. **IMMEDIATE:** Add authentication to noVNC (:6080) 
3. **HIGH:** Audit VNC password strength (:5901)
4. **HIGH:** Identify service behind nginx :5000 (401)
5. **MEDIUM:** Document Chrome DevTools :9222 access controls
6. **LOW:** Verify Psiphon tunnel (:18080/18081) is intentional

---

*Report generated by ServerRoot.net Real Scanner Agent v2.0*  
*Scan duration: ~90 seconds*