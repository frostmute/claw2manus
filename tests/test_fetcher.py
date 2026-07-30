import urllib.parse
from unittest.mock import MagicMock, patch

import pytest

from claw2manus.fetcher import RequestException, SkillFetcher, _quote_path_segment


# --- Escaping / injection tests (from original PR) ---


@pytest.mark.parametrize(
    "author,name",
    [
        ("user/repo", "skill#name"),
        ("..", ".."),
    ],
)
def test_fetch_skill_from_github_escaping(author, name):
    fetcher = SkillFetcher()
    expected_author = _quote_path_segment(author)
    expected_name = _quote_path_segment(name)
    expected_url = (
        "https://raw.githubusercontent.com/openclaw/skills/main/skills/"
        f"{expected_author}/{expected_name}/SKILL.md"
    )

    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, text="content")
        fetcher.fetch_skill_from_github(author, name)

        mock_get.assert_called_once_with(expected_url, timeout=(3.05, 10))


def test_fetch_skill_from_clawhub_website_escaping():
    fetcher = SkillFetcher()
    name = "skill name?"
    expected_name = _quote_path_segment(name)
    expected_url = f"https://clawhub.ai/skills/{expected_name}"

    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_get.return_value = MagicMock(status_code=200, text="<html></html>")
        with patch("claw2manus.fetcher.BeautifulSoup") as mock_soup:
            mock_soup.return_value.find.return_value = None
            fetcher.fetch_skill_from_clawhub_website(name)

        mock_get.assert_called_once_with(expected_url, timeout=(3.05, 10))


def test_discover_author_via_github_escaping():
    fetcher = SkillFetcher()
    name = "skill/name"
    quoted_name = _quote_path_segment(name)
    expected_url = SkillFetcher.GITHUB_SEARCH_API_URL.format(name=quoted_name)

    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"total_count": 0}
        mock_get.return_value = mock_response
        fetcher.discover_author_via_github(name)

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == expected_url
        assert kwargs["timeout"] == (3.05, 10)


def test_raw_github_url_from_nested_raw_path():
    fetcher = SkillFetcher()
    raw_url = (
        "https://raw.githubusercontent.com/Xquik-dev/tweetclaw/master/"
        "skills/tweetclaw/SKILL.md"
    )

    assert fetcher._raw_github_url_from_identifier(raw_url) == (raw_url, "tweetclaw")


def test_raw_github_url_from_blob_path():
    fetcher = SkillFetcher()

    assert fetcher._raw_github_url_from_identifier(
        "https://github.com/Xquik-dev/tweetclaw/blob/master/skills/tweetclaw/SKILL.md"
    ) == (
        "https://raw.githubusercontent.com/Xquik-dev/tweetclaw/master/skills/tweetclaw/SKILL.md",
        "tweetclaw",
    )


def test_raw_github_url_from_blob_path_quotes_segments():
    fetcher = SkillFetcher()

    assert fetcher._raw_github_url_from_identifier(
        "https://github.com/org name/repo/blob/main/skills/tweet claw/SKILL.md"
    ) == (
        "https://raw.githubusercontent.com/"
        f"{urllib.parse.quote('org name', safe='')}/repo/main/skills/"
        f"{urllib.parse.quote('tweet claw', safe='')}/SKILL.md",
        "tweet claw",
    )


# --- Functional tests ---


def test_fetch_skill_from_github_success():
    fetcher = SkillFetcher()
    expected_url = SkillFetcher.CLAW_HUB_RAW_GITHUB_URL.format(
        author=_quote_path_segment("author1"),
        name=_quote_path_segment("skill1"),
    )
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "test skill content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        content = fetcher.fetch_skill_from_github("author1", "skill1")
        assert content == "test skill content"
        mock_get.assert_called_once_with(expected_url, timeout=(3.05, 10))


def test_fetch_skill_from_github_failure():
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_get.side_effect = RequestException("Network error")

        content = fetcher.fetch_skill_from_github("author1", "skill1")
        assert content is None


def test_fetch_skill_from_raw_github_url_success():
    fetcher = SkillFetcher()
    raw_url = "https://raw.githubusercontent.com/org/repo/main/skills/demo/SKILL.md"
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "raw skill content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        content = fetcher.fetch_skill_from_raw_github_url(raw_url)
        assert content == "raw skill content"
        mock_get.assert_called_once_with(raw_url, timeout=(3.05, 10))


def test_fetch_skill_from_raw_github_url_failure():
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_get.side_effect = RequestException("Network error")

        content = fetcher.fetch_skill_from_raw_github_url(
            "https://raw.githubusercontent.com/org/repo/main/skills/demo/SKILL.md"
        )
        assert content is None


