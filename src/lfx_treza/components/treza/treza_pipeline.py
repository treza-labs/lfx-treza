from __future__ import annotations

# Component first: lfx.io needs lfx.custom loaded, or the import is circular.
from lfx.custom.custom_component.component import Component  # noqa: F401

import json

from lfx.io import MessageTextInput, MultilineInput, Output
from lfx.schema.data import Data

from lfx_treza._base import TrezaComponent, api_key_input, max_cost_input, wait_input
from lfx_treza._client import TrezaError


class TrezaRunPipelineComponent(TrezaComponent):
    display_name = "Treza Run Pipeline"
    description = "Run one of your saved Treza pipelines, with new inputs if given. Priced first, paid from prepaid Treza credits."
    name = "TrezaRunPipeline"

    inputs = [
        api_key_input(),
        MessageTextInput(
            name="pipeline_id",
            display_name="Pipeline ID",
            info="In the pipeline's address in Treza. Starts with pipeline_.",
            required=True,
            tool_mode=True,
        ),
        MultilineInput(
            name="inputs_json",
            display_name="Inputs (JSON)",
            info='One entry per input step, for example {"prompt_1": "a lighthouse at dawn"}. Leave empty to run it as saved.',
            tool_mode=True,
        ),
        max_cost_input(),
        wait_input(600),
    ]

    outputs = [Output(display_name="Result", name="result", method="run_pipeline")]

    def run_pipeline(self) -> Data:
        pid = (self.pipeline_id or "").strip()
        raw = (self.inputs_json or "").strip()

        def start(treza, cap):
            if not pid:
                raise TrezaError("Give the Pipeline ID. It is in the pipeline's address in Treza and starts with pipeline_.")
            try:
                inputs = json.loads(raw) if raw else None
            except ValueError as err:
                raise TrezaError(f"Inputs must be JSON, like {{\"prompt_1\": \"a lighthouse\"}}: {err}") from err
            if inputs is not None and not isinstance(inputs, dict):
                raise TrezaError('Inputs must be a JSON object, like {"prompt_1": "a lighthouse"}.')
            return treza.start_quoted(cap, lambda: treza.request("estimate_run_cost", {"pipelineId": pid}), inputs or None)

        return self._render(start, None, 600)
