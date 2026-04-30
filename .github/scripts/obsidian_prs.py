import os
import re
import requests

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]
README = "README.md"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_my_prs():
    r = requests.get(
        "https://api.github.com/repos/obsidianmd/obsidian-releases/pulls",
        headers=headers,
        params={"state": "open", "per_page": 100}
    )
    return [pr for pr in r.json() if pr["user"]["login"] == USERNAME]

def get_review_status(pr_number):
    r = requests.get(
        f"https://api.github.com/repos/obsidianmd/obsidian-releases/pulls/{pr_number}/reviews",
        headers=headers
    )
    reviews = r.json()
    if not reviews:
        return "⏳ Awaiting Review"
    latest = reviews[-1]["state"]
    return {
        "APPROVED": "✅ Approved",
        "CHANGES_REQUESTED": "🔴 Changes Requested",
        "COMMENTED": "💬 Comment Left",
        "DISMISSED": "❌ Dismissed"
    }.get(latest, "⏳ Awaiting Review")

def get_type(pr):
    files_r = requests.get(
        f"https://api.github.com/repos/obsidianmd/obsidian-releases/pulls/{pr['number']}/files",
        headers=headers
    )
    files = [f["filename"] for f in files_r.json()]
    if any("community-css-themes" in f for f in files):
        return "🎨 Theme"
    if any("community-plugins" in f for f in files):
        return "🔌 Plugin"
    return "❓ Unknown"

def build_table(prs):
    if not prs:
        return "_No open PRs on obsidian-releases._"

    lines = [
        "| Name | Type | Status | Opened | PR |",
        "|------|------|--------|--------|----|"
    ]

    for pr in prs:
        name = pr["title"]
        number = pr["number"]
        opened = pr["created_at"][:10]
        status = get_review_status(number)
        kind = get_type(pr)
        url = pr["html_url"]
        lines.append(f"| {name} | {kind} | {status} | {opened} | [#{number}]({url}) |")

    return "\n".join(lines)

def update_readme(content):
    with open(README, "r") as f:
        readme = f.read()

    start = "<!-- OBSIDIAN-PRS:START -->"
    end = "<!-- OBSIDIAN-PRS:END -->"
    block = f"{start}\n{content}\n{end}"

    if start in readme:
        readme = re.sub(f"{re.escape(start)}.*?{re.escape(end)}", block, readme, flags=re.DOTALL)
    else:
        readme += f"\n\n{block}\n"

    with open(README, "w") as f:
        f.write(readme)

prs = get_my_prs()
table = build_table(prs)
update_readme(table)
print(f"Found {len(prs)} PR(s).")
