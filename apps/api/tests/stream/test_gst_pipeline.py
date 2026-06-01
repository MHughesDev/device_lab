# tests/stream/test_gst_pipeline.py — Phase 09 GStreamer pipeline tests
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch


def test_best_encoder_falls_back_to_x264_when_gst_unavailable():
    with patch("app.stream.pipeline.gst._available_encoders", return_value=[]):
        from app.stream.pipeline import gst
        enc = gst.best_encoder()
        assert enc == "x264enc"


def test_best_encoder_picks_first_available():
    with patch("app.stream.pipeline.gst._available_encoders", return_value=["vaapih264enc", "x264enc"]):
        from app.stream.pipeline import gst
        enc = gst.best_encoder()
        assert enc == "vaapih264enc"


def test_pipeline_falls_back_to_x264():
    with patch("app.stream.pipeline.gst._available_encoders", return_value=["x264enc"]):
        from app.stream.pipeline import gst
        enc = gst.best_encoder()
        assert enc == "x264enc"


def test_encoder_config_x264_sets_zerolatency_no_bframes():
    from app.stream.pipeline.gst import _encoder_config
    cfg = _encoder_config("x264enc")
    assert "zerolatency" in cfg
    assert "bframes=0" in cfg
    assert "intra-refresh=true" in cfg


def test_encoder_config_vaapi_sets_no_bframes():
    from app.stream.pipeline.gst import _encoder_config
    cfg = _encoder_config("vaapih264enc")
    assert "max-bframes=0" in cfg


def test_encoder_config_nvenc_sets_no_bframes():
    from app.stream.pipeline.gst import _encoder_config
    cfg = _encoder_config("nvh264enc")
    assert "bframes=0" in cfg


def test_is_gstreamer_available_false_when_not_installed():
    with patch("app.stream.pipeline.gst._gst", side_effect=ImportError("no gi")):
        from app.stream.pipeline import gst
        assert not gst.is_gstreamer_available()


def test_pipeline_desc_includes_encoder_and_appsink():
    from app.stream.pipeline.gst import GstPipeline
    p = GstPipeline(src_element="fakesrc", encoder_name="x264enc")
    desc = p._pipeline_desc()
    assert "x264enc" in desc
    assert "appsink" in desc
    assert "fakesrc" in desc
