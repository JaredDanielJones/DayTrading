#!/usr/bin/env python3
"""
Simple test script to verify the trading bot can be imported and basic functions work
"""

import sys
import os

# Add the parent directory to the path so we can import trading_bot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_import():
    """Test that the trading bot can be imported"""
    try:
        import trading_bot
        print("✅ Successfully imported trading_bot module")
        return True
    except ImportError as e:
        print(f"❌ Failed to import trading_bot: {e}")
        return False

def test_class_instantiation():
    """Test that the bot class can be instantiated with dummy credentials"""
    try:
        # Set dummy environment variables for testing
        os.environ['ALPACA_API_KEY'] = 'test_key'
        os.environ['ALPACA_SECRET_KEY'] = 'test_secret'
        
        from trading_bot import SimpleMovingAverageBot
        
        # Note: This will fail to connect to Alpaca with dummy credentials,
        # but we're just testing that the class can be instantiated
        try:
            bot = SimpleMovingAverageBot()
            print("⚠️  Bot instantiated but will fail without real credentials")
        except Exception as e:
            if "authentication" in str(e).lower() or "key" in str(e).lower():
                print("✅ Bot class instantiation works (auth error expected with test credentials)")
                return True
            else:
                print(f"❌ Unexpected error during bot instantiation: {e}")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to instantiate bot class: {e}")
        return False

def test_dependencies():
    """Test that all required dependencies are available"""
    required_modules = ['pandas', 'numpy', 'alpaca_trade_api', 'dotenv']
    success = True
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} is available")
        except ImportError:
            print(f"❌ {module} is not available")
            success = False
    
    return success

def main():
    """Run all tests"""
    print("Running trading bot tests...")
    print("=" * 40)
    
    tests = [
        ("Dependencies", test_dependencies),
        ("Import", test_import),
        ("Class Instantiation", test_class_instantiation),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nTesting {test_name}:")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 40)
    print("Test Results:")
    all_passed = True
    for test_name, result in results:
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
        if not result:
            all_passed = False
    
    if all_passed:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print("\n❌ Some tests failed.")
        return 1

if __name__ == "__main__":
    exit(main())