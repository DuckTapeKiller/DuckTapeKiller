import os
import requests
import re

def update_obsidian_prs():
    token = os.environ.get("GITHUB_TOKEN")
    username = os.environ.get("GITHUB_USERNAME", "DuckTapeKiller")
    repo = "obsidianmd/obsidian-releases"
    readme_path = "README.md"

    # Search API is more robust for finding PRs by specific authors in large repos
    query = f"is:pr is:open author:{username} repo:{repo}"
    url = f"https://api.github.com/search/issues?q={query}"
    
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }

    response = requests.get(url, headers=headers)
    
    if response.status_code != 200:
        print(f"API Error: {response.status_code} - {response.text}")
        return

    # Search API returns results in the 'items' key
    data = response.json()
    prs = data.get("items", [])

    if not prs:
        new_content = "_No open PRs on obsidian-releases._"
    else:
        table = ["| PR | Title | Status |", "| :--- | :--- | :--- |"]
        for pr in prs:
            table.append(f"| #{pr['number']} | [{pr['title']}]({pr['html_url']}) | {pr['state']} |")
        new_content = "\n".join(table)

    if not os.path.exists(readme_path):
        print("README.md not found.")
        return

    with open(readme_path, "r", encoding="utf-8") as f:
        readme_text = f.read()

    start_tag = "<!-- OBSIDIAN-PRS:START -->"
    end_tag = "<!-- OBSIDIAN-PRS:END -->"
    
    pattern = f"{re.escape(start_tag)}.*?{re.escape(end_tag)}"
    replacement = f"{start_tag}\n{new_content}\n{end_tag}"
    
    if not re.search(pattern, readme_text, flags=re.DOTALL):
        print("Markers not found in README.md. Ensure they exist!")
        return

    updated_readme = re.sub(pattern, replacement, readme_text, flags=re.DOTALL)

    with open(readme_path, "w", encoding="utf-8") as f:
        f.write(updated_readme)
    print("Successfully updated README.md")

if __name__ == "__main__":
    update_obsidian_prs()
