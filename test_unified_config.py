"""
Test suite for Unified Configuration Manager
"""

import sys
import json
import time
import os
sys.path.insert(0, '/workspace')

from agent.unified_config import UnifiedConfig

def test_config_creation():
    """Test 1: Configuration creation"""
    print("Test 1: Configuration creation...")
    
    config = UnifiedConfig("test_config.json")
    
    assert config is not None
    assert config.validate_config()
    
    print("✅ Test 1 PASSED: Config manager created")
    return True

def test_get_set_values():
    """Test 2: Get and set values"""
    print("\nTest 2: Get and set values...")
    
    config = UnifiedConfig("test_config.json")
    
    # Test get with default
    value = config.get("nonexistent.key", "default_value")
    assert value == "default_value"
    
    # Test get existing value
    c2_server = config.get("system.c2_server")
    assert c2_server == "localhost"
    
    # Test set value with save=True
    config.set("system.c2_port", 9999, save=True)
    assert config.get("system.c2_port") == 9999
    
    config.stop_monitoring()
    
    print("✅ Test 2 PASSED: Get and set working")
    return True

def test_hot_reload():
    """Test 3: Hot reload functionality"""
    print("\nTest 3: Hot reload functionality...")
    
    config = UnifiedConfig("test_config.json")
    
    # Modify file externally
    test_value = f"test_{int(time.time())}"
    with open("test_config.json", 'r') as f:
        data = json.load(f)
    
    data['system']['test_field'] = test_value
    
    with open("test_config.json", 'w') as f:
        json.dump(data, f)
    
    # Manually trigger reload
    config.reload_config()
    
    # Check if value was loaded
    assert config.get("system.test_field") == test_value
    
    config.stop_monitoring()
    
    print("✅ Test 3 PASSED: Hot reload working")
    return True

def test_callbacks():
    """Test 4: Configuration callbacks"""
    print("\nTest 4: Configuration callbacks...")
    
    config = UnifiedConfig("test_config.json")
    
    callback_called = [False]
    
    def test_callback(config_data):
        callback_called[0] = True
    
    config.register_callback(test_callback)
    
    # Manually trigger callback notification
    config._notify_callbacks()
    
    assert callback_called[0]
    
    config.stop_monitoring()
    
    print("✅ Test 4 PASSED: Callbacks working")
    return True

def test_config_validation():
    """Test 5: Configuration validation"""
    print("\nTest 5: Configuration validation...")
    
    config = UnifiedConfig("test_config.json")
    
    assert config.validate_config()
    
    summary = config.get_config_summary()
    assert 'config_file' in summary
    assert 'valid' in summary
    assert summary['valid'] == True
    
    config.stop_monitoring()
    
    print("✅ Test 5 PASSED: Validation working")
    return True

def cleanup():
    """Clean up test files"""
    try:
        os.remove("test_config.json")
    except:
        pass

def main():
    """Run all tests"""
    print("=" * 60)
    print("🧪 Unified Configuration Manager - Integration Tests")
    print("=" * 60)
    
    tests = [
        test_config_creation,
        test_get_set_values,
        test_hot_reload,
        test_callbacks,
        test_config_validation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            result = test()
            if result:
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ FAILED: {test.__name__}")
            print(f"   Error: {str(e)}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    # Cleanup
    cleanup()
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed}/{len(tests)} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n🎉 All tests passed! Unified Config is ready.\n")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review.\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())