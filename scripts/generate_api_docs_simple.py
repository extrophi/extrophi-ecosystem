#!/usr/bin/env python3
"""
Simplified API Documentation Generator

Generates Mintlify-compatible API documentation from manually defined specs.
This approach avoids import issues with FastAPI apps that have database dependencies.

Usage:
    python scripts/generate_api_docs_simple.py
"""

import json
from pathlib import Path
from typing import Any, Dict, List


def get_api_spec() -> Dict[str, Any]:
    """
    Manually defined API specification based on codebase analysis.

    Returns:
        OpenAPI 3.0 specification
    """
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Extrophi Ecosystem API",
            "version": "1.0.0",
            "description": "Complete API documentation for the Extrophi Ecosystem including Content Intelligence, Token System, and Publishing Platform.",
        },
        "servers": [
            {
                "url": "https://api.extrophi.ai",
                "description": "Production server"
            },
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            }
        ],
        "paths": {
            "/health": {
                "get": {
                    "tags": ["Health"],
                    "summary": "Health Check",
                    "description": "Check application health status and component availability.",
                    "responses": {
                        "200": {
                            "description": "Service is healthy",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "healthy"},
                                            "version": {"type": "string", "example": "1.0.0"},
                                            "components": {
                                                "type": "object",
                                                "additionalProperties": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/scrape/{platform}": {
                "post": {
                    "tags": ["Scraping"],
                    "summary": "Scrape Content from Platform",
                    "description": "Scrape content from specified platform (twitter, youtube, reddit, web).",
                    "parameters": [
                        {
                            "name": "platform",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "enum": ["twitter", "youtube", "reddit", "web"]},
                            "description": "Platform to scrape from"
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["target"],
                                    "properties": {
                                        "target": {"type": "string", "description": "Target identifier (username, URL, etc.)", "example": "dankoe"},
                                        "limit": {"type": "integer", "description": "Maximum items to scrape", "default": 20, "example": 50}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Scraping completed successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "status": {"type": "string", "example": "success"},
                                            "platform": {"type": "string", "example": "twitter"},
                                            "target": {"type": "string", "example": "dankoe"},
                                            "count": {"type": "integer", "example": 50},
                                            "content_ids": {"type": "array", "items": {"type": "string"}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/analyze/content": {
                "post": {
                    "tags": ["Analysis"],
                    "summary": "Analyze Content with LLM",
                    "description": "Analyze single content piece with LLM to extract frameworks, hooks, themes, and pain points.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["content"],
                                    "properties": {
                                        "content": {"type": "string", "description": "Content text to analyze"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Analysis completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "frameworks": {"type": "array", "items": {"type": "string"}},
                                            "hooks": {"type": "array", "items": {"type": "string"}},
                                            "themes": {"type": "array", "items": {"type": "string"}},
                                            "pain_points": {"type": "array", "items": {"type": "string"}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/query/rag": {
                "post": {
                    "tags": ["RAG"],
                    "summary": "Semantic Search",
                    "description": "Perform semantic search across all content using vector embeddings.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["prompt"],
                                    "properties": {
                                        "prompt": {"type": "string", "description": "Natural language query"},
                                        "n_results": {"type": "integer", "default": 10, "description": "Number of results"},
                                        "platform_filter": {"type": "string", "description": "Filter by platform"},
                                        "author_filter": {"type": "string", "description": "Filter by author"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Search results",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "query": {"type": "string"},
                                            "count": {"type": "integer"},
                                            "results": {"type": "array", "items": {"type": "object"}}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/publish": {
                "post": {
                    "tags": ["Publishing"],
                    "summary": "Publish Cards",
                    "description": "Publish cards from Writer module with privacy filtering and $EXTROPY rewards.",
                    "security": [{"ApiKeyAuth": []}],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["cards"],
                                    "properties": {
                                        "cards": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "required": ["title", "body", "category", "privacy_level"],
                                                "properties": {
                                                    "title": {"type": "string", "example": "How to Build Momentum"},
                                                    "body": {"type": "string", "example": "The key to building momentum is..."},
                                                    "category": {"type": "string", "example": "BUSINESS"},
                                                    "privacy_level": {"type": "string", "enum": ["BUSINESS", "IDEAS", "PERSONAL", "PRIVATE"]},
                                                    "tags": {"type": "array", "items": {"type": "string"}}
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Publishing completed",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "published_urls": {"type": "array", "items": {"type": "string"}},
                                            "extropy_earned": {"type": "string", "example": "10.00000000"},
                                            "cards_published": {"type": "integer"},
                                            "cards_filtered": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/attributions": {
                "post": {
                    "tags": ["Attributions"],
                    "summary": "Create Attribution",
                    "description": "Create attribution and transfer $EXTROPY tokens. Supports citation (+0.1), remix (+0.5), and reply (+0.05).",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["source_card_id", "target_card_id", "attribution_type", "user_id"],
                                    "properties": {
                                        "source_card_id": {"type": "string", "format": "uuid"},
                                        "target_card_id": {"type": "string", "format": "uuid"},
                                        "attribution_type": {"type": "string", "enum": ["citation", "remix", "reply"]},
                                        "user_id": {"type": "string", "format": "uuid"},
                                        "context": {"type": "string"},
                                        "excerpt": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Attribution created successfully"
                        }
                    }
                }
            },
            "/attributions/{card_id}": {
                "get": {
                    "tags": ["Attributions"],
                    "summary": "Get Card Attributions",
                    "description": "Get all attributions for a card (backlinks showing who cited this card).",
                    "parameters": [
                        {
                            "name": "card_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "format": "uuid"}
                        },
                        {
                            "name": "limit",
                            "in": "query",
                            "schema": {"type": "integer", "default": 100}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Attribution list"
                        }
                    }
                }
            },
            "/tokens/balance/{user_id}": {
                "get": {
                    "tags": ["Tokens"],
                    "summary": "Get Token Balance",
                    "description": "Get current $EXTROPY token balance for a user.",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string", "format": "uuid"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Token balance",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "user_id": {"type": "string"},
                                            "balance": {"type": "string", "example": "125.50000000"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/tokens/transfer": {
                "post": {
                    "tags": ["Tokens"],
                    "summary": "Transfer Tokens",
                    "description": "Transfer $EXTROPY tokens between users.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["from_user_id", "to_user_id", "amount", "reason"],
                                    "properties": {
                                        "from_user_id": {"type": "string", "format": "uuid"},
                                        "to_user_id": {"type": "string", "format": "uuid"},
                                        "amount": {"type": "string", "example": "25.00000000"},
                                        "reason": {"type": "string"}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Transfer completed"
                        }
                    }
                }
            },
            "/api/enrich": {
                "post": {
                    "tags": ["Enrichment"],
                    "summary": "Enrich Card Content",
                    "description": "Enrich card content with AI-powered suggestions using RAG pipeline.",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "required": ["card_id", "content"],
                                    "properties": {
                                        "card_id": {"type": "string"},
                                        "content": {"type": "string", "description": "Card text to enrich"},
                                        "context": {"type": "string", "description": "Surrounding context"},
                                        "max_suggestions": {"type": "integer", "default": 5}
                                    }
                                }
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Enrichment suggestions",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "card_id": {"type": "string"},
                                            "suggestions": {"type": "array", "items": {"type": "object"}},
                                            "sources": {"type": "array", "items": {"type": "object"}},
                                            "processing_time_ms": {"type": "number"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        },
        "components": {
            "securitySchemes": {
                "ApiKeyAuth": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "Authorization"
                }
            }
        },
        "tags": [
            {"name": "Health", "description": "Health check endpoints"},
            {"name": "Scraping", "description": "Content scraping from multiple platforms"},
            {"name": "Analysis", "description": "LLM-powered content analysis"},
            {"name": "RAG", "description": "Semantic search and retrieval"},
            {"name": "Publishing", "description": "Card publishing with privacy controls"},
            {"name": "Attributions", "description": "Attribution system with token rewards"},
            {"name": "Tokens", "description": "$EXTROPY token operations"},
            {"name": "Enrichment", "description": "AI-powered content enrichment"}
        ]
    }


def generate_mintlify_page(path: str, method: str, operation: Dict[str, Any]) -> str:
    """Generate Mintlify markdown page for an endpoint."""

    title = operation.get("summary", f"{method.upper()} {path}")
    description = operation.get("description", "")
    tags = operation.get("tags", [])

    md = f"""---
title: "{title}"
api: "{method.upper()} {path}"
description: "{description[:100]}..."
---

## Overview

{description}

"""

    # Parameters
    params = operation.get("parameters", [])
    if params:
        md += "## Parameters\n\n"
        for param in params:
            name = param.get("name", "")
            required = "**Required**" if param.get("required") else "*Optional*"
            desc = param.get("description", "")
            param_type = param.get("schema", {}).get("type", "string")

            md += f"### `{name}` {required}\n\n"
            md += f"- **Type:** `{param_type}`\n"
            md += f"- **Location:** {param.get('in', 'query')}\n"
            if desc:
                md += f"- **Description:** {desc}\n"
            md += "\n"

    # Request body
    request_body = operation.get("requestBody", {})
    if request_body:
        md += "## Request Body\n\n"
        schema = request_body.get("content", {}).get("application/json", {}).get("schema", {})

        if "properties" in schema:
            md += "```json\n"
            example = {}
            for prop, prop_schema in schema["properties"].items():
                example[prop] = prop_schema.get("example", f"<{prop_schema.get('type', 'value')}>")
            md += json.dumps(example, indent=2)
            md += "\n```\n\n"

    # Code examples
    md += "## Code Examples\n\n"

    md += "### Python\n\n```python\n"
    md += f"""import requests

url = "https://api.extrophi.ai{path}"
headers = {{"Authorization": "Bearer YOUR_API_KEY"}}

response = requests.{method}(url, headers=headers"""

    if method in ["post", "put", "patch"]:
        md += ", json=data"

    md += """)
print(response.json())
```

"""

    md += "### cURL\n\n```bash\n"
    md += f"""curl -X {method.upper()} \\
  https://api.extrophi.ai{path} \\
  -H "Authorization: Bearer YOUR_API_KEY\""""

    if method in ["post", "put", "patch"]:
        md += """ \\
  -d '{"key": "value"}'"""

    md += "\n```\n\n"

    return md


def main():
    """Generate API documentation."""
    print("🚀 Generating API documentation...")

    # Get API spec
    spec = get_api_spec()

    # Save OpenAPI spec
    project_root = Path(__file__).parent.parent
    openapi_path = project_root / "docs" / "api" / "openapi.json"
    openapi_path.parent.mkdir(parents=True, exist_ok=True)

    with open(openapi_path, "w") as f:
        json.dump(spec, f, indent=2)

    print(f"✅ Saved OpenAPI spec to {openapi_path}")

    # Generate Mintlify pages
    print("📄 Generating Mintlify documentation pages...")
    endpoints_dir = project_root / "docs" / "api" / "endpoints"
    endpoints_dir.mkdir(parents=True, exist_ok=True)

    page_count = 0
    for path, methods in spec["paths"].items():
        for method, operation in methods.items():
            # Generate filename
            page_name = path.strip("/").replace("{", "").replace("}", "").replace("/", "-")
            if not page_name:
                page_name = "root"
            page_name = f"{method}-{page_name}.md"

            # Generate content
            content = generate_mintlify_page(path, method, operation)

            # Save page
            page_path = endpoints_dir / page_name
            with open(page_path, "w") as f:
                f.write(content)

            page_count += 1
            print(f"  ✓ {page_name}")

    print(f"\n✨ Successfully generated {page_count} documentation pages!")
    print(f"📂 Documentation saved to {endpoints_dir}")
    print("\n🎉 API documentation generation complete!")


if __name__ == "__main__":
    main()
