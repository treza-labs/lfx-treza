"""What every Treza component shares: the API key, the Max cost, the wait, and how a render comes back.

A render is quoted first. When the quote is over Max cost nothing starts and nothing is spent. A refusal comes back
as Data with an ``error`` and a ``code``, not as an exception, so an agent using the component as a tool can read it
and tell the person.
"""

from __future__ import annotations

from typing import Any, Callable

from lfx.custom.custom_component.component import Component
from lfx.io import FloatInput, IntInput, SecretStrInput
from lfx.schema.data import Data

from lfx_treza._client import TrezaClient, TrezaError, finished_or_raise, max_cost, run_item

DOCS_URL = "https://www.trezalabs.com/integrations/langflow"


def api_key_input() -> SecretStrInput:
    return SecretStrInput(
        name="api_key",
        display_name="Treza API Key",
        info="A Treza API key with the pipelines read, write and run permissions. Make one at "
        "https://www.trezalabs.com/platform/api-keys",
        required=True,
        value="TREZA_API_KEY",
    )


def max_cost_input() -> FloatInput:
    return FloatInput(
        name="max_cost_usd",
        display_name="Max Cost (USD)",
        info="The most one render may cost. Treza prices it first, and nothing is spent when the price is higher. "
        "Leave at 0 for no cap. Set a cap when an agent uses this component.",
        value=0.0,
    )


def wait_input(default: int) -> IntInput:
    return IntInput(
        name="wait_seconds",
        display_name="Wait (seconds)",
        info="How long to wait for the render. One still going comes back with status running and the IDs for "
        "Treza Get Run.",
        value=default,
        advanced=True,
    )


class TrezaComponent(Component):
    """Base class. Not shown in the palette on its own."""

    documentation: str = DOCS_URL
    icon = "Treza"

    def _client(self) -> TrezaClient:
        key = getattr(self, "api_key", None)
        if hasattr(key, "get_secret_value"):
            key = key.get_secret_value()
        if not key or not str(key).strip():
            raise TrezaError("Add a Treza API key. Make one at https://www.trezalabs.com/platform/api-keys", 401, "NoKey")
        return TrezaClient(str(key))

    def _cap(self) -> float:
        return max_cost(getattr(self, "max_cost_usd", None))

    def _wait(self, default: float) -> float:
        value = getattr(self, "wait_seconds", None)
        return float(value) if value else default

    def _render(self, start: Callable[[TrezaClient, float], dict[str, Any]], output_key: str | None, default_wait: float) -> Data:
        """Quote and start through ``start``, wait for the file, and return the render as Data."""

        def go() -> Data:
            treza = self._client()
            started = start(treza, self._cap())
            run = treza.wait_for_run(started["pipelineId"], started["runId"], self._wait(default_wait))
            run = {"runId": started["runId"], "pipelineId": started["pipelineId"], **run}
            finished_or_raise(run)
            quoted = started.get("quoted") or {}
            model = quoted.get("model")
            item = run_item(
                run,
                output_key,
                {"price_usd": started.get("priceUsd"), "model": model.get("id") if isinstance(model, dict) else model},
            )
            self.status = item.get("url") or item.get("status")
            return Data(data=item)

        return self._guard(go)

    def _guard(self, fn: Callable[[], Data]) -> Data:
        try:
            return fn()
        except TrezaError as err:
            self.status = str(err)
            return Data(data={"error": str(err), "code": err.code, "finished": False})
