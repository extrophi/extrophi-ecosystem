#!/usr/bin/env python3
"""
API Documentation Generator

Extracts OpenAPI specifications from FastAPI applications and generates
Mintlify-compatible documentation pages with code examples.

Usage:
    python scripts/generate_api_docs.py

Generates:
    - docs/api/openapi.json - Combined OpenAPI specification
    - docs/api/endpoints/*.md - Mintlify documentation pages
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def extract_openapi_spec(app_path: str, app_name: str) -> Dict[str, Any]:
    """
    Extract OpenAPI specification from a FastAPI application.

    Args:
        app_path: Path to the main.py file
        app_name: Name of the FastAPI app variable

    Returns:
        OpenAPI specification as dict
    """
    import importlib.util
    import importlib.machinery

    try:
        # Mock database connections and dependencies
        import unittest.mock as mock

        # Import the app module
        spec = importlib.util.spec_from_file_location("app_module", app_path)
        module = importlib.util.module_from_spec(spec)

        # Execute module
        spec.loader.exec_module(module)

        # Get the FastAPI app instance
        app = getattr(module, app_name)

        # Generate OpenAPI spec
        return app.openapi()
    except Exception as e:
        print(f"    Error during spec extraction: {e}")
        raise


def merge_openapi_specs(specs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple OpenAPI specifications into a single spec.

    Args:
        specs: List of OpenAPI specifications

    Returns:
        Merged OpenAPI specification
    """
    if not specs:
        return {}

    # Start with the first spec as base
    merged = specs[0].copy()

    # Merge paths from other specs
    for spec in specs[1:]:
        if "paths" in spec:
            merged.setdefault("paths", {}).update(spec["paths"])
        if "components" in spec:
            for component_type, components in spec["components"].items():
                merged.setdefault("components", {}).setdefault(component_type, {}).update(components)
        if "tags" in spec:
            merged.setdefault("tags", []).extend(spec["tags"])

    # Update info
    merged["info"] = {
        "title": "Extrophi Ecosystem API",
        "version": "1.0.0",
        "description": "Complete API documentation for the Extrophi Ecosystem including BrainDump, Research Module, and Backend services.",
    }

    return merged


def generate_code_examples(method: str, path: str, operation: Dict[str, Any]) -> Dict[str, str]:
    """
    Generate code examples for an API endpoint.

    Args:
        method: HTTP method (GET, POST, etc.)
        path: API endpoint path
        operation: OpenAPI operation object

    Returns:
        Dict of code examples by language
    """
    # Extract request body schema if available
    request_body = operation.get("requestBody", {})
    request_schema = request_body.get("content", {}).get("application/json", {}).get("schema", {})

    # Generate example request body
    example_body = {}
    if "properties" in request_schema:
        for prop, prop_schema in request_schema["properties"].items():
            if "example" in prop_schema:
                example_body[prop] = prop_schema["example"]
            elif prop_schema.get("type") == "string":
                example_body[prop] = f"example_{prop}"
            elif prop_schema.get("type") == "integer":
                example_body[prop] = 123
            elif prop_schema.get("type") == "boolean":
                example_body[prop] = True
            elif prop_schema.get("type") == "array":
                example_body[prop] = []

    # Python example
    python_example = f"""import requests

url = "https://api.extrophi.ai{path}"
headers = {{
    "Content-Type": "application/json",
    "Authorization": "Bearer YOUR_API_KEY"
}}
"""

    if method.upper() in ["POST", "PUT", "PATCH"] and example_body:
        python_example += f"""
data = {json.dumps(example_body, indent=4)}

response = requests.{method.lower()}(url, headers=headers, json=data)
"""
    else:
        python_example += f"""
response = requests.{method.lower()}(url, headers=headers)
"""

    python_example += """print(response.json())"""

    # cURL example
    curl_example = f"""curl -X {method.upper()} \\
  https://api.extrophi.ai{path} \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_API_KEY\""""

    if method.upper() in ["POST", "PUT", "PATCH"] and example_body:
        curl_example += f""" \\
  -d '{json.dumps(example_body)}'"""

    # JavaScript example
    js_example = f"""const response = await fetch('https://api.extrophi.ai{path}', {{
  method: '{method.upper()}',
  headers: {{
    'Content-Type': 'application/json',
    'Authorization': 'Bearer YOUR_API_KEY'
  }}"""

    if method.upper() in ["POST", "PUT", "PATCH"] and example_body:
        js_example += f""",
  body: JSON.stringify({json.dumps(example_body, indent=4)})"""

    js_example += """
});

const data = await response.json();
console.log(data);"""

    return {
        "python": python_example,
        "curl": curl_example,
        "javascript": js_example,
    }


