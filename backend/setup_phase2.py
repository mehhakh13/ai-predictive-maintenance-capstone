#!/usr/bin/env python3
"""
Setup verification script for Phase 2
Checks all dependencies and configuration
"""
import os
import sys
from pathlib import Path

def check_mark(condition, message):
    """Print check mark or X based on condition"""
    symbol = "✓" if condition else "✗"
    status = "OK" if condition else "FAIL"
    print(f"{symbol} [{status}] {message}")
    return condition

def check_dependencies():
    """Check if required packages are installed"""
    print("\n📦 Checking Dependencies...")

    required_packages = [
        "anthropic",
        "fastapi",
        "uvicorn",
        "pydantic",
        "pandas"
    ]

    all_installed = True
    for package in required_packages:
        try:
            __import__(package)
            check_mark(True, f"{package} installed")
        except ImportError:
            check_mark(False, f"{package} NOT installed")
            all_installed = False

    return all_installed

def check_environment():
    """Check environment variables"""
    print("\n🔐 Checking Environment Variables...")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    has_key = api_key is not None and len(api_key) > 0

    check_mark(has_key, "ANTHROPIC_API_KEY is set")

    if not has_key:
        print("\n⚠️  Set your API key:")
        print("   export ANTHROPIC_API_KEY='your-key-here'")
        print("   OR create a .env file with:")
        print("   ANTHROPIC_API_KEY=your-key-here")

    return has_key

def check_data_files():
    """Check if data files exist"""
    print("\n📁 Checking Data Files...")

    base_dir = Path(__file__).parent.parent

    files_to_check = [
        base_dir / "data" / "processed" / "predictions_with_metadata.parquet",
        base_dir / "models" / "xgboost_upm_predictor.pkl",
        base_dir / "models" / "feature_importance.csv",
    ]

    all_exist = True
    for file_path in files_to_check:
        exists = file_path.exists()
        check_mark(exists, f"{file_path.name}")
        if not exists:
            all_exist = False

    return all_exist

def check_services():
    """Check if services can be initialized"""
    print("\n⚙️  Checking Services...")

    try:
        # Add parent directory to path
        sys.path.insert(0, str(Path(__file__).parent))

        from services.data_service import get_data_service
        data_service = get_data_service()
        check_mark(True, "Data Service initialized")

        from services.session_manager import get_session_manager
        session_manager = get_session_manager()
        check_mark(True, "Session Manager initialized")

        # Only try to initialize LLM service if API key is present
        if os.getenv("ANTHROPIC_API_KEY"):
            from services.llm_service import get_llm_service
            llm_service = get_llm_service()
            check_mark(True, f"LLM Service initialized ({len(llm_service.tools)} tools)")
        else:
            check_mark(False, "LLM Service (requires API key)")
            return False

        return True
    except Exception as e:
        check_mark(False, f"Service initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def check_tools():
    """Check if all tool modules exist"""
    print("\n🛠️  Checking Tools...")

    base_dir = Path(__file__).parent
    tools_dir = base_dir / "tools"

    tool_files = [
        "cost_tools.py",
        "risk_tools.py",
        "building_tools.py",
        "trend_tools.py"
    ]

    all_exist = True
    for tool_file in tool_files:
        exists = (tools_dir / tool_file).exists()
        check_mark(exists, tool_file)
        if not exists:
            all_exist = False

    return all_exist

def print_summary(checks):
    """Print summary of all checks"""
    print("\n" + "="*60)
    print("SETUP VERIFICATION SUMMARY")
    print("="*60)

    all_passed = all(checks.values())

    for name, passed in checks.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status} - {name}")

    print("="*60)

    if all_passed:
        print("\n✅ All checks passed! Ready to run Phase 2.")
        print("\nTo start the server:")
        print("  cd backend")
        print("  python main.py")
        print("\nTo run tests:")
        print("  python backend/test_chat_phase2.py")
    else:
        print("\n❌ Some checks failed. Please fix the issues above.")

    print()

def main():
    """Run all checks"""
    print("\n" + "="*60)
    print("PHASE 2 SETUP VERIFICATION")
    print("="*60)

    checks = {
        "Dependencies": check_dependencies(),
        "Environment Variables": check_environment(),
        "Data Files": check_data_files(),
        "Tools": check_tools(),
        "Services": check_services()
    }

    print_summary(checks)

if __name__ == "__main__":
    main()
