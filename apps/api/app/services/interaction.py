"""
Semantic interaction service — shared by MCP tools and future REST API.
Action execution pattern reference: appium/appium-uiautomator2-driver lib/commands/.
"""
from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

from sqlmodel import Session

from app.models import ActionResult, BatchResult, Device, Step
from app.services import evidence as ev_svc
from app.services import screen_version as sv
from app.services.screen_version import ScreenVersionConflict


class DeviceNotReady(Exception): ...
class TargetNotFound(Exception): ...
class ActionTimeout(Exception): ...


async def _resolve_target(device: Device, target: str) -> str:
    """Resolve a semantic target (accessible name → role → selector → coords)."""
    if device.family == "browser":
        from app.adapters.browser.adapter import _sessions
        session = _sessions.get(str(device.id))
        if session and session._page:
            page = session._page
            # Try accessible name
            try:
                el = await page.get_by_label(target).first.element_handle()  # type: ignore
                if el:
                    return target
            except Exception:
                pass
            # Try text
            try:
                el = await page.get_by_text(target, exact=False).first.element_handle()  # type: ignore
                if el:
                    return target
            except Exception:
                pass
    return target  # pass through; adapter will handle final resolution


async def execute_action(
    db: Session,
    device_id: uuid.UUID,
    action: str,
    params: dict,
    session_id: str = "mcp",
    expected_screen_version: int | None = None,
) -> ActionResult:
    device = db.get(Device, device_id)
    if not device:
        return ActionResult(
            success=False,
            before_screen_version=0,
            after_screen_version=0,
            evidence_id="",
            error="Device not found",
        )

    if device.state != "ready":
        return ActionResult(
            success=False,
            before_screen_version=sv.current_version(db, device_id),
            after_screen_version=sv.current_version(db, device_id),
            evidence_id="",
            error=f"DEVICE_NOT_READY: device is '{device.state}'",
        )

    before_version = sv.current_version(db, device_id)

    if expected_screen_version is not None and expected_screen_version != before_version:
        return ActionResult(
            success=False,
            before_screen_version=before_version,
            after_screen_version=before_version,
            evidence_id="",
            error=f"SCREEN_VERSION_CONFLICT: expected {expected_screen_version}, got {before_version}",
        )

    warnings: list[str] = []
    error: str | None = None
    success = False

    try:
        await _dispatch_action(device, action, params)
        success = True
    except TargetNotFound as e:
        error = f"TARGET_NOT_FOUND: {e}"
    except ActionTimeout as e:
        error = f"ACTION_TIMEOUT: {e}"
    except Exception as e:
        error = str(e)

    after_version = sv.increment(db, device_id) if success else before_version

    ev = ev_svc.create_evidence(
        db,
        session_id=session_id,
        device_id=device_id,
        mcp_tool=action,
        request_payload={"action": action, **params},
        before_screen_version=before_version,
        after_screen_version=after_version,
        warnings=warnings,
    )

    return ActionResult(
        success=success,
        before_screen_version=before_version,
        after_screen_version=after_version,
        evidence_id=str(ev.id),
        warnings=warnings,
        error=error,
    )


async def _dispatch_action(device: Device, action: str, params: dict) -> None:
    if device.family == "browser":
        await _browser_action(device, action, params)
    elif device.family == "linux":
        await _linux_action(device, action, params)
    else:
        raise NotImplementedError(f"Interaction not implemented for family '{device.family}'")


async def _browser_action(device: Device, action: str, params: dict) -> None:
    from app.adapters.browser.adapter import _sessions
    session = _sessions.get(str(device.id))
    if not session or session._page is None:
        raise DeviceNotReady("No active browser session")
    page = session._page

    if action == "navigate":
        await page.goto(params.get("url", ""))  # type: ignore
    elif action == "click":
        target = params.get("target", "")
        try:
            await page.click(target)  # type: ignore
        except Exception as e:
            raise TargetNotFound(str(e)) from e
    elif action == "type_text":
        target = params.get("target", "body")
        text = params.get("text", "")
        await page.fill(target, text)  # type: ignore
    elif action == "fill_form":
        for selector, value in params.get("fields", {}).items():
            await page.fill(selector, str(value))  # type: ignore
    elif action == "scroll":
        direction = params.get("direction", "down")
        amount = params.get("amount", 300)
        delta_y = amount if direction == "down" else -amount
        await page.evaluate(f"window.scrollBy(0, {delta_y})")  # type: ignore
    elif action == "select_option":
        await page.select_option(params.get("target", ""), params.get("value", ""))  # type: ignore
    elif action == "wait_for":
        condition = params.get("condition", "")
        timeout = params.get("timeout_ms", 5000)
        await page.wait_for_selector(condition, timeout=timeout)  # type: ignore
    else:
        raise NotImplementedError(f"Browser action '{action}' not implemented")


async def _linux_action(device: Device, action: str, params: dict) -> None:
    # Phase 03: Linux actions run via SSM command. Stubbed until runtime agent channel (Phase 04).
    if action in ("click", "type_text", "key", "scroll"):
        raise NotImplementedError(
            f"Linux action '{action}' requires runtime agent channel — available in Phase 04"
        )
    raise NotImplementedError(f"Linux action '{action}' not implemented")


async def run_steps(
    db: Session,
    device_id: uuid.UUID,
    steps: list[Step],
    abort_on_failure: bool = True,
    screen_version_guard: int | None = None,
    session_id: str = "mcp",
) -> BatchResult:
    current = sv.current_version(db, device_id)
    if screen_version_guard is not None and screen_version_guard != current:
        return BatchResult(
            success=False,
            steps=[],
            final_screen_version=current,
            total_steps=len(steps),
            completed_steps=0,
        )

    results: list[ActionResult] = []
    overall_success = True

    for step in steps:
        if step.wait_after_ms > 0:
            await asyncio.sleep(step.wait_after_ms / 1000)

        result = await execute_action(
            db=db,
            device_id=device_id,
            action=step.action,
            params=step.params,
            session_id=session_id,
            expected_screen_version=step.expected_screen_version,
        )
        results.append(result)

        if not result.success:
            overall_success = False
            if abort_on_failure:
                break

    return BatchResult(
        success=overall_success,
        steps=results,
        final_screen_version=sv.current_version(db, device_id),
        total_steps=len(steps),
        completed_steps=len(results),
    )
