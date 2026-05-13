from __future__ import annotations

from claw2manus.fetcher import SkillFetcher


class FakeResponse:
    def __init__(self, text: str):
        self.text = text

    def raise_for_status(self):
        return None


def test_fetch_skill_from_nested_raw_github_url(monkeypatch):
    skill_text = "---\nname: tweetclaw\n---\n# TweetClaw"
    requested_urls: list[str] = []

    def fake_get(url, *args, **kwargs):
        requested_urls.append(url)
        return FakeResponse(skill_text)

    monkeypatch.setattr("claw2manus.fetcher.requests.get", fake_get)

    content, skill_name = SkillFetcher().fetch_skill(
        "https://raw.githubusercontent.com/Xquik-dev/tweetclaw/master/skills/tweetclaw/SKILL.md",
    )

    assert content == skill_text
    assert skill_name == "tweetclaw"
    assert requested_urls == [
        "https://raw.githubusercontent.com/Xquik-dev/tweetclaw/master/skills/tweetclaw/SKILL.md",
    ]


def test_fetch_skill_converts_github_blob_url_to_raw(monkeypatch):
    skill_text = "---\nname: tweetclaw\n---\n# TweetClaw"
    requested_urls: list[str] = []

    def fake_get(url, *args, **kwargs):
        requested_urls.append(url)
        return FakeResponse(skill_text)

    monkeypatch.setattr("claw2manus.fetcher.requests.get", fake_get)

    content, skill_name = SkillFetcher().fetch_skill(
        "https://github.com/Xquik-dev/tweetclaw/blob/master/skills/tweetclaw/SKILL.md",
    )

    assert content == skill_text
    assert skill_name == "tweetclaw"
    assert requested_urls == [
        "https://raw.githubusercontent.com/Xquik-dev/tweetclaw/master/skills/tweetclaw/SKILL.md",
    ]
