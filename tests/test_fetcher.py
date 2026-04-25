import pytest
from unittest.mock import patch, MagicMock
from claw2manus.fetcher import SkillFetcher
import requests
import bs4

def test_fetch_skill_from_github_success():
    fetcher = SkillFetcher()
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = "test skill content"
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        content = fetcher.fetch_skill_from_github("author1", "skill1")
        assert content == "test skill content"
        mock_get.assert_called_once()

def test_fetch_skill_from_github_failure():
    fetcher = SkillFetcher()
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        content = fetcher.fetch_skill_from_github("author1", "skill1")
        assert content is None

@patch('claw2manus.fetcher.BeautifulSoup')
def test_fetch_skill_from_clawhub_website_success_markdown(mock_bs):
    fetcher = SkillFetcher()
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = '<html><body><div class="markdown-body">test content</div></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Setup mock BS
        mock_soup = MagicMock()
        mock_content_element = MagicMock()
        mock_content_element.get_text.return_value = "test content"
        mock_soup.find.return_value = mock_content_element
        mock_bs.return_value = mock_soup

        content = fetcher.fetch_skill_from_clawhub_website("skill1")
        assert content == "test content"

@patch('claw2manus.fetcher.BeautifulSoup')
def test_fetch_skill_from_clawhub_website_success_code(mock_bs):
    fetcher = SkillFetcher()
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.text = '<html><body><pre>test content</pre></body></html>'
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        # Setup mock BS
        mock_soup = MagicMock()
        # First call to find (markdown-body or article) returns None
        # Second call to find (pre or code) returns element
        mock_soup.find.side_effect = [None, None, MagicMock(get_text=lambda: "test content")]
        mock_bs.return_value = mock_soup

        content = fetcher.fetch_skill_from_clawhub_website("skill1")
        assert content == "test content"

def test_fetch_skill_from_clawhub_website_failure():
    fetcher = SkillFetcher()
    with patch('requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        content = fetcher.fetch_skill_from_clawhub_website("skill1")
        assert content is None

def test_discover_author_via_github_success():
    fetcher = SkillFetcher()
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total_count": 1,
            "items": [{"path": "skills/author2/skill2/SKILL.md"}]
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        author = fetcher.discover_author_via_github("skill2")
        assert author == "author2"

def test_discover_author_via_github_not_found():
    fetcher = SkillFetcher()
    with patch('requests.get') as mock_get:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "total_count": 0,
            "items": []
        }
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        author = fetcher.discover_author_via_github("skill2")
        assert author is None

def test_discover_author_via_github_exception():
    fetcher = SkillFetcher()
    with patch('requests.get') as mock_get:
        mock_get.side_effect = Exception("Some error")

        author = fetcher.discover_author_via_github("skill2")
        assert author is None

def test_fetch_skill_with_github_url():
    fetcher = SkillFetcher()
    with patch.object(fetcher, 'fetch_skill_from_github', return_value="github content") as mock_fetch:
        content, name = fetcher.fetch_skill("https://raw.githubusercontent.com/openclaw/skills/main/skills/author3/skill3/SKILL.md")
        assert content == "github content"
        assert name == "skill3"

def test_fetch_skill_with_author_and_name():
    fetcher = SkillFetcher()
    with patch.object(fetcher, 'fetch_skill_from_github', return_value="github content") as mock_fetch:
        content, name = fetcher.fetch_skill("author4/skill4")
        assert content == "github content"
        assert name == "skill4"
        mock_fetch.assert_called_once_with("author4", "skill4")

def test_fetch_skill_with_discovery():
    fetcher = SkillFetcher()
    with patch.object(fetcher, 'fetch_skill_from_github', side_effect=[None, None, "discovered content"]) as mock_github, \
         patch.object(fetcher, 'discover_author_via_github', return_value="author5") as mock_discover:

        content, name = fetcher.fetch_skill("skill5")

        assert content == "discovered content"
        assert name == "skill5"
        mock_discover.assert_called_once_with("skill5")
        assert mock_github.call_count == 3

def test_fetch_skill_fallback_to_scraping():
    fetcher = SkillFetcher()
    with patch.object(fetcher, 'fetch_skill_from_github', return_value=None), \
         patch.object(fetcher, 'discover_author_via_github', return_value=None), \
         patch.object(fetcher, 'fetch_skill_from_clawhub_website', return_value="scraped content") as mock_scrape:

        content, name = fetcher.fetch_skill("skill6")

        assert content == "scraped content"
        assert name == "skill6"
        mock_scrape.assert_called_once_with("skill6")

def test_fetch_skill_not_found():
    fetcher = SkillFetcher()
    with patch.object(fetcher, 'fetch_skill_from_github', return_value=None), \
         patch.object(fetcher, 'discover_author_via_github', return_value=None), \
         patch.object(fetcher, 'fetch_skill_from_clawhub_website', return_value=None):

        content, name = fetcher.fetch_skill("skill7")

        assert content is None
        assert name is None
