"""
Penetration Test Runner

Runs all security tests and generates a comprehensive report.

Usage:
    python test_runner.py <base_url> [api_key]

Example:
    python test_runner.py http://localhost:8000 extro_live_abc123...
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Import all test modules
# Add parent directory to path to allow imports
sys.path.insert(0, str(Path(__file__).parent))

# Import test classes (using the actual module names with underscores, but prefixed with numbers)
# We need to use importlib to import modules starting with numbers
import importlib.util

def load_test_module(filename, class_name):
    """Dynamically load a test module by filename"""
    spec = importlib.util.spec_from_file_location(filename.replace('.py', ''), Path(__file__).parent / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return getattr(module, class_name)

AuthBypassTests = load_test_module("01_auth_bypass.py", "AuthBypassTests")
RateLimitBypassTests = load_test_module("02_rate_limit_bypass.py", "RateLimitBypassTests")
TokenManipulationTests = load_test_module("03_token_manipulation.py", "TokenManipulationTests")
PrivilegeEscalationTests = load_test_module("04_privilege_escalation.py", "PrivilegeEscalationTests")
InputValidationTests = load_test_module("05_input_validation.py", "InputValidationTests")


class PentestRunner:
    """Main penetration test runner"""

    def __init__(self, base_url: str, api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.all_results = {}
        self.start_time = None
        self.end_time = None

    async def run_all_tests(self):
        """Run all penetration tests"""
        print("\n" + "=" * 70)
        print("  EXTROPHI ECOSYSTEM - SECURITY PENETRATION TEST SUITE")
        print("  SEC-BETA Agent - Comprehensive Security Assessment")
        print("=" * 70)
        print(f"\nTarget: {self.base_url}")
        print(f"API Key: {'Provided' if self.api_key else 'Not provided (some tests will skip)'}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\n" + "=" * 70)

        self.start_time = datetime.now()

        # 1. Authentication Bypass Tests
        print("\n\n[1/5] Running Authentication Bypass Tests...")
        auth_tester = AuthBypassTests(self.base_url)
        self.all_results["authentication_bypass"] = await auth_tester.run_all_tests()

        # 2. Rate Limit Bypass Tests
        print("\n\n[2/5] Running Rate Limit Bypass Tests...")
        rate_tester = RateLimitBypassTests(self.base_url, self.api_key)
        self.all_results["rate_limit_bypass"] = await rate_tester.run_all_tests()

        # 3. Token Manipulation Tests
        print("\n\n[3/5] Running Token Manipulation Tests...")
        token_tester = TokenManipulationTests(self.base_url, self.api_key)
        self.all_results["token_manipulation"] = await token_tester.run_all_tests()

        # 4. Privilege Escalation Tests
        print("\n\n[4/5] Running Privilege Escalation Tests...")
        priv_tester = PrivilegeEscalationTests(self.base_url, self.api_key)
        self.all_results["privilege_escalation"] = await priv_tester.run_all_tests()

        # 5. Input Validation Tests
        print("\n\n[5/5] Running Input Validation Tests...")
        input_tester = InputValidationTests(self.base_url, self.api_key)
        self.all_results["input_validation"] = await input_tester.run_all_tests()

        self.end_time = datetime.now()

        # Generate summary
        self.print_summary()

        # Save detailed JSON report
        self.save_json_report()

        # Return exit code
        return 0 if self.all_tests_passed() else 1

    def print_summary(self):
        """Print executive summary"""
        print("\n\n" + "=" * 70)
        print("  EXECUTIVE SUMMARY")
        print("=" * 70)

        total_passed = sum(r.get("passed", 0) for r in self.all_results.values())
        total_failed = sum(r.get("failed", 0) for r in self.all_results.values())
        total_skipped = sum(r.get("skipped", 0) for r in self.all_results.values())
        total_tests = total_passed + total_failed + total_skipped

        print(f"\nTotal Tests Run: {total_tests}")
        print(f"  ✅ Passed:  {total_passed}")
        print(f"  ❌ Failed:  {total_failed}")
        print(f"  ⚠️  Skipped: {total_skipped}")

        duration = (self.end_time - self.start_time).total_seconds()
        print(f"\nDuration: {duration:.2f} seconds")

        # Critical vulnerabilities
        critical_vulns = self.get_critical_vulnerabilities()
        if critical_vulns:
            print(f"\n🚨 CRITICAL VULNERABILITIES FOUND: {len(critical_vulns)}")
            for vuln in critical_vulns:
                print(f"  - {vuln['category']}: {vuln['test']}")
        else:
            print("\n✅ No critical vulnerabilities found")

        # High severity vulnerabilities
        high_vulns = self.get_high_severity_vulnerabilities()
        if high_vulns:
            print(f"\n⚠️  HIGH SEVERITY VULNERABILITIES: {len(high_vulns)}")
            for vuln in high_vulns:
                print(f"  - {vuln['category']}: {vuln['test']}")

        print("\n" + "=" * 70)
        print(f"\nDetailed report saved to: security/pentest-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json")
        print("=" * 70 + "\n")

    def get_critical_vulnerabilities(self):
        """Extract critical vulnerabilities"""
        critical = []
        for category, results in self.all_results.items():
            for detail in results.get("details", []):
                if detail.get("severity") == "CRITICAL" and detail.get("status") == "FAIL":
                    critical.append({"category": category, "test": detail.get("test")})
        return critical

    def get_high_severity_vulnerabilities(self):
        """Extract high severity vulnerabilities"""
        high = []
        for category, results in self.all_results.items():
            for detail in results.get("details", []):
                if detail.get("severity") == "HIGH" and detail.get("status") == "FAIL":
                    high.append({"category": category, "test": detail.get("test")})
        return high

    def all_tests_passed(self):
        """Check if all tests passed"""
        return all(r.get("failed", 1) == 0 for r in self.all_results.values())

    def save_json_report(self):
        """Save detailed JSON report"""
        report = {
            "test_suite": "Extrophi Ecosystem Security Penetration Test",
            "agent": "SEC-BETA",
            "target": self.base_url,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": (self.end_time - self.start_time).total_seconds(),
            "summary": {
                "total_passed": sum(r.get("passed", 0) for r in self.all_results.values()),
                "total_failed": sum(r.get("failed", 0) for r in self.all_results.values()),
                "total_skipped": sum(r.get("skipped", 0) for r in self.all_results.values()),
            },
            "critical_vulnerabilities": self.get_critical_vulnerabilities(),
            "high_vulnerabilities": self.get_high_severity_vulnerabilities(),
            "detailed_results": self.all_results,
        }

        filename = f"pentest-results-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        filepath = Path(__file__).parent.parent / filename

        with open(filepath, "w") as f:
            json.dump(report, f, indent=2, default=str)

        print(f"\n✅ JSON report saved to: {filepath}")


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_runner.py <base_url> [api_key]")
        print("Example: python test_runner.py http://localhost:8000 extro_live_abc123...")
        sys.exit(1)

    base_url = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None

    runner = PentestRunner(base_url, api_key)
    exit_code = await runner.run_all_tests()

    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
