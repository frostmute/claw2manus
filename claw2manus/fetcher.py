import requests
import os
import re

class SkillFetcher:
    CLAW_HUB_RAW_GITHUB_URL = "https://raw.githubusercontent.com/openclaw/skills/main/skills/{author}/{name}/SKILL.md"
    CLAW_HUB_WEBSITE_URL = "https://clawhub.ai/skills/{name}"

    def fetch_skill_from_github(self, author: str, name: str) -> str | None:
        url = self.CLAW_HUB_RAW_GITHUB_URL.format(author=author, name=name)
        try:
            response = requests.get(url)
            response.raise_for_status()  # Raise an exception for HTTP errors
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Error fetching from GitHub: {e}")
            return None

    def fetch_skill_from_clawhub_website(self, name: str) -> str | None:
        # This is a placeholder. Scraping clawhub.ai would require a more sophisticated approach
        # (e.g., using BeautifulSoup) and is prone to breaking if the website structure changes).
        # For now, we will return None.
        print(f"Scraping from {self.CLAW_HUB_WEBSITE_URL.format(name=name)} is not fully implemented and may not work reliably.")
        print("Please provide a direct URL or ensure the skill is available on GitHub.")
        return None # Or implement actual scraping logic here

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
            
            # Fallback to scraping if GitHub fails and no author was specified
            skill_content = self.fetch_skill_from_clawhub_website(skill_identifier)
            if skill_content:
                skill_name = skill_identifier
                return skill_content, skill_name

        return None, None
