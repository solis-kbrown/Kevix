#!/usr/bin/env python3
"""
ServerRoot.net - C2 Server Launcher
Central Command and Control server
"""
import sys
import os
sys.path.insert(0, '/workspace')

from c2.server import C2Server
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - C2 - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/c2_server.log'),
        logging.StreamHandler()
    ]
)

if __name__ == "__main__":
    print("=" * 60)
    print("  SERVERROOT.NET - C2 SERVER")
    print("  Central Command and Control")
    print("=" * 60)
    
    server = C2Server(host="0.0.0.0", port=8443, db_path="data/c2_database.db")
    print(f"[*] C2 Server starting on 0.0.0.0:8443")
    server.start()