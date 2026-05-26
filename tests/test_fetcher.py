import urllib.parse
from unittest.mock import MagicMock, patch

import pytest

from claw2manus.fetcher import SkillFetcher, _quote_path_segment


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
    expected_url = SkillFetcher.GITHUB_SEARCH_API_URL.format(name=f'"{quoted_name}"')

    with patch("claw2manus.fetcher.requests.get") as mock_get:
        mock_response = MagicMock(status_code=200)
        mock_response.json.return_value = {"total_count": 0}
        mock_get.return_value = mock_response
        fetcher.discover_author_via_github(name)

        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert args[0] == expected_url
        assert kwargs["timeout"] == (3.05, 10)
