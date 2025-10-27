"""
WhatsApp Integration Setup Verification Script
Checks if all components are properly configured
"""

import sys
import json
from pathlib import Path


def print_header(text):
    """Print formatted header"""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)


def print_check(passed, message):
    """Print check result"""
    symbol = "✓" if passed else "✗"
    status = "OK" if passed else "FAIL"
    print(f"[{symbol}] {message:<50} [{status}]")
    return passed


def check_file_exists(filepath):
    """Check if file exists"""
    return Path(filepath).exists()


def check_dependencies():
    """Check if required Python packages are installed"""
    print_header("Checking Dependencies")
    
    required_packages = [
        ('fastapi', 'FastAPI'),
        ('uvicorn', 'Uvicorn'),
        ('twilio', 'Twilio SDK'),
        ('neo4j', 'Neo4j Driver'),
        ('langchain_mistralai', 'LangChain Mistral'),
    ]
    
    all_ok = True
    for package, name in required_packages:
        try:
            __import__(package)
            print_check(True, f"{name} installed")
        except ImportError:
            print_check(False, f"{name} missing")
            all_ok = False
    
    return all_ok


def check_files():
    """Check if all required files exist"""
    print_header("Checking Files")
    
    required_files = [
        'config/config.json',
        'src/whatsapp/whatsapp_agent.py',
        'src/whatsapp/twilio_client.py',
        'src/whatsapp/conversation_manager.py',
        'run_whatsapp_agent.py',
        'requirements_whatsapp.txt',
        'docs/TWILIO_SETUP_GUIDE.md',
    ]
    
    all_ok = True
    for filepath in required_files:
        exists = check_file_exists(filepath)
        print_check(exists, f"{filepath}")
        all_ok = all_ok and exists
    
    return all_ok


def check_config():
    """Check configuration file"""
    print_header("Checking Configuration")
    
    try:
        with open('config/config.json', 'r') as f:
            config = json.load(f)
        
        all_ok = True
        
        # Check Twilio config
        twilio = config.get('twilio', {})
        has_sid = bool(twilio.get('account_sid', ''))
        has_token = bool(twilio.get('auth_token', ''))
        has_number = bool(twilio.get('whatsapp_number', ''))
        
        print_check(has_sid, "Twilio Account SID configured")
        print_check(has_token, "Twilio Auth Token configured")
        print_check(has_number, "Twilio WhatsApp number configured")
        
        all_ok = all_ok and has_sid and has_token and has_number
        
        # Check Neo4j config
        neo4j = config.get('neo4j', {})
        has_uri = bool(neo4j.get('uri', ''))
        has_user = bool(neo4j.get('user', ''))
        has_password = bool(neo4j.get('password', ''))
        
        print_check(has_uri, "Neo4j URI configured")
        print_check(has_user, "Neo4j user configured")
        print_check(has_password, "Neo4j password configured")
        
        all_ok = all_ok and has_uri and has_user and has_password
        
        # Check Mistral config
        mistral = config.get('mistral', {})
        has_api_key = bool(mistral.get('api_key', ''))
        
        print_check(has_api_key, "Mistral API key configured")
        
        all_ok = all_ok and has_api_key
        
        # Check WhatsApp config
        whatsapp = config.get('whatsapp', {})
        print_check('max_conversation_history' in whatsapp, "WhatsApp settings configured")
        
        return all_ok
        
    except FileNotFoundError:
        print_check(False, "config/config.json not found")
        return False
    except json.JSONDecodeError:
        print_check(False, "config/config.json is not valid JSON")
        return False


def check_server_can_start():
    """Check if server can be imported"""
    print_header("Checking Server")
    
    try:
        from src.whatsapp.whatsapp_agent import create_app
        print_check(True, "WhatsApp agent can be imported")
        return True
    except ImportError as e:
        print_check(False, f"Import error: {e}")
        return False


def main():
    """Run all checks"""
    print_header("WhatsApp Integration Setup Verification")
    print("\nThis script checks if your WhatsApp bot is properly configured.")
    
    results = []
    
    # Run checks
    results.append(("Dependencies", check_dependencies()))
    results.append(("Files", check_files()))
    results.append(("Configuration", check_config()))
    results.append(("Server Import", check_server_can_start()))
    
    # Summary
    print_header("Summary")
    
    all_passed = all(passed for _, passed in results)
    
    for name, passed in results:
        print_check(passed, name)
    
    print("\n" + "="*70)
    
    if all_passed:
        print("✓ All checks passed! Your WhatsApp bot is ready to run.")
        print("\nNext steps:")
        print("1. Run: python run_whatsapp_agent.py")
        print("2. In another terminal: ngrok http 8000")
        print("3. Configure webhook URL in Twilio Console")
        print("4. Test by sending: @agent test message")
        print("\nSee docs/TWILIO_SETUP_GUIDE.md for detailed instructions.")
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        print("\nCommon fixes:")
        print("- Install dependencies: pip install -r requirements_whatsapp.txt")
        print("- Update config/config.json with your Twilio credentials")
        print("- See docs/TWILIO_SETUP_GUIDE.md for setup instructions")
    
    print("="*70 + "\n")
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())

