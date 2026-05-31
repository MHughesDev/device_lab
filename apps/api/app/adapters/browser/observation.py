"""
Browser AX observation — patterns from browser-use/browser_use/dom/.
Extracts the DOM accessibility tree from a live Playwright page.
"""
from __future__ import annotations

import json


async def extract_ax_tree(page: object) -> dict:
    """Extract AX snapshot from a Playwright page object."""
    try:
        # Use Playwright's built-in accessibility snapshot
        snapshot = await page.accessibility.snapshot()  # type: ignore[attr-defined]
        return {"nodes": [snapshot] if snapshot else [], "source": "playwright_ax"}
    except AttributeError:
        pass
    # Fallback: execute JS to walk DOM with role/name/value
    try:
        result = await page.evaluate(_DOM_WALKER_JS)  # type: ignore[attr-defined]
        return {"nodes": result, "source": "dom_walker"}
    except Exception as e:
        return {"error": str(e), "nodes": []}


_DOM_WALKER_JS = """
() => {
  function walkNode(el, depth) {
    if (depth > 10) return null;
    const role = el.getAttribute && el.getAttribute('role');
    const name = el.getAttribute && (el.getAttribute('aria-label') || el.getAttribute('aria-labelledby') || el.textContent?.slice(0, 80));
    const node = {
      tag: el.tagName?.toLowerCase(),
      role: role || undefined,
      name: name?.trim() || undefined,
      children: []
    };
    for (const child of el.children) {
      const childNode = walkNode(child, depth + 1);
      if (childNode) node.children.push(childNode);
    }
    return node;
  }
  return [walkNode(document.body, 0)].filter(Boolean);
}
"""


async def extract_screenshot(page: object) -> bytes | None:
    try:
        return await page.screenshot()  # type: ignore[attr-defined]
    except Exception:
        return None
