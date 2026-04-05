"""
Check MonitoringSystem interface
"""

import sys
sys.path.insert(0, '/workspace')

from agent.monitoring_system import MonitoringSystem

# Create instance
monitoring = MonitoringSystem(agent_id="test", c2_server="localhost")

# List all methods
print("MonitoringSystem methods:")
for method in dir(monitoring):
    if not method.startswith('_'):
        print(f"  - {method}")

# Check for callback methods
print("\nChecking for callback registration methods:")
print(f"  register_health_callback: {hasattr(monitoring, 'register_health_callback')}")
print(f"  register_alert_callback: {hasattr(monitoring, 'register_alert_callback')}")
print(f"  register_callback: {hasattr(monitoring, 'register_callback')}")
print(f"  add_callback: {hasattr(monitoring, 'add_callback')}")
print(f"  set_callback: {hasattr(monitoring, 'set_callback')}")

# Check for methods that might be related
print("\nHealth-related methods:")
for method in dir(monitoring):
    if 'health' in method.lower() and not method.startswith('_'):
        print(f"  - {method}")

print("\nAlert-related methods:")
for method in dir(monitoring):
    if 'alert' in method.lower() and not method.startswith('_'):
        print(f"  - {method}")