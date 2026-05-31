import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models import ActionResult, BatchResult, Device, Step
from app.services import interaction, screen_version as sv


def _make_device(state: str = "ready", family: str = "browser") -> Device:
    return Device(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        family=family,
        state=state,
        screen_version=5,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def _db_stub(device: Device) -> MagicMock:
    db = MagicMock()
    db.get.return_value = device
    db.add = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    return db


class TestExecuteAction:
    @pytest.mark.asyncio
    async def test_device_not_ready_returns_error(self) -> None:
        device = _make_device(state="stopped")
        db = _db_stub(device)
        with patch.object(sv, "current_version", return_value=5):
            result = await interaction.execute_action(db, device.id, "click", {"target": "button"})
        assert not result.success
        assert "DEVICE_NOT_READY" in (result.error or "")

    @pytest.mark.asyncio
    async def test_screen_version_conflict(self) -> None:
        device = _make_device(state="ready")
        db = _db_stub(device)
        with patch.object(sv, "current_version", return_value=5):
            result = await interaction.execute_action(
                db, device.id, "click", {"target": "btn"}, expected_screen_version=3
            )
        assert not result.success
        assert "SCREEN_VERSION_CONFLICT" in (result.error or "")

    @pytest.mark.asyncio
    async def test_browser_navigate_success(self) -> None:
        device = _make_device(state="ready", family="browser")
        db = _db_stub(device)

        page = AsyncMock()
        page.goto = AsyncMock()
        from app.adapters.browser.session import BrowserSession
        session = BrowserSession(device_id=str(device.id))
        session._page = page

        from app.adapters.browser import adapter
        adapter._sessions[str(device.id)] = session

        with patch.object(sv, "current_version", return_value=5), \
             patch.object(sv, "increment", return_value=6), \
             patch("app.services.evidence.create_evidence", return_value=MagicMock(id=uuid.uuid4())):
            result = await interaction.execute_action(
                db, device.id, "navigate", {"url": "https://example.com"}
            )

        page.goto.assert_called_once_with("https://example.com")
        assert result.success
        del adapter._sessions[str(device.id)]

    @pytest.mark.asyncio
    async def test_linux_action_raises_not_implemented(self) -> None:
        device = _make_device(state="ready", family="linux")
        db = _db_stub(device)
        with patch.object(sv, "current_version", return_value=0), \
             patch("app.services.evidence.create_evidence", return_value=MagicMock(id=uuid.uuid4())):
            result = await interaction.execute_action(db, device.id, "click", {"target": "btn"})
        assert not result.success
        assert result.error is not None


class TestRunSteps:
    @pytest.mark.asyncio
    async def test_run_steps_abort_on_failure(self) -> None:
        device = _make_device(state="ready", family="browser")
        db = _db_stub(device)

        steps = [
            Step(action="navigate", params={"url": "https://example.com"}),
            Step(action="click", params={"target": "nonexistent"}),
            Step(action="type_text", params={"target": "input", "text": "hello"}),
        ]

        page = AsyncMock()
        page.goto = AsyncMock()
        page.click = AsyncMock(side_effect=Exception("element not found"))
        from app.adapters.browser.session import BrowserSession
        session = BrowserSession(device_id=str(device.id))
        session._page = page
        from app.adapters.browser import adapter
        adapter._sessions[str(device.id)] = session

        with patch.object(sv, "current_version", return_value=0), \
             patch.object(sv, "increment", return_value=1), \
             patch("app.services.evidence.create_evidence", return_value=MagicMock(id=uuid.uuid4())):
            result = await interaction.run_steps(db, device.id, steps, abort_on_failure=True)

        assert not result.success
        assert result.completed_steps == 2  # navigate ok, click fail → abort
        assert result.total_steps == 3
        del adapter._sessions[str(device.id)]

    @pytest.mark.asyncio
    async def test_screen_version_guard_blocks_start(self) -> None:
        device = _make_device(state="ready", family="browser")
        db = _db_stub(device)
        with patch.object(sv, "current_version", return_value=10):
            result = await interaction.run_steps(
                db, device.id, [], screen_version_guard=5
            )
        assert not result.success
        assert result.completed_steps == 0

    @pytest.mark.asyncio
    async def test_run_steps_continue_on_failure(self) -> None:
        device = _make_device(state="ready", family="browser")
        db = _db_stub(device)

        steps = [
            Step(action="click", params={"target": "bad"}),
            Step(action="navigate", params={"url": "https://x.com"}),
        ]
        page = AsyncMock()
        page.click = AsyncMock(side_effect=Exception("not found"))
        page.goto = AsyncMock()
        from app.adapters.browser.session import BrowserSession
        session = BrowserSession(device_id=str(device.id))
        session._page = page
        from app.adapters.browser import adapter
        adapter._sessions[str(device.id)] = session

        with patch.object(sv, "current_version", return_value=0), \
             patch.object(sv, "increment", return_value=1), \
             patch("app.services.evidence.create_evidence", return_value=MagicMock(id=uuid.uuid4())):
            result = await interaction.run_steps(db, device.id, steps, abort_on_failure=False)

        assert result.completed_steps == 2  # both ran
        del adapter._sessions[str(device.id)]


class TestScreenVersionConflict:
    def test_assert_version_raises_on_mismatch(self) -> None:
        db = MagicMock()
        device = _make_device()
        device.screen_version = 7
        db.get.return_value = device
        with pytest.raises(sv.ScreenVersionConflict) as exc_info:
            sv.assert_version(db, device.id, 5)
        assert exc_info.value.expected == 5
        assert exc_info.value.actual == 7

    def test_assert_version_passes_on_match(self) -> None:
        db = MagicMock()
        device = _make_device()
        device.screen_version = 5
        db.get.return_value = device
        sv.assert_version(db, device.id, 5)  # should not raise
