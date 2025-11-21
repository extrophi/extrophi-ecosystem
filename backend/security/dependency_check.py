"""
A06:2021 - Vulnerable and Outdated Components
Dependency vulnerability checking and monitoring
"""

import json
import subprocess
from typing import Dict, List


class DependencyChecker:
    """Check for vulnerable and outdated Python dependencies."""

    @staticmethod
    def check_vulnerabilities() -> List[Dict]:
        """
        Check for known vulnerabilities in dependencies using safety.

        Returns:
            List[Dict]: List of vulnerabilities found

        Note:
            Requires 'safety' package: pip install safety
        """
        try:
            # Run safety check
            result = subprocess.run(
                ["safety", "check", "--json", "--output", "json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.stdout:
                vulnerabilities = json.loads(result.stdout)
                return vulnerabilities if isinstance(vulnerabilities, list) else []

            return []

        except subprocess.TimeoutExpired:
            print("Safety check timed out")
            return []
        except FileNotFoundError:
            print(
                "Safety not installed. Install with: pip install safety\n"
                "Or use pip-audit as alternative: pip install pip-audit"
            )
            return []
        except json.JSONDecodeError:
            print(f"Failed to parse safety output: {result.stdout}")
            return []
        except Exception as e:
            print(f"Dependency check failed: {e}")
            return []

    @staticmethod
    def check_outdated_packages() -> List[Dict]:
        """
        Check for outdated packages.

        Returns:
            List[Dict]: List of outdated packages with version info
        """
        try:
            result = subprocess.run(
                ["pip", "list", "--outdated", "--format=json"],
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0 and result.stdout:
                outdated = json.loads(result.stdout)
                return outdated

            return []

        except subprocess.TimeoutExpired:
            print("Outdated packages check timed out")
            return []
        except json.JSONDecodeError:
            print(f"Failed to parse pip output: {result.stdout}")
            return []
        except Exception as e:
            print(f"Outdated package check failed: {e}")
            return []

    @staticmethod
    def check_with_pip_audit() -> List[Dict]:
        """
        Check vulnerabilities using pip-audit (alternative to safety).

        Returns:
            List[Dict]: List of vulnerabilities

        Note:
            Requires 'pip-audit' package: pip install pip-audit
        """
        try:
            result = subprocess.run(
                ["pip-audit", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.stdout:
                audit_results = json.loads(result.stdout)
                return audit_results.get("dependencies", [])

            return []

        except subprocess.TimeoutExpired:
            print("pip-audit check timed out")
            return []
        except FileNotFoundError:
            print("pip-audit not installed. Install with: pip install pip-audit")
            return []
        except json.JSONDecodeError:
            print(f"Failed to parse pip-audit output: {result.stdout}")
            return []
        except Exception as e:
            print(f"pip-audit check failed: {e}")
            return []

    @staticmethod
    def generate_security_report() -> Dict:
        """
        Generate comprehensive security report.

        Returns:
            Dict: Security report with vulnerabilities and outdated packages
        """
        report = {
            "vulnerabilities": [],
            "outdated_packages": [],
            "summary": {"total_vulnerabilities": 0, "total_outdated": 0, "status": "unknown"},
        }

        # Check vulnerabilities (try both safety and pip-audit)
        vulnerabilities = DependencyChecker.check_vulnerabilities()
        if not vulnerabilities:
            vulnerabilities = DependencyChecker.check_with_pip_audit()

        report["vulnerabilities"] = vulnerabilities
        report["summary"]["total_vulnerabilities"] = len(vulnerabilities)

        # Check outdated packages
        outdated = DependencyChecker.check_outdated_packages()
        report["outdated_packages"] = outdated
        report["summary"]["total_outdated"] = len(outdated)

        # Determine status
        if report["summary"]["total_vulnerabilities"] == 0:
            report["summary"]["status"] = "secure"
        elif report["summary"]["total_vulnerabilities"] < 5:
            report["summary"]["status"] = "warning"
        else:
            report["summary"]["status"] = "critical"

        return report


def check_dependencies() -> Dict:
    """
    Convenience function to check dependencies.

    Returns:
        Dict: Security report
    """
    return DependencyChecker.generate_security_report()
