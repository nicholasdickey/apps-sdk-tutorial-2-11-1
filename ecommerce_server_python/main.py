"""Pizzaz demo MCP server implemented with the Python FastMCP helper.

The server mirrors the Node example in this repository and exposes
widget-backed tools that render the Pizzaz UI bundle. Each handler returns the
HTML shell via an MCP resource and echoes the selected topping as structured
content so the ChatGPT client can hydrate the widget. The module also wires the
handlers into an HTTP/SSE stack so you can run the server with uvicorn on port
8000, matching the Node transport behavior."""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Dict, List

import mcp.types as types
from mcp.server.fastmcp import FastMCP


@dataclass(frozen=True)
class PizzazWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ECOMMERCE_SAMPLE_DATA_PATH = (
    Path(__file__).resolve().parent.parent
    / "ecommerce_server_python"
    / "sample_data.json"
)


@lru_cache(maxsize=None)
def _load_widget_html(component_name: str) -> str:
    html_path = ASSETS_DIR / f"{component_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf8")

    fallback_candidates = sorted(ASSETS_DIR.glob(f"{component_name}-*.html"))
    if fallback_candidates:
        return fallback_candidates[-1].read_text(encoding="utf8")

    raise FileNotFoundError(
        f'Widget HTML for "{component_name}" not found in {ASSETS_DIR}. '
        "Run `pnpm run build` to generate the assets before starting the server."
    )


@lru_cache(maxsize=1)
def _load_ecommerce_cart_items() -> List[Dict[str, Any]]:
    if not ECOMMERCE_SAMPLE_DATA_PATH.exists():
        return []

    try:
        raw = json.loads(ECOMMERCE_SAMPLE_DATA_PATH.read_text(encoding="utf8"))
    except json.JSONDecodeError:
        return []

    items: List[Dict[str, Any]] = []
    for entry in raw.get("products", []):
        if isinstance(entry, dict):
            items.append(entry)

    return items


def _product_matches_search(item: Dict[str, Any], search_term: str) -> bool:
    """Return True if the product matches the provided search term."""
    term = search_term.strip().lower()
    if not term:
        return True

    def _contains_text(value: Any) -> bool:
        return isinstance(value, str) and term in value.lower()

    searchable_fields = (
        "name",
        "description",
        "shortDescription",
        "detailSummary",
    )

    for field in searchable_fields:
        if _contains_text(item.get(field)):
            return True

    tags = item.get("tags")
    if isinstance(tags, list):
        for tag in tags:
            if _contains_text(tag):
                return True

    highlights = item.get("highlights")
    if isinstance(highlights, list):
        for highlight in highlights:
            if _contains_text(highlight):
                return True

    return False


ECOMMERCE_WIDGET = PizzazWidget(
    identifier="pizzaz-ecommerce",
    title="Show Ecommerce Catalog",
    template_uri="ui://widget/ecommerce.html",
    invoking="Loading the ecommerce catalog",
    invoked="Ecommerce catalog ready",
    html=_load_widget_html("ecommerce"),
    response_text="Rendered the ecommerce catalog!",
)


MIME_TYPE = "text/html+skybridge"

SEARCH_TOOL_NAME = ECOMMERCE_WIDGET.identifier
INCREMENT_TOOL_NAME = "increment_item"

SEARCH_TOOL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "title": "Product search terms",
    "properties": {
        "searchTerm": {
            "type": "string",
            "description": "Free-text keywords to filter products by name, description, tags, or highlights.",
        },
    },
    "required": [],
    "additionalProperties": False,
}

INCREMENT_TOOL_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "title": "Increment cart item",
    "properties": {
        "productId": {
            "type": "string",
            "description": "Product ID from the catalog to increment.",
        },
        "incrementBy": {
            "type": "integer",
            "minimum": 1,
            "default": 1,
            "description": "How many units to add to the product quantity (defaults to 1).",
        },
    },
    "required": ["productId"],
    "additionalProperties": False,
}


mcp = FastMCP(
    name="pizzaz-python",
    stateless_http=True,
)


def _resource_description(widget: PizzazWidget) -> str:
    return f"{widget.title} widget markup"


