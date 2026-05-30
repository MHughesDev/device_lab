---
doc_id: "5.2"
title: "Add an MCP Tool"
section: "Procedures"
summary: "Adds MCP tools by exposing FastAPI routes that surface as OpenAPI-derived MCP tools."
updated: "2026-04-17"
---

# 5.2 — Add an MCP Tool

## 5.2.1 Purpose

Add a new MCP tool to the application, either by exposing a FastAPI endpoint
or by adding a small route that maps to the behavior you need.

For a **development-only** stdio MCP server (queue helpers, repo resources, `make`
wrappers for coding agents), see [microfast-dev-mcp.md](microfast-dev-mcp.md) — separate from this FastAPI-integrated path.

## 5.2.2 Trigger

- New AI-accessible capability needed
- Existing endpoint needs MCP exposure with custom behavior

## 5.2.3 Prerequisites

- `fastapi-mcp` installed (see `pyproject.toml`)
- MCP module mounted in `apps/api/app/main.py`
- Understanding of MCP tool design principles

## 5.2.4 How tools are built

`fastapi-mcp` generates MCP tools from the app's **OpenAPI** schema. Each
operation becomes a tool named by its `operation_id`. There is no `@mcp.tool()`
decorator in this library — add or reuse **FastAPI routes** with clear
docstrings and type hints.

## 5.2.5 Method A: Expose an existing FastAPI endpoint

If you add a new FastAPI route anywhere under the mounted app, it becomes an MCP
tool automatically (subject to optional tag/operation filtering in
`apps/api/app/mcp/__init__.py`).

1. Create your FastAPI endpoint in `apps/api/app/<module>/router.py` as normal
2. Ensure the endpoint has:
   - Clear docstring (becomes the tool description for the AI model)
   - Type-annotated parameters (becomes the tool input schema)
   - Type-annotated return value (becomes the tool output schema)
3. Optionally tag it for filtering:

   ```python
   @router.get("/estimates/{id}", tags=["estimates"])
   ```

4. Restart the server — the tool appears at `/mcp` automatically

### Filtering endpoints

To control which endpoints become MCP tools, edit `apps/api/app/mcp/__init__.py`:

```python
mcp = FastApiMCP(
    app,
    include_tags=["estimates", "quotes"],  # Only these tags
    exclude_operations=["debug_info"],  # Skip these operation IDs
)
```

## 5.2.6 Method B: Add a dedicated MCP-oriented route

Use this when the tool should not live in a domain module (e.g. a minimal
connectivity check or an aggregation wrapper).

1. Open `apps/api/app/mcp/__init__.py`
2. Add a route on `_mcp_custom_router` (or register another `APIRouter`) **before**
   `FastApiMCP` is constructed, with an explicit `operation_id`:

   ```python
   @_mcp_custom_router.get(
       "/my_tool",
       operation_id="my_custom_tool",
       response_model=MyResponse,
   )
   async def my_custom_tool(...) -> MyResponse:
       """Describe the tool for MCP clients."""
       ...
   ```

3. For heavier logic, call service-layer functions from the handler — keep this
   package free of business rules beyond wiring.
4. Restart the server — the tool appears alongside auto-generated tools

## 5.2.7 Tool design rules

1. **One action per tool.** Don't combine read-and-update or create-and-submit.
2. **Clear docstrings.** The AI model reads these to decide when to call the tool.
3. **Type hints on everything.** The schema is generated from your function signature.
4. **No generic tools.** Never expose `run_sql`, `execute_shell`, or `call_api`.
5. **Declare side effects.** If the tool sends email or modifies external state, say so in the docstring.

## 5.2.8 Adding auth to MCP

Protect MCP endpoints using `AuthConfig` and FastAPI dependencies:

```python
from fastapi import Depends
from fastapi_mcp.types import AuthConfig
from apps.api.src.auth.dependencies import get_current_user

mcp = FastApiMCP(
    app,
    name="template-mcp-server",
    description="...",
    auth_config=AuthConfig(dependencies=[Depends(get_current_user)]),
)
```

See `fastapi_mcp.types.AuthConfig` for OAuth and metadata options.

## 5.2.9 Validation

- [ ] Server starts without errors
- [ ] `/mcp` endpoint is accessible
- [ ] New tool appears in MCP tool listing
- [ ] Tool has correct input schema (check via MCP Inspector)
- [ ] Tool docstring is clear and accurate
- [ ] Auth works if enabled (unauthorized callers rejected)

## 5.2.10 Testing with MCP Inspector

```bash
npx @modelcontextprotocol/inspector http://localhost:8000/mcp
```

This opens a browser UI where you can see all registered tools, their schemas,
and invoke them manually.

## 5.2.11 Removing MCP

To remove MCP from the project entirely:

1. Delete `apps/api/app/mcp/` folder
2. Remove lines between `# --- MCP MODULE START ---` and `# --- MCP MODULE END ---`
   in `apps/api/app/main.py` and `.env.example`
3. Remove `fastapi-mcp` from `pyproject.toml`
4. Run `make test` to verify nothing breaks
