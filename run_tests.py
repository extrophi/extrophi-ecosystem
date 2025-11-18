#!/usr/bin/env python3
"""
Comprehensive test runner for the Sovereign Backend.

This script runs different test suites with appropriate configurations
to ensure the system is bulletproof against all types of failures.
"""
from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Orchestrates test execution with different profiles."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.project_root = Path(__file__).parent
        self.start_time = time.time()
        self.results = {}
    
    def run_command(self, cmd: List[str], env: Optional[dict] = None) -> tuple[int, str, str]:
        """Run a command and capture output."""
        if self.verbose:
            print(f"Running: {' '.join(cmd)}")
        
        process_env = os.environ.copy()
        if env:
            process_env.update(env)
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=process_env,
            cwd=self.project_root,
        )
        
        return result.returncode, result.stdout, result.stderr
    
    def run_unit_tests(self) -> bool:
        """Run fast unit tests."""
        print("\n🧪 Running Unit Tests...")
        cmd = [
            "pytest",
            "-m", "unit",
            "--tb=short",
            "-q" if not self.verbose else "-v",
        ]
        
        returncode, stdout, stderr = self.run_command(cmd)
        self.results["unit"] = returncode == 0
        
        if returncode != 0:
            print(f"❌ Unit tests failed!\n{stderr}")
        else:
            print("✅ Unit tests passed!")
        
        return returncode == 0
    
    def run_integration_tests(self) -> bool:
        """Run integration tests."""
        print("\n🔌 Running Integration Tests...")
        
        # Check if services are available
        services_available = self.check_services()
        if not services_available:
            print("⚠️  Skipping integration tests - required services not available")
            return True
        
        cmd = [
            "pytest",
            "-m", "integration",
            "--tb=short",
            "-q" if not self.verbose else "-v",
        ]
        
        returncode, stdout, stderr = self.run_command(cmd)
        self.results["integration"] = returncode == 0
        
        if returncode != 0:
            print(f"❌ Integration tests failed!\n{stderr}")
        else:
            print("✅ Integration tests passed!")
        
        return returncode == 0
    
    def run_security_tests(self) -> bool:
        """Run security tests."""
        print("\n🔒 Running Security Tests...")
        cmd = [
            "pytest",
            "-m", "security",
            "--tb=short",
            "-q" if not self.verbose else "-v",
            "-x",  # Stop on first failure for security
        ]
        
        returncode, stdout, stderr = self.run_command(cmd)
        self.results["security"] = returncode == 0
        
        if returncode != 0:
            print(f"❌ Security tests failed! This is CRITICAL!\n{stderr}")
        else:
            print("✅ Security tests passed!")
        
        return returncode == 0
    
    def run_stress_tests(self, duration: int = 60) -> bool:
        """Run stress tests."""
        print(f"\n💪 Running Stress Tests (duration: {duration}s)...")
        cmd = [
            "pytest",
            "-m", "stress",
            "--tb=short",
            "-q" if not self.verbose else "-v",
            f"--timeout={duration + 30}",  # Add buffer for timeout
        ]
        
        env = {"STRESS_TEST_DURATION": str(duration)}
        
        returncode, stdout, stderr = self.run_command(cmd, env)
        self.results["stress"] = returncode == 0
        
        if returncode != 0:
            print(f"❌ Stress tests failed!\n{stderr}")
        else:
            print("✅ Stress tests passed!")
        
        return returncode == 0
    
    def run_chaos_tests(self) -> bool:
        """Run chaos engineering tests."""
        print("\n🌪️  Running Chaos Tests...")
        
        # Chaos tests are dangerous - confirm first
        if not self.confirm_dangerous_tests():
            print("⚠️  Skipping chaos tests")
            return True
        
        cmd = [
            "pytest",
            "-m", "chaos",
            "--tb=short",
            "-q" if not self.verbose else "-v",
        ]
        
        returncode, stdout, stderr = self.run_command(cmd)
        self.results["chaos"] = returncode == 0
        
        if returncode != 0:
            print(f"❌ Chaos tests failed!\n{stderr}")
        else:
            print("✅ Chaos tests passed! System is resilient!")
        
        return returncode == 0
    
    def run_coverage_report(self) -> None:
        """Generate coverage report."""
        print("\n📊 Generating Coverage Report...")
        cmd = ["pytest", "--cov=src", "--cov-report=html", "--cov-report=term"]
        
        returncode, stdout, stderr = self.run_command(cmd)
        
        if returncode == 0:
            print("✅ Coverage report generated in htmlcov/")
        else:
            print("❌ Failed to generate coverage report")
    
    def check_services(self) -> bool:
        """Check if required services are running."""
        services = {
            "PostgreSQL": "pg_isready",
            "Redis/Valkey": "redis-cli ping",
        }
        
        all_available = True
        for service, check_cmd in services.items():
            try:
                result = subprocess.run(
                    check_cmd.split(),
                    capture_output=True,
                    timeout=2,
                )
                if result.returncode != 0:
                    print(f"  ⚠️  {service} not available")
                    all_available = False
                else:
                    print(f"  ✅ {service} available")
            except Exception:
                print(f"  ⚠️  {service} check failed")
                all_available = False
        
        return all_available
    
    def confirm_dangerous_tests(self) -> bool:
        """Confirm before running dangerous tests."""
        response = input("\n⚠️  Chaos tests can be destructive. Run them? (y/N): ")
        return response.lower() == 'y'
    
    def print_summary(self) -> None:
        """Print test execution summary."""
        duration = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        for test_type, passed in self.results.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            print(f"{test_type.capitalize():15} {status}")
        
        print(f"\nTotal Duration: {duration:.2f} seconds")
        
        all_passed = all(self.results.values())
        if all_passed:
            print("\n🎉 ALL TESTS PASSED! The system is BULLETPROOF! 🛡️")
        else:
            print("\n❌ Some tests failed. Please fix before deployment!")
        
        return all_passed


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run comprehensive tests for Sovereign Backend"
    )
    parser.add_argument(
        "--suite",
        choices=["all", "unit", "integration", "security", "stress", "chaos"],
        default="all",
        help="Test suite to run",
    )
    parser.add_argument(
        "--stress-duration",
        type=int,
        default=60,
        help="Duration for stress tests in seconds",
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output",
    )
    parser.add_argument(
        "--coverage",
        action="store_true",
        help="Generate coverage report",
    )
    
    args = parser.parse_args()
    
    runner = TestRunner(verbose=args.verbose)
    
    print("🚀 Sovereign Backend Test Runner")
    print("================================")
    
    success = True
    
    if args.suite == "all":
        # Run all test suites in order
        success &= runner.run_unit_tests()
        if success:  # Only continue if unit tests pass
            success &= runner.run_security_tests()
        if success:  # Only continue if security tests pass
            success &= runner.run_integration_tests()
            success &= runner.run_stress_tests(args.stress_duration)
            # Chaos tests are optional
            runner.run_chaos_tests()
    elif args.suite == "unit":
        success = runner.run_unit_tests()
    elif args.suite == "integration":
        success = runner.run_integration_tests()
    elif args.suite == "security":
        success = runner.run_security_tests()
    elif args.suite == "stress":
        success = runner.run_stress_tests(args.stress_duration)
    elif args.suite == "chaos":
        success = runner.run_chaos_tests()
    
    if args.coverage:
        runner.run_coverage_report()
    
    runner.print_summary()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()