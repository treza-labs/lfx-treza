# lfx-treza

[Treza](https://www.trezalabs.com) components for [Langflow](https://www.langflow.org), as a Langflow Extension Bundle. Make AI pictures and video clips (Veo, Kling, Seedance and more) and run your saved Treza pipelines from a flow, or hand them to an Agent as tools. Treza prices every render first, and a Max cost you set stops any render that costs more, with nothing spent.

## Install

In the Python environment Langflow runs in:

```bash
pip install lfx-treza
```

Restart Langflow. The components appear under **Treza** in the components menu.

Create a Treza account at https://www.trezalabs.com, add credits, and make an API key at https://www.trezalabs.com/platform/api-keys with the `pipelines:read`, `pipelines:write` and `pipelines:run` permissions. Paste it into a component's **Treza API Key** field, or set `TREZA_API_KEY` in Langflow's environment (or as a Langflow global variable of that name).

The package is free. Renders are paid from your prepaid Treza credits; there is no subscription.

## Components

| Component | What it does | Cost |
| --- | --- | --- |
| Treza Image | A picture from a prompt, optionally from reference pictures. | Treza credits |
| Treza Video | A video clip from a prompt, optionally opening or ending on a picture. | Treza credits |
| Treza Run Pipeline | Runs one of your saved Treza pipelines, with new inputs as JSON. | Treza credits |
| Treza Get Run | Looks up a render that was still going when its component stopped waiting. | Free |
| Treza Balance | The credits left on the account. | Free |

Each returns a `Data` object. A finished render:

```json
{"url": "https://media.trezalabs.com/...png", "status": "success", "finished": true,
 "price_usd": 0.0, "model": "google/gemini-2.5-flash-image", "render_seconds": 12.0,
 "run_id": "...", "pipeline_id": "pipeline_..."}
```

### As agent tools

Turn on **Tool Mode** on a component and connect it to an Agent's **Tools** input. The agent fills in the prompt (or the pipeline ID and inputs); the API key, Max cost and wait stay as you set them on the canvas, so the agent cannot raise the cap.

## Spending

- **Max Cost (USD)**: with a cap set, Treza prices the render first. If the price is higher, the component returns `{"error": "This render costs $X, over the Max cost of $Y. Nothing was spent. ...", "code": "OverBudget"}` and starts nothing.
- Leave it at 0 for no cap. **Set a cap on components you give to an agent.**
- A render never starts when the balance does not cover its price.

## Long renders

Pictures usually take under a minute and videos one to five minutes. A component waits up to **Wait (seconds)** (advanced; 300 by default, 600 for pipelines). A render still going after that comes back with `"status": "running"` and its `run_id` and `pipeline_id`, and **Treza Get Run** returns the file once it is done. Nothing is started twice.

## Network and privacy

The components call Treza's API over HTTPS at `www.trezalabs.com`, sending the prompt and settings with your API key. Privacy policy: https://docs.trezalabs.com/terms-and-privacy/privacy

## Develop

```bash
pip install -e . pytest
pytest -q
```

The tests run against a scripted stand-in for Treza's API.

Treza is independent of Langflow and not endorsed by it. Issues: https://github.com/treza-labs/lfx-treza/issues · Email: hello@trezalabs.com · MIT licensed.
