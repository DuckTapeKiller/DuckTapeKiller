import os
import requests

USERNAME = os.environ["GITHUB_USERNAME"]
TOKEN = os.environ["GITHUB_TOKEN"]
README = "README.md"

headers = {
    "Authorization": f"token {TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_repos():
    repos, page = [], 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{USERNAME}/repos",
            headers=headers,
            params={"per_page": 100, "page": page}
        )
        data = r.json()
        if not data:
            break
        repos.extend(data)
        page += 1
    return repos

def get_releases(repo):
    r = requests.get(
        f"https://api.github.com/repos/{USERNAME}/{repo}/releases",
        headers=headers,
        params={"per_page": 100}
    )
    return r.json()

def build_chart(repos):
    stats = []
    total_downloads = 0

    for repo in repos:
        releases = get_releases(repo["name"])
        if not releases:
            continue
        downloads = sum(
            asset["download_count"]
            for rel in releases
            for asset in rel.get("assets", [])
        )
        if downloads == 0:
            continue
        stats.append({
            "name": repo["name"],
            "releases": len(releases),
            "latest": releases[0]["tag_name"],
            "downloads": downloads
        })
        total_downloads += downloads

    if not stats:
        return "_No releases with downloads found._"

    stats.sort(key=lambda x: x["downloads"], reverse=True)
    max_dl = stats[0]["downloads"]
    bar_width = 20

    lines = [
        "| Repository | Latest | Releases | Downloads | Chart |",
        "|------------|--------|----------|-----------|-------|"
    ]

    for s in stats:
        bar_len = round((s["downloads"] / max_dl) * bar_width)
        bar = "█" * bar_len + "░" * (bar_width - bar_len)
        lines.append(
            f"| [{s['name']}](https://github.com/{USERNAME}/{s['name']}) "
            f"| `{s['latest']}` "
            f"| {s['releases']} "
            f"| {s['downloads']:,} "
            f"| `{bar}` |"
        )

    lines.append(f"\n> **Total downloads across all releases: {total_downloads:,}**")
    return "\n".join(lines)

def update_readme(content):
    with open(README, "r") as f:
        readme = f.read()

    start = "<!-- RELEASE-STATS:START -->"
    end = "<!-- RELEASE-STATS:END -->"

    block = f"{start}\n{content}\n{end}"
    if start in readme:
        import re
        readme = re.sub(f"{re.escape(start)}.*?{re.escape(end)}", block, readme, flags=re.DOTALL)
    else:
        readme += f"\n\n{block}\n"

    with open(README, "w") as f:
        f.write(readme)

repos = get_repos()
chart = build_chart(repos)
update_readme(chart)
print("Done.")