def generate_mintlify_page(path: str, method: str, operation: Dict[str, Any], schemas: Dict[str, Any]) -> str:
    """
    Generate Mintlify markdown page for an API endpoint.

    Args:
        path: API endpoint path
        method: HTTP method
        operation: OpenAPI operation object
        schemas: OpenAPI component schemas

    Returns:
        Mintlify markdown content
    """
    # Page metadata
    title = operation.get("summary", f"{method.upper()} {path}")
    description = operation.get("description", "").strip()

    # Start markdown content
    md = f"""---
title: "{title}"
api: "{method.upper()} {path}"
description: "{description.split(chr(10))[0] if description else title}"
---

## Overview

{description if description else f"Endpoint: `{method.upper()} {path}`"}

"""

    # Add parameters section if available
    parameters = operation.get("parameters", [])
    if parameters:
        md += "## Parameters\n\n"
        for param in parameters:
            param_name = param.get("name", "unknown")
            param_in = param.get("in", "query")
            param_required = param.get("required", False)
            param_desc = param.get("description", "")
            param_type = param.get("schema", {}).get("type", "string")

            required_badge = "**Required**" if param_required else "*Optional*"
            md += f"### `{param_name}` {required_badge}\n\n"
            md += f"- **Type:** `{param_type}`\n"
            md += f"- **Location:** {param_in}\n"
            if param_desc:
                md += f"- **Description:** {param_desc}\n"
            md += "\n"

    # Add request body section if available
    request_body = operation.get("requestBody", {})
    if request_body:
        md += "## Request Body\n\n"
        request_schema = request_body.get("content", {}).get("application/json", {}).get("schema", {})

        if "$ref" in request_schema:
            schema_name = request_schema["$ref"].split("/")[-1]
            if schema_name in schemas:
                schema = schemas[schema_name]
                if "properties" in schema:
                    md += "| Field | Type | Required | Description |\n"
                    md += "|-------|------|----------|-------------|\n"
                    required_fields = schema.get("required", [])
                    for prop_name, prop_schema in schema["properties"].items():
                        prop_type = prop_schema.get("type", "unknown")
                        is_required = "✓" if prop_name in required_fields else ""
                        prop_desc = prop_schema.get("description", "")
                        md += f"| `{prop_name}` | `{prop_type}` | {is_required} | {prop_desc} |\n"
                    md += "\n"

    # Add response section
    responses = operation.get("responses", {})
    if responses:
        md += "## Responses\n\n"
        for status_code, response in responses.items():
            response_desc = response.get("description", "")
            md += f"### {status_code}\n\n"
            md += f"{response_desc}\n\n"

    # Add code examples
    md += "## Code Examples\n\n"
    examples = generate_code_examples(method, path, operation)

    md += "### Python\n\n"
    md += f"```python\n{examples['python']}\n```\n\n"

    md += "### cURL\n\n"
    md += f"```bash\n{examples['curl']}\n```\n\n"

    md += "### JavaScript\n\n"
    md += f"```javascript\n{examples['javascript']}\n```\n\n"

    return md


def main():
    """Main function to generate API documentation."""
    print("🚀 Generating API documentation...")

    # Define FastAPI applications to document
    apps = [
        {
            "path": str(project_root / "backend" / "main.py"),
            "name": "app",
            "title": "Backend API",
        },
        {
            "path": str(project_root / "research" / "backend" / "main.py"),
            "name": "app",
            "title": "Research Module API",
        },
    ]

    # Extract OpenAPI specs
    print("📝 Extracting OpenAPI specifications...")
    specs = []
    for app_config in apps:
        try:
            print(f"  - Extracting from {app_config['title']}...")
            spec = extract_openapi_spec(app_config["path"], app_config["name"])
            specs.append(spec)
        except Exception as e:
            print(f"    ⚠️  Warning: Could not extract spec from {app_config['title']}: {e}")

    if not specs:
        print("❌ Error: No OpenAPI specs could be extracted")
        return 1

    # Merge specs
    print("🔗 Merging OpenAPI specifications...")
    merged_spec = merge_openapi_specs(specs)

    # Save OpenAPI spec
    openapi_path = project_root / "docs" / "api" / "openapi.json"
    openapi_path.parent.mkdir(parents=True, exist_ok=True)
    with open(openapi_path, "w") as f:
        json.dump(merged_spec, f, indent=2)
    print(f"✅ Saved OpenAPI spec to {openapi_path}")

    # Generate Mintlify pages
    print("📄 Generating Mintlify documentation pages...")
    endpoints_dir = project_root / "docs" / "api" / "endpoints"
    endpoints_dir.mkdir(parents=True, exist_ok=True)

    schemas = merged_spec.get("components", {}).get("schemas", {})
    paths = merged_spec.get("paths", {})

    page_count = 0
    for path, methods in paths.items():
        for method, operation in methods.items():
            if method in ["get", "post", "put", "patch", "delete"]:
                # Generate page filename
                # Convert /scrape/{platform} to scrape-platform.md
                page_name = path.strip("/").replace("{", "").replace("}", "").replace("/", "-")
                if not page_name:
                    page_name = "root"
                page_name = f"{method}-{page_name}.md"

                # Generate page content
                page_content = generate_mintlify_page(path, method, operation, schemas)

                # Save page
                page_path = endpoints_dir / page_name
                with open(page_path, "w") as f:
                    f.write(page_content)

                page_count += 1
                print(f"  ✓ {page_name}")

    print(f"\n✨ Successfully generated {page_count} documentation pages!")
    print(f"📂 Documentation saved to {endpoints_dir}")
    print("\n🎉 API documentation generation complete!")

    return 0


if __name__ == "__main__":
    sys.exit(main())
