import sys
from unittest.mock import MagicMock

# Mock dependencies before importing the module under test
mock_requests = MagicMock()
sys.modules['requests'] = mock_requests
sys.modules['bs4'] = MagicMock()

import pytest
from unittest.mock import patch
from claw2manus.fetcher import SkillFetcher
import urllib.parse

def test_fetch_skill_from_github_escaping():
    fetcher = SkillFetcher()
    author = "user/repo"
    name = "skill#name"

    mock_requests.get.return_value = MagicMock(status_code=200, text="content")
    fetcher.fetch_skill_from_github(author, name)

    expected_author = urllib.parse.quote(author, safe='')
    expected_name = urllib.parse.quote(name, safe='')
    expected_url = f"https://raw.githubusercontent.com/openclaw/skills/main/skills/{expected_author}/{expected_name}/SKILL.md"

    args, kwargs = mock_requests.get.call_args
    assert args[0] == expected_url

def test_fetch_skill_from_clawhub_website_escaping():
    fetcher = SkillFetcher()
    name = "skill name?"

    mock_requests.get.return_value = MagicMock(status_code=200, text="<html></html>")
    fetcher.fetch_skill_from_clawhub_website(name)

    expected_name = urllib.parse.quote(name, safe='')
    expected_url = f"https://clawhub.ai/skills/{expected_name}"

    args, kwargs = mock_requests.get.call_args
    assert args[0] == expected_url

def test_discover_author_via_github_escaping():
    fetcher = SkillFetcher()
    name = "skill/name"

    mock_requests.get.return_value = MagicMock(status_code=200)
    mock_requests.get.return_value.json.return_value = {"total_count": 0}
    fetcher.discover_author_via_github(name)

    expected_name = urllib.parse.quote(name, safe='')
    expected_url = f"https://api.github.com/search/code?q=repo:openclaw/skills+filename:SKILL.md+path:skills/*/{expected_name}"

    args, kwargs = mock_requests.get.call_args
    assert args[0] == expected_url
