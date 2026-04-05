<h1>ServerRoot.net — Human Action Guide</h1><h2>Complete Manual Setup &amp; Deployment Checklist</h2><h3>v2.0.0-Enterprise | Updated: April 2026</h3><hr><h2>🎯 TL;DR — What's Automated vs What YOU Must Do</h2><table class="e-rte-table"> <thead> <tr> <th>Task</th> <th>Automated?</th> <th>You Do</th> </tr> </thead> <tbody><tr> <td>Service auto-restart</td> <td>✅ Watchdog</td> <td>Nothing</td> </tr> <tr> <td>Health checks every 60s</td> <td>✅ Scheduler</td> <td>Nothing</td> </tr> <tr> <td>Daily backups</td> <td>✅ Scheduler</td> <td>Nothing</td> </tr> <tr> <td>Log cleanup</td> <td>✅ Scheduler</td> <td>Nothing</td> </tr> <tr> <td>Broken dir/DB healing</td> <td>✅ Self-Healer</td> <td>Nothing</td> </tr> <tr> <td>OpenRouter AI key</td> <td>❌</td> <td>Section 1</td> </tr> <tr> <td>Email notifications</td> <td>❌</td> <td>Section 2</td> </tr> <tr> <td>DNS setup</td> <td>❌</td> <td>Section 3</td> </tr> <tr> <td>VM provisioning</td> <td>❌</td> <td>Section 4</td> </tr> <tr> <td>SSL/TLS certificate</td> <td>❌</td> <td>Section 5</td> </tr> <tr> <td>First login / password</td> <td>❌</td> <td>Section 6</td> </tr> <tr> <td>Download &amp; move files</td> <td>❌</td> <td>Section 7</td> </tr> </tbody></table><hr><h2>Section 1 — OpenRouter API Key (Enables Real AI/LLM)</h2><p><strong>Without this:</strong> System runs fully, but AI calls return rule-based fallbacks.<br><strong>With this:</strong> DeepSeek R1, Claude Sonnet, GPT-4o, Gemini, Llama analyze CVEs, plan attacks, diagnose errors in real time.</p><h3>Steps:</h3><ol> <li>Go to <strong><a href="https://openrouter.ai">https://openrouter.ai</a></strong> → Sign up (free tier available)</li> <li>Click <strong>Keys</strong> → <strong>Create Key</strong></li> <li>Copy your key (starts with <code>sk-or-v1-...</code>)</li> <li><p>Add to your <code>.env</code> file:</p><pre><code class="language-bash">OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxxxxxxxxx
</code></pre> </li> <li>Restart the API server: <code>pkill -f run_api_server.py &amp;&amp; python run_api_server.py &amp;</code></li> </ol><h3>Cost estimate:</h3><ul> <li>DeepSeek R1: ~$0.55/M tokens (very cheap)</li> <li>Claude Sonnet 3.5: ~$3/M tokens</li> <li>GPT-4o: ~$5/M tokens</li> <li>Gemini Flash: ~$0.10/M tokens (nearly free)</li> </ul><hr><h2>Section 2 — Email Notifications Setup</h2><p>The system can email you on: service restarts, health reports (hourly), disk warnings, backup completions, self-healer actions, and system startup.</p><h3>Option A: Gmail (recommended for personal use)</h3><ol> <li>Enable 2-Factor Authentication on your Google account</li> <li>Go to: <strong><a href="https://myaccount.google.com/apppasswords">https://myaccount.google.com/apppasswords</a></strong></li> <li>Create an App Password → name it "ServerRoot"</li> <li><p>Add to <code>.env</code>:</p><pre><code class="language-bash">SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=you@gmail.com
SMTP_PASS=xxxx-xxxx-xxxx-xxxx    # the 16-char app password
NOTIFY_EMAIL=alerts@yourdomain.com
FROM_NAME=ServerRoot.net
</code></pre> </li> </ol><h3>Option B: SendGrid (recommended for production)</h3><ol> <li>Sign up at <strong><a href="https://sendgrid.com">https://sendgrid.com</a></strong> (free 100 emails/day)</li> <li>Create an API Key</li> <li><p>Add to <code>.env</code>:</p><pre><code class="language-bash">SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USER=apikey
SMTP_PASS=SG.xxxxxxxxxxxxxxxx   # your SendGrid API key
NOTIFY_EMAIL=alerts@yourdomain.com
</code></pre> </li> </ol><h3>Option C: Mailgun</h3><pre><code class="language-bash">SMTP_HOST=smtp.mailgun.org
SMTP_PORT=587
SMTP_USER=postmaster@mg.yourdomain.com
SMTP_PASS=your-mailgun-password
NOTIFY_EMAIL=you@yourdomain.com
</code></pre><h3>Test email configuration:</h3><pre><code class="language-bash">python automation/email_notifier.py --test
</code></pre><hr><h2>Section 3 — DNS Setup</h2><p>Point your domain to your VM's public IP.</p><h3>Records to create:</h3><pre><code>Type    Name              Value               TTL
A       serverroot.net    &lt;YOUR-VM1-IP&gt;       300
A       www               &lt;YOUR-VM1-IP&gt;       300
A       api               &lt;YOUR-VM1-IP&gt;       300
A       c2                &lt;YOUR-VM2-IP&gt;       300
</code></pre><h3>Verify DNS propagation:</h3><pre><code class="language-bash">dig serverroot.net +short
nslookup serverroot.net
</code></pre><p>DNS can take 5 minutes to 48 hours to propagate globally.</p><hr><h2>Section 4 — VM Preparation &amp; Deployment</h2><h3>Requirements:</h3><ul> <li>Ubuntu 22.04 LTS or Debian 12</li> <li>2+ CPU cores, 4GB+ RAM, 50GB+ SSD</li> <li>Python 3.11+, Node.js 20+</li> <li>Ports open: 22 (SSH), 80, 443, 3001, 5001, 8443</li> </ul><h3>Step 1: Copy files to your VM</h3><pre><code class="language-bash"># From your local machine — download from this sandbox:
# All files are in /workspace — zip and download

