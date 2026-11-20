from __future__ import annotations

# Component first: lfx.io needs lfx.custom loaded, or the import is circular.
from lfx.custom.custom_component.component import Component  # noqa: F401

from lfx.io import BoolInput, DropdownInput, IntInput, MessageTextInput, Output
from lfx.schema.data import Data

from lfx_treza._base import TrezaComponent, api_key_input, max_cost_input, wait_input
from lfx_treza._client import compact, price_limit, to_number

VIDEO_SHAPES = ["16:9", "9:16", "1:1"]


class TrezaVideoComponent(TrezaComponent):
    display_name = "Treza Video"
    description = (
        "Make a short video clip from a description with Treza (Veo, Kling, Seedance and more). Takes one to five "
        "minutes. Priced first, paid from prepaid Treza credits."
    )
    name = "TrezaVideo"

    inputs = [
        api_key_input(),
        MessageTextInput(name="prompt", display_name="Prompt", info="What happens in the clip.", required=True, tool_mode=True),
        DropdownInput(
            name="aspect_ratio",
            display_name="Aspect Ratio",
            info='"16:9" wide, "9:16" vertical (Shorts, Reels, TikTok) or "1:1" square.',
            options=VIDEO_SHAPES,
            value="16:9",
        ),
        IntInput(name="duration_sec", display_name="Duration (seconds)", info="Clip length, usually 4 to 10.", value=4),
        BoolInput(name="with_audio", display_name="With Audio", info="Generate sound where the model can.", value=True, advanced=True),
        MessageTextInput(
            name="first_frame_url",
            display_name="First Frame URL",
            info="A picture in the Treza library that the clip opens on.",
            advanced=True,
        ),
        MessageTextInput(
            name="last_frame_url",
            display_name="Last Frame URL",
            info="A picture in the Treza library that the clip ends on.",
            advanced=True,
        ),
        MessageTextInput(name="model", display_name="Model", info="A Treza model ID. Leave empty for Treza's default.", advanced=True),
        max_cost_input(),
        wait_input(300),
    ]

    outputs = [Output(display_name="Video", name="video", method="generate_video")]

    def generate_video(self) -> Data:
        def start(treza, cap):
            args = compact(
                {
                    "prompt": (self.prompt or "").strip(),
                    "aspectRatio": self.aspect_ratio,
                    "durationSec": to_number(self.duration_sec),
                    "withAudio": self.with_audio,
                    "firstFrameUrl": (self.first_frame_url or "").strip() or None,
                    "lastFrameUrl": (self.last_frame_url or "").strip() or None,
                    "model": (self.model or "").strip() or None,
                    "maxPriceUsd": price_limit(cap),
                }
            )
            return treza.start_quoted(cap, lambda: treza.request("make_video", args))

        return self._render(start, "video", 300)
