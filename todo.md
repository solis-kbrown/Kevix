# ServerRoot.net — FULL PRODUCTION EXPANSION

## Phase 1: Autonomous Wide-Area Scan Loop ✅ (partial)
- [x] Build scan_find_deploy_v2.py with real fingerprinting
- [x] Build autonomous_loop.py with infinite cycle
- [ ] Fix autonomous_loop.py launch (nohup + disown properly)
- [ ] Expand target ranges to full /16 sweep
- [ ] Wire all agents into loop (use all available agents)

## Phase 2: Live Telemetry Reporting Dashboard
- [ ] Build real-time dashboard HTML (WebSocket or polling)
- [ ] Show: active agents, live scan results, vulns found, ops/sec
- [ ] Show: CISA KEV feed, NVD CVEs, deployed agents map
- [ ] Integrate with Flask API live data endpoints
- [ ] Serve dashboard on :3003 or embed in Next.js UI

## Phase 3: External C2 Callbacks + Exfil Channels
- [ ] Add beacon endpoint to Flask API (/api/beacon)
- [ ] Build HTTP-based exfil channel (POST findings to API)
- [ ] Add DNS-based callback stub
- [ ] Add encrypted agent → C2 comms channel
- [ ] Wire agents to phone home every 60s with findings

## Phase 4: Keepalive / Auto-Restart on Reboot
- [ ] Create systemd service units for all processes
- [ ] Create /etc/supervisor/conf.d/serverroot.conf entries
- [ ] Update deploy/keepalive.sh with all new agents
- [ ] Test restart recovery for autonomous_loop
- [ ] Push everything to GitHub solis-kbrown/Kevix