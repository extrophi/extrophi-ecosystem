"""Service Registry Module for Dynamic Service Discovery.

This module provides Consul-based service registry and discovery capabilities
for the Extrophi ecosystem.
"""

from orchestrator.registry.service_registry import ServiceRegistry
from orchestrator.registry.discovery_client import ServiceDiscoveryClient

__all__ = ["ServiceRegistry", "ServiceDiscoveryClient"]
