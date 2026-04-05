#!/usr/bin/env python3
"""
ServerRoot.net - C2 Server Launcher
Central Command and Control server
"""
import sys
import os
import time
import signal
sys.path.insert(0, '/workspace')

from c2.server import C2Server
import logging

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - C2 - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/c2_server.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def signal_handler(sig, frame):
    logger.info("C2 Server shutting down...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

if __name__ == "__main__":
    print("=" * 60)
    print("  SERVERROOT.NET - C2 SERVER")
    print("  Central Command and Control")
    print("=" * 60)
    
    server = C2Server(host="0.0.0.0", port=8443, db_path="data/c2_database.db")
    print(f"[*] C2 Server starting on 0.0.0.0:8443")
    server.start()
    
    logger.info("C2 Server running — press Ctrl+C to stop")
    
    # Keep main thread alive so daemon threads stay running
    while True:
        time.sleep(10)
        if not server.active:
            logger.warning("C2 server went inactive, restarting...")
            server.start()