@patch("claw2manus.fetcher.BeautifulSoup")
def test_fetch_skill_from_clawhub_website_success_markdown(mock_bs):
    fetcher = SkillFetcher()
    expected_url = SkillFetcher.CLAW_HUB_WEBSITE_URL.format(
        name=_quote_path_segment("skill1")
    )
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = (
            '<html><body><div class="markdown-body">test content</div></body></html>'
        )
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        mock_soup = MagicMock()
        mock_content_element = MagicMock()
        mock_content_element.get_text.return_value = "test content"
        mock_soup.find.return_value = mock_content_element
        mock_bs.return_value = mock_soup

        content = fetcher.fetch_skill_from_clawhub_website("skill1")
        assert content == "test content"
        mock_get.assert_called_once_with(expected_url, timeout=(3.05, 10))


@patch("claw2manus.fetcher.BeautifulSoup")
def test_fetch_skill_from_clawhub_website_success_code(mock_bs):
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "<html><body><pre>test content</pre></body></html>"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        mock_soup = MagicMock()
        mock_soup.find.side_effect = [
            None,
            None,
            MagicMock(get_text=lambda: "test content"),
        ]
        mock_bs.return_value = mock_soup

        content = fetcher.fetch_skill_from_clawhub_website("skill1")
        assert content == "test content"


def test_fetch_skill_from_clawhub_website_failure():
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_get.side_effect = RequestException("Network error")

        content = fetcher.fetch_skill_from_clawhub_website("skill1")
        assert content is None


def test_discover_author_via_github_success():
    fetcher = SkillFetcher()
    quoted = _quote_path_segment("skill2")
    expected_url = SkillFetcher.GITHUB_SEARCH_API_URL.format(name=quoted)
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total_count": 1,
            "items": [{"path": "skills/author2/skill2/SKILL.md"}],
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        author = fetcher.discover_author_via_github("skill2")
        assert author == "author2"
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == expected_url
        assert kwargs["timeout"] == (3.05, 10)
        assert kwargs["headers"]["User-Agent"] == "claw2manus"


def test_discover_author_via_github_not_found():
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"total_count": 0, "items": []}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        author = fetcher.discover_author_via_github("skill2")
        assert author is None


def test_discover_author_via_github_exception():
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_get.side_effect = Exception("Some error")

        author = fetcher.discover_author_via_github("skill2")
        assert author is None


def test_fetch_skill_with_github_url():
    fetcher = SkillFetcher()
    raw_url = (
        "https://raw.githubusercontent.com/openclaw/skills/main/skills/author3/"
        "skill3/SKILL.md"
    )
    with patch.object(
        fetcher, "fetch_skill_from_raw_github_url", return_value="github content"
    ) as mock_fetch:
        content, name = fetcher.fetch_skill(raw_url)
        assert content == "github content"
        assert name == "skill3"
        mock_fetch.assert_called_once_with(raw_url)


def test_fetch_skill_with_nested_raw_github_url():
    fetcher = SkillFetcher()
    raw_url = (
        "https://raw.githubusercontent.com/Xquik-dev/tweetclaw/master/"
        "skills/tweetclaw/SKILL.md"
    )
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "---\nname: tweetclaw\n---\n# TweetClaw"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        content, skill_name = fetcher.fetch_skill(raw_url)

        assert content == "---\nname: tweetclaw\n---\n# TweetClaw"
        assert skill_name == "tweetclaw"
        mock_get.assert_called_once_with(raw_url, timeout=(3.05, 10))


def test_fetch_skill_converts_github_blob_url_to_raw():
    fetcher = SkillFetcher()
    raw_url = (
        "https://raw.githubusercontent.com/Xquik-dev/tweetclaw/master/"
        "skills/tweetclaw/SKILL.md"
    )
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "---\nname: tweetclaw\n---\n# TweetClaw"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        content, skill_name = fetcher.fetch_skill(
            "https://github.com/Xquik-dev/tweetclaw/blob/master/"
            "skills/tweetclaw/SKILL.md",
        )

        assert content == "---\nname: tweetclaw\n---\n# TweetClaw"
        assert skill_name == "tweetclaw"
        mock_get.assert_called_once_with(raw_url, timeout=(3.05, 10))