def _tool_meta(widget: PizzazWidget) -> Dict[str, Any]:
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }


def _tool_invocation_meta(widget: PizzazWidget) -> Dict[str, Any]:
    return {
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
    }


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=SEARCH_TOOL_NAME,
            title=ECOMMERCE_WIDGET.title,
            description="Search the ecommerce catalog using free-text keywords.",
            inputSchema=SEARCH_TOOL_SCHEMA,
            _meta=_tool_meta(ECOMMERCE_WIDGET),
            # To disable the approval prompt for the tools
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        ),
        types.Tool(
            name=INCREMENT_TOOL_NAME,
            title="Increment Cart Item",
            description="Increase the quantity of an item already in the cart.",
            inputSchema=INCREMENT_TOOL_SCHEMA,
            _meta=_tool_meta(ECOMMERCE_WIDGET),
            # To disable the approval prompt for the tools
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        ),
    ]


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=ECOMMERCE_WIDGET.title,
            title=ECOMMERCE_WIDGET.title,
            uri=ECOMMERCE_WIDGET.template_uri,
            description=_resource_description(ECOMMERCE_WIDGET),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(ECOMMERCE_WIDGET),
        )
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=ECOMMERCE_WIDGET.title,
            title=ECOMMERCE_WIDGET.title,
            uriTemplate=ECOMMERCE_WIDGET.template_uri,
            description=_resource_description(ECOMMERCE_WIDGET),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(ECOMMERCE_WIDGET),
        )
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    requested_uri = str(req.params.uri)
    if requested_uri != ECOMMERCE_WIDGET.template_uri:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=ECOMMERCE_WIDGET.template_uri,
            mimeType=MIME_TYPE,
            text=ECOMMERCE_WIDGET.html,
            _meta=_tool_meta(ECOMMERCE_WIDGET),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    tool_name = req.params.name
    if tool_name not in {SEARCH_TOOL_NAME, INCREMENT_TOOL_NAME}:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {req.params.name}",
                    )
                ],
                isError=True,
            )
        )

    arguments = req.params.arguments or {}
    meta = _tool_invocation_meta(ECOMMERCE_WIDGET)
    cart_items = [deepcopy(item) for item in _load_ecommerce_cart_items()]

    if tool_name == SEARCH_TOOL_NAME:
        search_term = str(arguments.get("searchTerm", "")).strip()
        filtered_items = cart_items
        if search_term:
            filtered_items = [
                item
                for item in cart_items
                if _product_matches_search(item, search_term)
            ]
        structured_content: Dict[str, Any] = {
            "cartItems": filtered_items,
            "searchTerm": search_term,
        }
        response_text = ECOMMERCE_WIDGET.response_text
    else:
        product_id = str(arguments.get("productId", "")).strip()
        if not product_id:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text="productId is required to increment a cart item.",
                        )
                    ],
                    isError=True,
                )
            )

        increment_raw = arguments.get("incrementBy", 1)
        try:
            increment_by = int(increment_raw)
        except (TypeError, ValueError):
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text="incrementBy must be an integer.",
                        )
                    ],
                    isError=True,
                )
            )

        if increment_by < 1:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text="incrementBy must be at least 1.",
                        )
                    ],
                    isError=True,
                )
            )

        product = next(
            (item for item in cart_items if item.get("id") == product_id),
            None,
        )
        if product is None:
            return types.ServerResult(
                types.CallToolResult(
                    content=[
                        types.TextContent(
                            type="text",
                            text=f"Product '{product_id}' was not found in the cart.",
                        )
                    ],
                    isError=True,
                )
            )

        current_quantity_raw = product.get("quantity", 0)
        try:
            current_quantity = int(current_quantity_raw)
        except (TypeError, ValueError):
            current_quantity = 0
        product["quantity"] = current_quantity + increment_by

        structured_content = {
            "cartItems": cart_items,
            "searchTerm": "",
        }
        product_name = product.get("name", product_id)
        response_text = (
            f"Incremented {product_name} by {increment_by}. Updated cart ready."
        )

    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=response_text,
                )
            ],
            structuredContent=structured_content,
            _meta=meta,
        )
    )


mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource


app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000)
