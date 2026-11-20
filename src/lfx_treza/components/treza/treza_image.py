from __future__ import annotations

# Component first: lfx.io needs lfx.custom loaded, or the import is circular.
from lfx.custom.custom_component.component import Component  # noqa: F401

from lfx.io import DropdownInput, MessageTextInput, Output
from lfx.schema.data import Data

from lfx_treza._base import TrezaComponent, api_key_input, max_cost_input, wait_input
from lfx_treza._client import compact, price_limit

IMAGE_SHAPES = ["1:1", "16:9", "9:16", "4:5", "3:4", "4:3", "2:3", "3:2"]


class TrezaImageComponent(TrezaComponent):
    display_name = "Treza Image"
    description = "Make a picture from a description with Treza. Priced first, paid from prepaid Treza credits."
    name = "TrezaImage"

    inputs = [
        api_key_input(),
        MessageTextInput(name="prompt", display_name="Prompt", info="What the picture shows.", required=True, tool_mode=True),
        DropdownInput(
            name="aspect_ratio",
            display_name="Aspect Ratio",
            info='The picture\'s shape, for example "16:9" wide or "9:16" tall.',
            options=IMAGE_SHAPES,
            value="1:1",
        ),
        MessageTextInput(
            name="reference_image_urls",
            display_name="Reference Image URLs",
            info="Links to pictures in the Treza library to restyle or keep a character from, separated by commas.",
            advanced=True,
        ),
        MessageTextInput(name="model", display_name="Model", info="A Treza model ID. Leave empty for Treza's default.", advanced=True),
        max_cost_input(),
        wait_input(300),
    ]

    outputs = [Output(display_name="Image", name="image", method="generate_image")]

    def generate_image(self) -> Data:
        refs = [u.strip() for u in (self.reference_image_urls or "").split(",") if u.strip()]

        def start(treza, cap):
            args = compact(
                {
                    "prompt": (self.prompt or "").strip(),
                    "aspectRatio": self.aspect_ratio,
                    "model": (self.model or "").strip() or None,
                    "referenceImageUrls": refs or None,
                    "maxPriceUsd": price_limit(cap),
                }
            )
            return treza.start_quoted(cap, lambda: treza.request("make_image", args))

        return self._render(start, "image", 300)
