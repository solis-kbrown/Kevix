# ServerRoot.net — PRODUCTION PUSH (24/7 Operations)

## Phase 1: GitHub Push
- [ ] Initialize git repo and configure remote (solis-kbrown/Kevix)
- [ ] Clean up / stage all production files
- [ ] Commit and force-push to main branch

## Phase 2: Start All Services (24/7)
- [ ] Start Flask API on :5001
- [ ] Start C2 server
- [ ] Start Next.js UI on :3000
- [ ] Start watchdog automation
- [ ] Start scheduler automation
- [ ] Verify all 5 services healthy

## Phase 3: Expose & Validate Live Platform
- [ ] Expose Next.js UI port (single tunnel)
- [ ] Confirm API proxy working through UI tunnel
- [ ] Confirm dashboard loads with live data

## Phase 4: Launch Real Swarm Agents
- [ ] Start real swarm operations (IROperator)
- [ ] Confirm agents producing live outputs
- [ ] Show live dashboard data

## Phase 5: Production Keepalive
- [ ] Set up auto-restart loop (background)
- [ ] Confirm everything running 24/7