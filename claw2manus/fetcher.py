import logging
import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def _quote_path_segment(value: str) -> str:
    """URL-encode a path segment; dots encoded to block traversal via '..'."""
    return urllib.parse.quote(value, safe="").replace(".", "%2E")


class SkillFetcher:
    CLAW_HUB_RAW_GITHUB_URL = "https://raw.githubusercontent.com/openclaw/skills/main/skills/{author}/{name}/SKILL.md"
    CLAW_HUB_WEBSITE_URL = "https://clawhub.ai/skills/{name}"
    GITHUB_SEARCH_API_URL = "https://api.github.com/search/code?q=repo:openclaw/skills+filename:SKILL.md+path:skills/*/{name}"

    def fetch_skill_from_github(self, author: str, name: str) -> str | None:
        quoted_author = _quote_path_segment(author)
        quoted_name = _quote_path_segment(name)
        url = self.CLAW_HUB_RAW_GITHUB_URL.format(author=quoted_author, name=quoted_name)
        try:
            response = requests.get(url, timeout=(3.05, 10))
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException:
            logger.exception("Error fetching from GitHub")
            return None

    def fetch_skill_from_clawhub_website(self, name: str) -> str | None:
        """Scrapes SKILL.md content from clawhub.ai."""
        quoted_name = _quote_path_segment(name)
        url = self.CLAW_HUB_WEBSITE_URL.format(name=quoted_name)
        try:
            response = requests.get(url, timeout=(3.05, 10))
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")

            content_element = soup.find(class_="markdown-body") or soup.find("article")
            if content_element:
                return content_element.get_text()

            code_block = soup.find("pre") or soup.find("code")
            if code_block:
                return code_block.get_text()

            return None
        except requests.exceptions.RequestException:
            logger.exception("Error scraping from clawhub.ai")
            return None

    def discover_author_via_github(self, name: str) -> str | None:
        """Uses GitHub Search API to find the author of a skill."""
        quoted_name = _quote_path_segment(name)
        url = self.GITHUB_SEARCH_API_URL.format(name=f'"{quoted_name}"')
        headers = {"Accept": "application/vnd.github.v3+json"}
        try:
            response = requests.get(
                url,
                headers={**headers, "User-Agent": "claw2manus"},
                timeout=(3.05, 10),
            )
            response.raise_for_status()
            data = response.json()
            if data.get("total_count", 0) > 0:
                path = data["items"][0]["path"]
                match = re.search(r"skills/(?P<author>[^/]+)/", path)
                if match:
                    return match.group("author")
        except Exception:
            logger.exception("Error discovering author via GitHub")
        return None

    def fetch_skill(self, skill_identifier: str) -> tuple[str | None, str | None]:
        """
        Fetches a skill, trying GitHub first, then falling back to scraping.
        Returns (skill_content, skill_name).
        """
        skill_content = None
        skill_name = None

        if ("github.com" in skill_identifier or "githubusercontent.com" in skill_identifier) and "SKILL.md" in skill_identifier:
            match = re.search(
                r"skills/(?P<author>[^/]+)/(?P<name>[^/]+)/SKILL.md",
                skill_identifier,
            )
            if match:
                author = match.group("author")
                name = match.group("name")
                skill_content = self.fetch_skill_from_github(author, name)
                skill_name = name
                if skill_content:
                    return skill_content, skill_name

        if "/" in skill_identifier:
            author, name = skill_identifier.split("/", 1)
            skill_content = self.fetch_skill_from_github(author, name)
            skill_name = name
            if skill_content:
                return skill_content, skill_name
        else:
            common_authors = ["openclaw", "peterskoett"]
            for author in common_authors:
                skill_content = self.fetch_skill_from_github(author, skill_identifier)
                if skill_content:
                    skill_name = skill_identifier
                    return skill_content, skill_name

            logger.info(
                "Author not specified for '%s'. Attempting to discover via GitHub API...",
                skill_identifier,
            )
            discovered_author = self.discover_author_via_github(skill_identifier)
            if discovered_author:
                logger.info("Discovered author: %s", discovered_author)
                skill_content = self.fetch_skill_from_github(
                    discovered_author, skill_identifier
                )
                if skill_content:
                    return skill_content, skill_identifier

            quoted_name = _quote_path_segment(skill_identifier)
            logger.info(
                "Falling back to scraping from %s...",
                self.CLAW_HUB_WEBSITE_URL.format(name=quoted_name),
            )
            skill_content = self.fetch_skill_from_clawhub_website(skill_identifier)
            if skill_content:
                skill_name = skill_identifier
                return skill_content, skill_name

        return None, None
