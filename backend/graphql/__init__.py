"""
GraphQL API Module

Provides GraphQL interface for Extrophi Ecosystem using Strawberry.

Exposes:
- Queries: card, user, searchCards, userBalance
- Mutations: publishCard, citeCard, remixCard, replyCard
- Nested queries with field resolvers
"""

from .schema import schema

__all__ = ["schema"]
