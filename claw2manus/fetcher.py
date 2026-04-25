import requests
import os
import re
import urllib.parse
from bs4 import BeautifulSoup

class SkillFetcher:
    CLAW_HUB_RAW_GITHUB_URL = "https://raw.githubusercontent.com/openclaw/skills/main/skills/{author}/{name}/SKILL.md"
    CLAW_HUB_WEBSITE_URL = "https://clawhub.ai/skills/{name}"
    GITHUB_SEARCH_API_URL = "https://api.github.com/search/code?q=repo:openclaw/skills+filename:SKILL.md+path:skills/*/{name}"

    def fetch_skill_from_github(self, author: str, name: str) -> str | None:
        quoted_author = urllib.parse.quote(author, safe='')
        quoted_name = urllib.parse.quote(name, safe='')
        url = self.CLAW_HUB_RAW_GITHUB_URL.format(author=quoted_author, name=quoted_name)
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching from GitHub: {e}")
            return None

    def fetch_skill_from_clawhub_website(self, name: str) -> str | None:
        """Scrapes SKILL.md content from clawhub.ai."""
        quoted_name = urllib.parse.quote(name, safe='')
        url = self.CLAW_HUB_WEBSITE_URL.format(name=quoted_name)
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Heuristic: find markdown content in common containers
            content_element = soup.find(class_='markdown-body') or soup.find('article')
            if content_element:
                return content_element.get_text()
            
            # Fallback: look for any large pre/code block
            code_block = soup.find('pre') or soup.find('code')
            if code_block:
                return code_block.get_text()

            return None
        except requests.exceptions.RequestException as e:
            print(f"Error scraping from clawhub.ai: {e}")
            return None

    def discover_author_via_github(self, name: str) -> str | None:
        """Uses GitHub Search API to find the author of a skill."""
        quoted_name = urllib.parse.quote(name, safe='')
        url = self.GITHUB_SEARCH_API_URL.format(name=quoted_name)
        headers = {"Accept": "application/vnd.github.v3+json"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            if data.get("total_count", 0) > 0:
                # Path format: skills/author/name/SKILL.md
                path = data["items"][0]["path"]
                match = re.search(r"skills/(?P<author>[^/]+)/", path)
                if match:
                    return match.group("author")
        except Exception as e:
            print(f"Error discovering author via GitHub: {e}")
        return None

    def fetch_skill(self, skill_identifier: str) -> tuple[str | None, str | None]:
        """
        Fetches a skill, trying GitHub first, then falling back to scraping.
        Returns (skill_content, skill_name).
        """
        skill_content = None
        skill_name = None

        # Try to parse as a GitHub URL first
        if "github.com" in skill_identifier and "SKILL.md" in skill_identifier:
            # Example: https://raw.githubusercontent.com/openclaw/skills/main/skills/peterskoett/self-improving-agent/SKILL.md
            match = re.search(r"skills/(?P<author>[^/]+)/(?P<name>[^/]+)/SKILL.md", skill_identifier)
            if match:
                author = match.group("author")
                name = match.group("name")
                skill_content = self.fetch_skill_from_github(author, name)
                skill_name = name
                if skill_content:
                    return skill_content, skill_name

        # Assume it's a skill name (e.g., "pwnclaw-security-scan")
        # We need to guess the author for GitHub. For now, we'll use a common one or require full path.
        # For simplicity, let's assume a default author or require the user to specify author/name.
        # For this task, we'll assume the user provides the full skill name as 'author/name' or just 'name' and we'll try 'openclaw' as author.
        if "/" in skill_identifier:
            author, name = skill_identifier.split("/", 1)
            skill_content = self.fetch_skill_from_github(author, name)
            skill_name = name
            if skill_content:
                return skill_content, skill_name
        else:
            # Try with a common author like 'openclaw' or 'peterskoett'
            common_authors = ["openclaw", "peterskoett"]
            for author in common_authors:
                skill_content = self.fetch_skill_from_github(author, skill_identifier)
                if skill_content:
                    skill_name = skill_identifier
                    return skill_content, skill_name
            
            # Try to discover author via GitHub Search API
            print(f"Author not specified for '{skill_identifier}'. Attempting to discover via GitHub API...")
            discovered_author = self.discover_author_via_github(skill_identifier)
            if discovered_author:
                print(f"Discovered author: {discovered_author}")
                skill_content = self.fetch_skill_from_github(discovered_author, skill_identifier)
                if skill_content:
                    return skill_content, skill_identifier

            # Fallback to scraping if GitHub fails and no author was specified
            quoted_skill_identifier = urllib.parse.quote(skill_identifier, safe='')
            print(f"Falling back to scraping from {self.CLAW_HUB_WEBSITE_URL.format(name=quoted_skill_identifier)}...")
            skill_content = self.fetch_skill_from_clawhub_website(skill_identifier)
            if skill_content:
                skill_name = skill_identifier
                return skill_content, skill_name

        return None, None
