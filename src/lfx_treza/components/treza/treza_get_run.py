from __future__ import annotations

# Component first: lfx.io needs lfx.custom loaded, or the import is circular.
from lfx.custom.custom_component.component import Component  # noqa: F401

from lfx.io import MessageTextInput, Output
from lfx.schema.data import Data

from lfx_treza._base import TrezaComponent, api_key_input
from lfx_treza._client import TOP_UP_URL, compact, finished_or_raise, run_item, to_number


class TrezaGetRunComponent(TrezaComponent):
    display_name = "Treza Get Run"
    description = "Check a Treza render that was still going when its component stopped waiting. Free."
    name = "TrezaGetRun"

    inputs = [
        api_key_input(),
        MessageTextInput(name="pipeline_id", display_name="Pipeline ID", info="The pipeline_id a Treza component returned.", required=True, tool_mode=True),
        MessageTextInput(name="run_id", display_name="Run ID", info="The run_id a Treza component returned.", required=True, tool_mode=True),
    ]

    outputs = [Output(display_name="Run", name="run", method="get_run")]

    def get_run(self) -> Data:
        pid, rid = (self.pipeline_id or "").strip(), (self.run_id or "").strip()

        def go() -> Data:
            run = self._client().call("get_run", {"pipelineId": pid, "runId": rid})
            run = {"runId": rid, "pipelineId": pid, **run}
            finished_or_raise(run)
            item = run_item(run)
            self.status = item.get("url") or item.get("status")
            return Data(data=item)

        return self._guard(go)


class TrezaBalanceComponent(TrezaComponent):
    display_name = "Treza Balance"
    description = "The prepaid credits left on the Treza account, in US dollars. Free."
    name = "TrezaBalance"

    inputs = [api_key_input()]

    outputs = [Output(display_name="Balance", name="balance", method="get_balance")]

    def get_balance(self) -> Data:
        def go() -> Data:
            balance = self._client().call("get_credit_balance")
            item = compact(
                {
                    "balance_usd": to_number(balance.get("balanceUsd")),
                    "approx_videos_remaining": balance.get("approxVideosRemaining"),
                    "top_up_url": balance.get("topUpUrl") or TOP_UP_URL,
                }
            )
            self.status = f"${item.get('balance_usd', 0):.2f}"
            return Data(data=item)

        return self._guard(go)
