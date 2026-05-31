from mcp.server.fastmcp import FastMCP

mcp = FastMCP("DeviceLab", version="0.1.0")


@mcp.tool()
def workspace_status() -> dict:
    """Return workspace capabilities and cloud account status."""
    return {"status": "not_implemented", "phase": 1}


@mcp.tool()
def list_devices() -> list:
    """List all devices and their current lifecycle state."""
    return [{"status": "not_implemented", "phase": 1}]