# Or git clone if you have a repo set up:
git clone &lt;your-repo&gt; /opt/serverroot
</code></pre><h3>Step 2: Run VM setup script</h3><pre><code class="language-bash">cd /opt/serverroot
chmod +x deploy/setup_vm.sh
sudo bash deploy/setup_vm.sh
</code></pre><p>This script installs: Python 3.11, pip deps, Node.js 20, nginx, certbot, systemd services.</p><h3>Step 3: Configure environment</h3><pre><code class="language-bash">cp .env.example .env
nano .env   # Fill in your API key, email, IPs
</code></pre><h3>Step 4: Start everything</h3><pre><code class="language-bash">bash deploy/start_all.sh
</code></pre><h3>Step 5: Install cron + systemd automation</h3><pre><code class="language-bash">bash automation/setup_cron.sh
</code></pre><h3>Step 6: Verify health</h3><pre><code class="language-bash">bash deploy/health_check.sh
</code></pre><h3>For VM2 (C2 server only):</h3><pre><code class="language-bash"># Same steps, but only start C2:
nohup python run_c2_server.py &gt; logs/c2_server.log 2&gt;&amp;1 &amp;
# Set PEER_VM_IP=&lt;vm1-ip&gt; in .env
</code></pre><hr><h2>Section 5 — SSL/TLS Certificate (HTTPS)</h2><p>Run this AFTER DNS has propagated and nginx is running:</p><pre><code class="language-bash"># Install certbot (already done by setup_vm.sh)
sudo certbot --nginx -d serverroot.net -d www.serverroot.net

# Auto-renewal is set up automatically by certbot
# Test renewal:
sudo certbot renew --dry-run
</code></pre><p>After SSL is set up, update nginx to redirect HTTP → HTTPS.</p><hr><h2>Section 6 — First Login &amp; Security</h2><h3>Change the default secret key:</h3><pre><code class="language-bash"># In .env:
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")
</code></pre><h3>Set up firewall:</h3><pre><code class="language-bash">sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw allow 3001/tcp  # UI (or proxy via nginx)
sudo ufw allow 5001/tcp  # API
sudo ufw allow 8443/tcp  # C2
sudo ufw enable
</code></pre><h3>Restrict API access (optional, recommended for production):</h3><p>Edit <code>run_api_server.py</code> — change host from <code>0.0.0.0</code> to <code>127.0.0.1</code> and proxy through nginx with auth.</p><hr><h2>Section 7 — Downloading &amp; Moving Files</h2><h3>How to download everything from this sandbox:</h3><p>The entire project is in <code>/workspace</code>. You can:</p><p><strong>Option A: Download individual files</strong> via the file browser in this interface.</p><p><strong>Option B: Create a zip archive:</strong></p><pre><code class="language-bash">cd /workspace &amp;&amp; zip -r serverroot_complete.zip . \
  --exclude "*/node_modules/*" \
  --exclude "*/__pycache__/*" \
  --exclude "*/.next/*" \
  --exclude "*/archive/*"
