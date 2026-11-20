"""A scripted Treza: answers each tool from a queue and records what was asked."""


class FakeResponse:
    def __init__(self, status, body):
        self.status_code = status
        self._body = body
        self.text = str(body)

    def json(self):
        return self._body


class FakeTreza:
    def __init__(self, **answers):
        self.answers = {tool: list(replies) for tool, replies in answers.items()}
        self.calls = []

    def post(self, url, json=None, headers=None, timeout=None):
        tool = url.rsplit("/", 1)[-1]
        self.calls.append((tool, json, headers))
        status, body = self.answers[tool].pop(0)
        return FakeResponse(status, body)

    def asked(self, tool):
        return [args for name, args, _ in self.calls if name == tool]
