from __future__ import annotations

import logging
import re
import urllib.parse

import requests
from bs4 import BeautifulSoup

try:
    from requests.exceptions import RequestException
except (AttributeError, ImportError, ModuleNotFoundError):
    class RequestException(Exception):
        pass

logger = logging.getLogger(__name__)


def _quote_path_segment(value: str) -> str:
    """URL-encode a path segment; dots encoded to block traversal via '..'."""
    return urllib.parse.quote(value, safe="").replace(".", "%2E")


class SkillFetcher:
    CLAW_HUB_RAW_GITHUB_URL = "https://raw.githubusercontent.com/openclaw/skills/main/skills/{author}/{name}/SKILL.md"
    CLAW_HUB_WEBSITE_URL = "https://clawhub.ai/skills/{name}"
    GITHUB_SEARCH_API_URL = "https://api.github.com/search/code?q=repo:openclaw/skills+filename:SKILL.md+path:skills/*/{name}"

    def _skill_name_from_path(self, path: str) -> str | None:
        parts = [part for part in path.split("/") if part]
        if not parts or parts[-1].lower() != "skill.md":
            return None
        if len(parts) >= 2:
            return parts[-2]
        return None

    def _raw_github_url_from_identifier(
        self, skill_identifier: str
    ) -> tuple[str, str] | None:
        parsed = urllib.parse.urlparse(skill_identifier)
        netloc = parsed.netloc.lower()
        path_parts = [part for part in parsed.path.split("/") if part]

        if netloc == "raw.githubusercontent.com" and len(path_parts) >= 5:
            skill_name = self._skill_name_from_path("/".join(path_parts[3:]))
            if skill_name:
                return skill_identifier, skill_name

        if netloc in {"github.com", "www.github.com"} and len(path_parts) >= 5:
            owner, repo, marker, ref, *skill_path = path_parts
            if marker != "blob":
                return None
            skill_name = self._skill_name_from_path("/".join(skill_path))
            if not skill_name:
                return None
            raw_path = "/".join(
                urllib.parse.quote(part, safe="")
                for part in [owner, repo, ref, *skill_path]
            )
            return f"https://raw.githubusercontent.com/{raw_path}", skill_name

        return None

    def fetch_skill_from_raw_github_url(self, url: str) -> str | None:
        try:
            response = requests.get(url, timeout=(3.05, 10))
            response.raise_for_status()
            return response.text
        except RequestException:
            logger.exception("Error fetching raw GitHub skill")
            return None

    def fetch_skill_from_github(self, author: str, name: str) -> str | None:
        quoted_author = _quote_path_segment(author)
        quoted_name = _quote_path_segment(name)
        url = self.CLAW_HUB_RAW_GITHUB_URL.format(
            author=quoted_author, name=quoted_name
        )
        try:
            response = requests.get(url, timeout=(3.05, 10))
            response.raise_for_status()
            return response.text
        except RequestException:
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
        except RequestException:
            logger.exception("Error scraping from clawhub.ai")
            return None

    def discover_author_via_github(self, name: str) -> str | None:
        """Uses GitHub Search API to find the author of a skill."""
        quoted_name = _quote_path_segment(name)
        url = self.GITHUB_SEARCH_API_URL.format(name=quoted_name)
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

        is_github_skill_url = (
            "github.com" in skill_identifier or "githubusercontent.com" in skill_identifier
        ) and "skill.md" in skill_identifier.lower()
        if is_github_skill_url:
            github_target = self._raw_github_url_from_identifier(skill_identifier)
            if not github_target:
                return None, None
            raw_url, skill_name = github_target
            skill_content = self.fetch_skill_from_raw_github_url(raw_url)
            if skill_content:
                return skill_content, skill_name
            return None, None

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
