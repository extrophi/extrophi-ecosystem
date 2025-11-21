"""
A09:2021 - Security Logging and Monitoring Failures
Security audit logging for tracking security-relevant events
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Create logs directory if it doesn't exist
LOGS_DIR = Path(__file__).parent.parent.parent / "backend" / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure security audit logger
security_logger = logging.getLogger("security_audit")
security_logger.setLevel(logging.INFO)

# File handler for security logs
handler = logging.FileHandler(LOGS_DIR / "security_audit.log")
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
security_logger.addHandler(handler)

# Also log to console in development
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
security_logger.addHandler(console_handler)


class AuditLogger:
    """
    Log security-relevant events for monitoring and compliance.

    Events logged:
    - Authentication attempts (success/failure)
    - Authorization failures
    - Suspicious activity
    - Data access patterns
    - Configuration changes
    """

    @staticmethod
    def log_authentication_attempt(
        username: str,
        success: bool,
        ip_address: str,
        user_agent: str = "",
        additional_info: Optional[Dict] = None,
    ):
        """
        Log authentication attempts (login, API key usage).

        Args:
            username: Username or user ID attempting authentication
            success: Whether authentication succeeded
            ip_address: Client IP address
            user_agent: Client user agent string
            additional_info: Additional context (e.g., failure reason)
        """
        event = {
            "event_type": "authentication",
            "username": username,
            "success": success,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "timestamp": datetime.utcnow().isoformat(),
            "additional_info": additional_info or {},
        }

        if success:
            security_logger.info(f"Authentication successful: {json.dumps(event)}")
        else:
            security_logger.warning(f"Authentication failed: {json.dumps(event)}")

    @staticmethod
    def log_authorization_failure(
        username: str, resource: str, action: str, ip_address: str, reason: str = ""
    ):
        """
        Log authorization failures (permission denied).

        Args:
            username: Username or user ID
            resource: Resource being accessed
            action: Action attempted (read, write, delete)
            ip_address: Client IP address
            reason: Reason for denial
        """
        event = {
            "event_type": "authorization_failure",
            "username": username,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "reason": reason,
            "timestamp": datetime.utcnow().isoformat(),
        }

        security_logger.warning(f"Authorization denied: {json.dumps(event)}")

    @staticmethod
    def log_suspicious_activity(
        description: str, ip_address: str, details: Dict[str, Any], severity: str = "high"
    ):
        """
        Log suspicious activity (rate limit exceeded, SQL injection attempt, etc.).

        Args:
            description: Description of suspicious activity
            ip_address: Client IP address
            details: Additional details about the activity
            severity: Severity level (low, medium, high, critical)
        """
        event = {
            "event_type": "suspicious_activity",
            "description": description,
            "ip_address": ip_address,
            "severity": severity,
            "details": details,
            "timestamp": datetime.utcnow().isoformat(),
        }

        if severity in ["high", "critical"]:
            security_logger.error(f"Suspicious activity detected: {json.dumps(event)}")
        else:
            security_logger.warning(f"Suspicious activity detected: {json.dumps(event)}")

    @staticmethod
    def log_data_access(
        username: str,
        resource: str,
        action: str,
        ip_address: str,
        record_count: int = 1,
        success: bool = True,
    ):
        """
        Log data access for audit trail.

        Args:
            username: Username or user ID
            resource: Resource accessed (table name, file path)
            action: Action performed (read, write, delete)
            ip_address: Client IP address
            record_count: Number of records accessed
            success: Whether access was successful
        """
        event = {
            "event_type": "data_access",
            "username": username,
            "resource": resource,
            "action": action,
            "ip_address": ip_address,
            "record_count": record_count,
            "success": success,
            "timestamp": datetime.utcnow().isoformat(),
        }

        security_logger.info(f"Data access: {json.dumps(event)}")

    @staticmethod
    def log_configuration_change(
        username: str,
        setting: str,
        old_value: Any,
        new_value: Any,
        ip_address: str,
    ):
        """
        Log configuration changes for audit trail.

        Args:
            username: Username or user ID making change
            setting: Setting name/path
            old_value: Previous value
            new_value: New value
            ip_address: Client IP address
        """
        event = {
            "event_type": "configuration_change",
            "username": username,
            "setting": setting,
            "old_value": str(old_value),
            "new_value": str(new_value),
            "ip_address": ip_address,
            "timestamp": datetime.utcnow().isoformat(),
        }

        security_logger.info(f"Configuration changed: {json.dumps(event)}")

    @staticmethod
    def log_security_event(
        event_type: str,
        description: str,
        severity: str = "info",
        details: Optional[Dict] = None,
    ):
        """
        Log generic security event.

        Args:
            event_type: Type of security event
            description: Event description
            severity: Severity level (info, warning, error, critical)
            details: Additional event details
        """
        event = {
            "event_type": event_type,
            "description": description,
            "severity": severity,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        log_message = f"Security event: {json.dumps(event)}"

        if severity == "critical":
            security_logger.critical(log_message)
        elif severity == "error":
            security_logger.error(log_message)
        elif severity == "warning":
            security_logger.warning(log_message)
        else:
            security_logger.info(log_message)

    @staticmethod
    def log_rate_limit_exceeded(ip_address: str, endpoint: str, limit: int):
        """
        Log rate limit violations.

        Args:
            ip_address: Client IP address
            endpoint: API endpoint
            limit: Rate limit that was exceeded
        """
        AuditLogger.log_suspicious_activity(
            description="Rate limit exceeded",
            ip_address=ip_address,
            details={"endpoint": endpoint, "limit": limit},
            severity="medium",
        )

    @staticmethod
    def log_injection_attempt(
        ip_address: str, injection_type: str, payload: str, endpoint: str
    ):
        """
        Log injection attack attempts.

        Args:
            ip_address: Client IP address
            injection_type: Type of injection (SQL, XSS, Command)
            payload: Attack payload (sanitized for logging)
            endpoint: Targeted endpoint
        """
        AuditLogger.log_suspicious_activity(
            description=f"{injection_type} injection attempt",
            ip_address=ip_address,
            details={
                "injection_type": injection_type,
                "payload": payload[:200],  # Truncate for safety
                "endpoint": endpoint,
            },
            severity="high",
        )
