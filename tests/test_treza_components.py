"""Unit tests for lfx-treza against a scripted Treza API. No network and no API key needed."""

from __future__ import annotations

import pytest

import lfx_treza._base as base
from lfx_treza import (
    TrezaBalanceComponent,
    TrezaGetRunComponent,
    TrezaImageComponent,
    TrezaRunPipelineComponent,
    TrezaVideoComponent,
)
from lfx_treza._client import TrezaClient

from .fakes import FakeTreza

PID, RID = "pipeline_1", "run_1"
IMAGE_URL = "https://media.trezalabs.com/api/media/generated/image/a.png"
VIDEO_URL = "https://media.trezalabs.com/api/media/generated/video/a.mp4"


def quote(price, **extra):
    return 200, {"pipelineId": PID, "estimatedChargeUsd": price, "quoteId": "q1", "sufficient": True, "model": {"id": "google/veo-3.1-lite"}, **extra}


def done(outputs):
    return 200, {"status": "success", "outputs": outputs, "durationMs": 12000}


@pytest.fixture
def treza(monkeypatch):
    holder = {}

    def make(**answers):
        fake = FakeTreza(**answers)
        holder["fake"] = fake
        monkeypatch.setattr(base, "TrezaClient", lambda key: TrezaClient(key, session=fake))
        return fake

    return make


def build(cls, **attrs):
    component = cls()
    component.set_attributes({"api_key": "treza_test_key", **attrs})  # pragma: allowlist secret
    return component


def test_bundle_exports_five_components():
    names = {c.name for c in (TrezaImageComponent, TrezaVideoComponent, TrezaRunPipelineComponent, TrezaGetRunComponent, TrezaBalanceComponent)}
    assert names == {"TrezaImage", "TrezaVideo", "TrezaRunPipeline", "TrezaGetRun", "TrezaBalance"}


def test_prompt_inputs_work_as_agent_tools():
    for cls in (TrezaImageComponent, TrezaVideoComponent):
        prompt = next(i for i in cls.inputs if i.name == "prompt")
        assert prompt.tool_mode is True


def test_image_quotes_then_starts_once_and_returns_the_file(treza):
    fake = treza(make_image=[quote(0.0)], run_pipeline=[(200, {"runId": RID})], get_run=[done({"image": IMAGE_URL})])
    data = build(TrezaImageComponent, prompt="a lighthouse", aspect_ratio="4:5", reference_image_urls="", model="", max_cost_usd=0.0, wait_seconds=30).generate_image()
    assert data.data["url"] == IMAGE_URL
    assert data.data["price_usd"] == 0.0
    assert data.data["run_id"] == RID
    assert fake.asked("make_image") == [{"prompt": "a lighthouse", "aspectRatio": "4:5"}]
    assert fake.asked("run_pipeline") == [{"pipelineId": PID, "quoteId": "q1"}]
    assert fake.calls[0][2]["Authorization"] == "Bearer treza_test_key"


def test_video_over_max_cost_starts_nothing(treza):
    fake = treza(make_video=[quote(0.28)])
    data = build(TrezaVideoComponent, prompt="a fox in snow", aspect_ratio="9:16", duration_sec=4, with_audio=True, max_cost_usd=0.01, wait_seconds=30).generate_video()
    assert data.data["code"] == "OverBudget"
    assert "Nothing was spent" in data.data["error"]
    assert fake.asked("make_video")[0]["maxPriceUsd"] == 0.01
    assert fake.asked("run_pipeline") == []


def test_video_still_running_comes_back_with_ids(treza):
    treza(make_video=[quote(0.28)], run_pipeline=[(200, {"runId": RID})], get_run=[(200, {"status": "running", "pollAfterSec": 5})])
    data = build(TrezaVideoComponent, prompt="a fox", aspect_ratio="16:9", duration_sec=4, with_audio=True, max_cost_usd=1.0, wait_seconds=1).generate_video()
    assert data.data["status"] == "running"
    assert data.data["finished"] is False
    assert data.data["pipeline_id"] == PID and data.data["run_id"] == RID


def test_low_balance_is_refused_before_starting(treza):
    fake = treza(make_image=[quote(0.06, sufficient=False, balanceUsd=0.02)])
    data = build(TrezaImageComponent, prompt="x", aspect_ratio="1:1", max_cost_usd=0.0).generate_image()
    assert data.data["code"] == "InsufficientCredits"
    assert fake.asked("run_pipeline") == []


def test_run_pipeline_passes_inputs(treza):
    fake = treza(estimate_run_cost=[quote(0.5)], run_pipeline=[(200, {"runId": RID})], get_run=[done({"video": VIDEO_URL})])
    data = build(TrezaRunPipelineComponent, pipeline_id=PID, inputs_json='{"prompt_1": "a lighthouse"}', max_cost_usd=0.0, wait_seconds=30).run_pipeline()
    assert data.data["url"] == VIDEO_URL
    assert fake.asked("run_pipeline") == [{"pipelineId": PID, "inputs": {"prompt_1": "a lighthouse"}, "quoteId": "q1"}]


def test_run_pipeline_rejects_bad_json(treza):
    treza()
    data = build(TrezaRunPipelineComponent, pipeline_id=PID, inputs_json="{not json", max_cost_usd=0.0).run_pipeline()
    assert "must be JSON" in data.data["error"]


def test_get_run_and_balance(treza):
    treza(get_run=[done({"video": VIDEO_URL})], get_credit_balance=[(200, {"balanceUsd": 2.86, "approxVideosRemaining": 10})])
    run = build(TrezaGetRunComponent, pipeline_id=PID, run_id=RID).get_run()
    assert run.data["url"] == VIDEO_URL
    balance = build(TrezaBalanceComponent).get_balance()
    assert balance.data["balance_usd"] == 2.86


def test_missing_key_is_a_readable_refusal(treza):
    treza()
    component = TrezaBalanceComponent()
    component.set_attributes({"api_key": ""})
    data = component.get_balance()
    assert data.data["code"] == "NoKey"
