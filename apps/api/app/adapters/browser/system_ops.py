# system_ops.py — Browser system operations via Playwright page/context APIs
from __future__ import annotations

from app.adapters.spi import CapabilityUnsupportedError

SYSTEM_ACTIONS = {
    "navigate", "new_tab", "close_tab", "list_tabs", "switch_tab",
    "get_console_logs", "get_network_requests", "handle_dialog",
    "get_clipboard", "set_clipboard", "get_screen_size",
    "launch_app",  # treated as navigate for browser
    "wait_for", "key_down", "key_up",
    # run_shell, file_system, window/process management not supported
}

BROWSER_UNSUPPORTED = {"run_shell", "read_file", "write_file", "list_directory",
                        "list_windows", "focus_window", "resize_window",
                        "list_processes", "kill_process"}


async def handle_system_action(device: object, action: str, params: dict) -> dict:
    if action in BROWSER_UNSUPPORTED:
        raise CapabilityUnsupportedError(action, "browser")

    from app.adapters.browser.adapter import _sessions
    device_id = str(device.id)  # type: ignore[attr-defined]
    session = _sessions.get(device_id)
    if not session or session._page is None:
        return {"success": False, "error": "No active browser session"}

    page = session._page

    if action == "navigate" or action == "launch_app":
        url = params.get("url") or params.get("app", "")
        await page.goto(url)
        return {"success": True, "url": url}

    elif action == "new_tab":
        url = params.get("url", "about:blank")
        new_page = await session._browser.new_page()
        if url != "about:blank":
            await new_page.goto(url)
        session._page = new_page
        return {"success": True, "url": url}

    elif action == "close_tab":
        await page.close()
        pages = session._browser.pages
        if pages:
            session._page = pages[-1]
        return {"success": True}

    elif action == "list_tabs":
        pages = session._browser.pages
        tabs = []
        for i, p in enumerate(pages):
            tabs.append({"index": i, "url": p.url, "title": await p.title()})
        return {"success": True, "tabs": tabs}

    elif action == "switch_tab":
        index = int(params.get("index", 0))
        pages = session._browser.pages
        if index >= len(pages):
            return {"success": False, "error": f"Tab {index} out of range"}
        await pages[index].bring_to_front()
        session._page = pages[index]
        return {"success": True, "index": index}

    elif action == "get_console_logs":
        level = params.get("level", "all")
        msgs = getattr(session, "_console_msgs", [])
        if level != "all":
            msgs = [m for m in msgs if m.get("type") == level]
        return {"success": True, "messages": msgs}

    elif action == "get_network_requests":
        reqs = getattr(session, "_network_requests", [])
        return {"success": True, "requests": reqs}

    elif action == "handle_dialog":
        accept = params.get("accept", True)
        text = params.get("text", "")
        async def _handler(dialog):
            if accept:
                await dialog.accept(text or dialog.default_value)
            else:
                await dialog.dismiss()
        page.once("dialog", _handler)
        return {"success": True, "configured": True}

    elif action == "get_clipboard":
        text = await page.evaluate("navigator.clipboard.readText().catch(() => '')")
        return {"success": True, "text": text}

    elif action == "set_clipboard":
        text = params.get("text", "")
        await page.evaluate(f"navigator.clipboard.writeText({json.dumps(text)}).catch(() => {{}})")
        return {"success": True}

    elif action == "get_screen_size":
        size = page.viewport_size
        if size:
            return {"success": True, "width": size["width"], "height": size["height"]}
        return {"success": True, "width": 1280, "height": 720}

    elif action == "wait_for":
        condition = params.get("condition", "")
        timeout_ms = int(params.get("timeout_ms", 10000))
        try:
            await page.wait_for_selector(condition, timeout=timeout_ms)
            return {"success": True, "found": True}
        except Exception:
            # Try text content search
            try:
                await page.wait_for_function(
                    f"document.body.innerText.includes({json.dumps(condition)})",
                    timeout=timeout_ms,
                )
                return {"success": True, "found": True}
            except Exception:
                return {"success": True, "found": False}

    elif action == "key_down":
        key = params.get("key", "")
        await page.keyboard.down(key)
        return {"success": True}

    elif action == "key_up":
        key = params.get("key", "")
        await page.keyboard.up(key)
        return {"success": True}

    raise CapabilityUnsupportedError(action, "browser")


import json  # noqa: E402 (needed by set_clipboard)