def test_fetch_skill_github_url_failure_does_not_fall_through():
    fetcher = SkillFetcher()
    raw_url = (
        "https://raw.githubusercontent.com/Xquik-dev/tweetclaw/master/"
        "skills/tweetclaw/SKILL.md"
    )
    with (
        patch.object(
            fetcher, "fetch_skill_from_raw_github_url", return_value=None
        ) as mock_raw,
        patch.object(fetcher, "fetch_skill_from_github") as mock_github,
    ):
        content, skill_name = fetcher.fetch_skill(
            "https://github.com/Xquik-dev/tweetclaw/blob/master/"
            "skills/tweetclaw/SKILL.md",
        )

        assert content is None
        assert skill_name is None
        mock_raw.assert_called_once_with(raw_url)
        mock_github.assert_not_called()


def test_fetch_skill_with_author_and_name():
    fetcher = SkillFetcher()
    with patch.object(
        fetcher, "fetch_skill_from_github", return_value="github content"
    ) as mock_fetch:
        content, name = fetcher.fetch_skill("author4/skill4")
        assert content == "github content"
        assert name == "skill4"
        mock_fetch.assert_called_once_with("author4", "skill4")


def test_fetch_skill_with_discovery():
    fetcher = SkillFetcher()
    with (
        patch.object(
            fetcher,
            "fetch_skill_from_github",
            side_effect=[None, None, "discovered content"],
        ) as mock_github,
        patch.object(
            fetcher, "discover_author_via_github", return_value="author5"
        ) as mock_discover,
    ):
        content, name = fetcher.fetch_skill("skill5")

        assert content == "discovered content"
        assert name == "skill5"
        mock_discover.assert_called_once_with("skill5")
        assert mock_github.call_count == 3


def test_fetch_skill_fallback_to_scraping():
    fetcher = SkillFetcher()
    with (
        patch.object(fetcher, "fetch_skill_from_github", return_value=None),
        patch.object(fetcher, "discover_author_via_github", return_value=None),
        patch.object(
            fetcher,
            "fetch_skill_from_clawhub_website",
            return_value="scraped content",
        ) as mock_scrape,
    ):
        content, name = fetcher.fetch_skill("skill6")

        assert content == "scraped content"
        assert name == "skill6"
        mock_scrape.assert_called_once_with("skill6")


def test_fetch_skill_not_found():
    fetcher = SkillFetcher()
    with (
        patch.object(fetcher, "fetch_skill_from_github", return_value=None),
        patch.object(fetcher, "discover_author_via_github", return_value=None),
        patch.object(fetcher, "fetch_skill_from_clawhub_website", return_value=None),
    ):
        content, name = fetcher.fetch_skill("skill7")

        assert content is None
        assert name is None


# --- GITHUB_TOKEN support ---


def test_no_github_token_no_auth_header(monkeypatch):
    """Without GITHUB_TOKEN, requests must be issued with no Authorization header."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetcher.fetch_skill_from_github("author", "skill")

        args, kwargs = mock_get.call_args
        # Either no headers=, or a headers dict with no Authorization
        assert "headers" not in kwargs or "Authorization" not in (kwargs.get("headers") or {})


def test_github_token_attaches_auth_header(monkeypatch):
    """With GITHUB_TOKEN set, fetch_skill_from_github sends an Authorization header."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_testtoken12345")
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetcher.fetch_skill_from_github("author", "skill")

        args, kwargs = mock_get.call_args
        assert kwargs.get("headers", {}).get("Authorization") == "Bearer ghp_testtoken12345"


def test_github_token_empty_string_no_header(monkeypatch):
    """An empty GITHUB_TOKEN should be treated as unauthenticated."""
    monkeypatch.setenv("GITHUB_TOKEN", "")
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetcher.fetch_skill_from_github("author", "skill")

        args, kwargs = mock_get.call_args
        assert "headers" not in kwargs or "Authorization" not in kwargs.get("headers", {})


def test_github_token_used_for_search_api(monkeypatch):
    """discover_author_via_github should also send the Authorization header."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_searchtest")
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {"total_count": 0}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetcher.discover_author_via_github("skill")

        args, kwargs = mock_get.call_args
        assert kwargs.get("headers", {}).get("Authorization") == "Bearer ghp_searchtest"


def test_github_token_used_for_raw_github_url(monkeypatch):
    """Raw-GitHub fetches should also use the token when set."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_rawtest")
    fetcher = SkillFetcher()
    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.text = "content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        fetcher.fetch_skill_from_raw_github_url(
            "https://raw.githubusercontent.com/org/repo/main/skills/demo/SKILL.md"
        )

        args, kwargs = mock_get.call_args
        assert kwargs.get("headers", {}).get("Authorization") == "Bearer ghp_rawtest"