</code></pre><p><strong>Option C: Git init and push to your repo:</strong></p><pre><code class="language-bash">cd /workspace
git init
git add .
git commit -m "ServerRoot.net v2.0.0-Enterprise"
git remote add origin git@github.com:yourusername/serverroot.git
git push -u origin main
</code></pre><h3>On your VM — rebuild the frontend:</h3><pre><code class="language-bash">cd web/serverroot-ui
npm install
npm run build
</code></pre><p>(The <code>.next/</code> build folder is not included in git — you rebuild on the server)</p><hr><h2>Section 8 — What's Fully Automated (Do Nothing)</h2><p>Once <code>setup_cron.sh</code> and <code>start_all.sh</code> are run, these happen automatically:</p><table class="e-rte-table"> <thead> <tr> <th>Task</th> <th>Frequency</th> <th>Script</th> </tr> </thead> <tbody><tr> <td>Health check + report</td> <td>Every 60 seconds</td> <td>scheduler.py</td> </tr> <tr> <td>Self-healing check</td> <td>Every 5 minutes (cron)</td> <td>self_healer.py</td> </tr> <tr> <td>Data backup to data/backups/</td> <td>Every hour</td> <td>scheduler.py</td> </tr> <tr> <td>Old log cleanup (&gt;7 days)</td> <td>Daily 2am</td> <td>scheduler.py</td> </tr> <tr> <td>Old scan cleanup (&gt;30 days)</td> <td>Daily 2:30am</td> <td>scheduler.py</td> </tr> <tr> <td>Peer VM sync</td> <td>Every 5 minutes</td> <td>scheduler.py</td> </tr> <tr> <td>Intel DB update</td> <td>Every 2 hours</td> <td>scheduler.py</td> </tr> <tr> <td>Session log rotation</td> <td>Every hour</td> <td>scheduler.py</td> </tr> <tr> <td>API server auto-restart</td> <td>On failure</td> <td>watchdog.py</td> </tr> <tr> <td>C2 server auto-restart</td> <td>On failure</td> <td>watchdog.py</td> </tr> <tr> <td>Disk space alert email</td> <td>When &gt;85%</td> <td>watchdog.py</td> </tr> <tr> <td>Service restart email</td> <td>On each restart</td> <td>watchdog.py</td> </tr> <tr> <td>Hourly health email</td> <td>On the hour</td> <td>scheduler.py</td> </tr> <tr> <td>Startup email</td> <td>On start_all.sh</td> <td>start_all.sh</td> </tr> </tbody></table><hr><h2>Section 9 — Troubleshooting Quick Reference</h2><pre><code class="language-bash"># Check all service status:
bash deploy/health_check.sh

# View live API logs:
tail -f logs/api_server.log

# View watchdog logs:
tail -f logs/watchdog.log

# View scheduler logs:
tail -f logs/scheduler.log

# Manually run self-healer:
python -c "import sys; sys.path.insert(0,'.'); import automation.self_healer as sh; print(sh.run_all_healers())"

# Run all tests:
python tests/test_modules.py

# Test email:
python automation/email_notifier.py --test

# Check databases:
python -c "
import sqlite3
for db in ['data/intel.db','data/c2_database.db','data/comprehensive_records.db']:
    conn = sqlite3.connect(db)
    tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
    for (t,) in tables:
        n = conn.execute(f'SELECT COUNT(*) FROM \"{t}\"').fetchone()[0]
        if n &gt; 0: print(f'{db}::{t} = {n} rows')
    conn.close()
"

# Restart everything:
bash deploy/stop_all.sh &amp;&amp; bash deploy/start_all.sh
</code></pre><hr><h2>Section 10 — Architecture Reference</h2><pre><code>VM1 (Primary) — Business Tier
├── Next.js UI          :3001  (Dashboard, Agents, Vulns, Threats, AI Research)
├── Flask API Server    :5001  (11 REST endpoints, swarm management)
├── Nginx Proxy         :80/:443 → :3001/:5001
├── Watchdog            (background — auto-restart services)
├── Scheduler           (background — 8 recurring tasks)
└── Self-Healer         (cron */5min — heal broken conditions)

VM2 (C2 Node) — Business Tier
├── C2 Server           :8443  (agent command &amp; control)
├── Watchdog            (same — monitors C2)
└── Peer Sync           (syncs data back to VM1 every 5min)

Both VMs
├── SQLite DBs: intel.db, c2_database.db, comprehensive_records.db
├── Python 3.11 — 96 modules across agent/, exploits/, stealth/, etc.
└── Email notifications via SMTP (Gmail/SendGrid/Mailgun)
</code></pre><hr><p><em>ServerRoot.net v2.0.0-Enterprise — Generated April 2026</em></p>