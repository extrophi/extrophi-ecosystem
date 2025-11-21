"""
A10:2021 - Server-Side Request Forgery (SSRF)
URL validation to prevent SSRF attacks
"""

import ipaddress
import socket
from typing import List
from urllib.parse import urlparse

from fastapi import HTTPException, status


class SSRFProtection:
    """
    Prevent Server-Side Request Forgery (SSRF) attacks.

    Blocks requests to:
    - Private IP ranges (RFC 1918, RFC 4193)
    - Loopback addresses (127.0.0.0/8, ::1)
    - Link-local addresses (169.254.0.0/16, fe80::/10)
    - Cloud metadata services (169.254.169.254, fd00:ec2::254)
    """

    # Blocked IPv4 and IPv6 networks
    BLOCKED_NETWORKS: List[ipaddress.ip_network] = [
        # IPv4 Private ranges (RFC 1918)
        ipaddress.ip_network("10.0.0.0/8"),  # Class A private
        ipaddress.ip_network("172.16.0.0/12"),  # Class B private
        ipaddress.ip_network("192.168.0.0/16"),  # Class C private
        # IPv4 Loopback
        ipaddress.ip_network("127.0.0.0/8"),
        # IPv4 Link-local
        ipaddress.ip_network("169.254.0.0/16"),
        # IPv4 Multicast
        ipaddress.ip_network("224.0.0.0/4"),
        # IPv6 Loopback
        ipaddress.ip_network("::1/128"),
        # IPv6 Private (RFC 4193)
        ipaddress.ip_network("fc00::/7"),
        # IPv6 Link-local
        ipaddress.ip_network("fe80::/10"),
        # IPv6 Multicast
        ipaddress.ip_network("ff00::/8"),
    ]

    # Allowed schemes
    ALLOWED_SCHEMES = ["http", "https"]

    # Blocked ports (common internal services)
    BLOCKED_PORTS = [
        22,  # SSH
        23,  # Telnet
        25,  # SMTP
        3306,  # MySQL
        5432,  # PostgreSQL
        6379,  # Redis
        27017,  # MongoDB
        9200,  # Elasticsearch
    ]

    @classmethod
    def validate_url(cls, url: str, allow_private: bool = False) -> str:
        """
        Validate URL to prevent SSRF attacks.

        Args:
            url: URL to validate
            allow_private: If True, allows private IP ranges (use with caution)

        Returns:
            str: Validated URL

        Raises:
            HTTPException: If URL is invalid or potentially dangerous

        Example:
            >>> SSRFProtection.validate_url("https://example.com")
            'https://example.com'
            >>> SSRFProtection.validate_url("http://127.0.0.1/admin")
            HTTPException: Access to private networks not allowed
        """
        try:
            parsed = urlparse(url)

            # Check scheme
            if parsed.scheme not in cls.ALLOWED_SCHEMES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid URL scheme. Only {', '.join(cls.ALLOWED_SCHEMES)} allowed.",
                )

            # Check hostname exists
            if not parsed.hostname:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="URL must include a hostname",
                )

            # Resolve hostname to IP
            try:
                ip_str = socket.gethostbyname(parsed.hostname)
                ip = ipaddress.ip_address(ip_str)
            except socket.gaierror:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot resolve hostname: {parsed.hostname}",
                )
            except ValueError:
                # Hostname might already be an IP
                try:
                    ip = ipaddress.ip_address(parsed.hostname)
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid hostname or IP: {parsed.hostname}",
                    )

            # Check if IP is in blocked ranges (unless explicitly allowed)
            if not allow_private:
                for network in cls.BLOCKED_NETWORKS:
                    if ip in network:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Access to private/internal networks not allowed: {ip}",
                        )

            # Check for cloud metadata services (critical for cloud environments)
            if str(ip) in ["169.254.169.254", "fd00:ec2::254"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Access to cloud metadata services is not allowed",
                )

            # Check port if specified
            if parsed.port and parsed.port in cls.BLOCKED_PORTS:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Access to port {parsed.port} is not allowed",
                )

            return url

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid URL: {str(e)}",
            )

    @classmethod
    def is_safe_ip(cls, ip_str: str) -> bool:
        """
        Check if IP address is safe (not in blocked ranges).

        Args:
            ip_str: IP address string

        Returns:
            bool: True if safe, False if blocked
        """
        try:
            ip = ipaddress.ip_address(ip_str)

            # Check blocked ranges
            for network in cls.BLOCKED_NETWORKS:
                if ip in network:
                    return False

            # Check cloud metadata
            if str(ip) in ["169.254.169.254", "fd00:ec2::254"]:
                return False

            return True

        except ValueError:
            return False

    @classmethod
    def validate_redirect_url(cls, url: str, base_url: str) -> str:
        """
        Validate redirect URL (stricter than regular URL validation).

        Args:
            url: Redirect URL to validate
            base_url: Base URL to compare against

        Returns:
            str: Validated URL

        Raises:
            HTTPException: If redirect is invalid or potentially dangerous
        """
        # First, apply standard SSRF validation
        validated_url = cls.validate_url(url)

        # Parse both URLs
        parsed_redirect = urlparse(validated_url)
        parsed_base = urlparse(base_url)

        # Ensure redirect is to same domain (or subdomain)
        if not parsed_redirect.hostname.endswith(parsed_base.hostname):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Redirect to external domain not allowed",
            )

        return validated_url
