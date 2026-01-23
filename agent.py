import argparse
import sys
import os
from git import Repo
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import google.generativeai as genai

try:
    from flask import Flask
except ImportError:
    Flask = None

REPORT_FILE = "comment.txt"

# --- Rich UI Setup ---
console = Console()

def write_report(message):
    """Always write a report file."""
    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        f.write(message)
    console.print(f"[dim]Report written to {REPORT_FILE}[/dim]")

def generate_report_header():
    """Generate a professional report header."""
    return """# 🤖 AI MERGE GUARD - Analysis Report

---

**Automated Semantic Merge Conflict Detection**

---

"""

def generate_success_report():
    """Generate a detailed success report."""
    return generate_report_header() + """## ✅ Status: ALL CHECKS PASSED

### Summary
The AI Merge Guard has successfully analyzed this pull request and found **no risky semantic merge conflicts**.

### What was checked:
- 🔍 Scanned for files moved/renamed in this PR
- 🔍 Cross-referenced with modifications in the target branch
- 🔍 Analyzed potential semantic conflicts that Git might miss

### Result
Your changes are safe to merge. No files were moved that have also been modified in the main branch.
"""

def generate_conflict_report(conflicts, gemini_analysis):
    """Generate a detailed conflict report."""
    conflict_list = "\n".join([f"- `{c['old_path']}` → `{c['new_path']}`" for c in conflicts])
    return generate_report_header() + f"""## ⚠️ Status: RISKY MERGE DETECTED

### Summary
The AI Merge Guard has detected **{len(conflicts)} potential semantic merge conflict(s)** that require your attention.

### Detected Conflicts
The following files were **moved/renamed in this PR** but have also been **modified in the main branch**:

{conflict_list}

### Why This Matters
When a file is moved in your branch while someone else modifies the original file in main, Git may not properly merge these changes. This can lead to:
- Lost code changes
- Unexpected behavior after merge
- Silent failures that are hard to debug

---

## 🧠 Gemini AI Analysis

{gemini_analysis}

---

### Recommended Actions
1. Review the conflicts listed above
2. Follow the Git commands provided by Gemini
3. Test thoroughly after resolving conflicts
4. Re-run the PR checks after fixes

---

*This automated check helps prevent subtle merge issues where file relocations can cause changes to be lost or overwritten.*

> **AI Merge Guard** - Keeping your codebase safe, one merge at a time. 🛡️
"""

def generate_error_report(error_msg):
    """Generate a detailed error report."""
    return generate_report_header() + f"""## ❌ Status: ANALYSIS ERROR

### Summary
The AI Merge Guard encountered an error while analyzing this pull request.

### Error Details
```
{error_msg}
```

### Possible Causes
- Missing or invalid API key
- Repository access issues
- Network connectivity problems
- Git configuration issues

### Recommended Actions
1. Check that the `GEMINI_API_KEY` secret is properly configured
2. Ensure the repository has proper permissions
3. Re-run the workflow
4. Contact the repository maintainer if the issue persists

---

> **AI Merge Guard** - Keeping your codebase safe, one merge at a time. 🛡️
"""

def run_server():
    if Flask is None:
        print("Flask is not installed. Please install Flask to use the server mode.")
        sys.exit(1)
    app = Flask(__name__)

    @app.route('/')
    def home():
        return '<h1>AI Agent running...</h1>'

    app.run(host='0.0.0.0', port=8080)

# --- Gemini Setup ---
# Assumes GEMINI_API_KEY is set in the environment
API_KEY = os.getenv("GEMINI_API_KEY")

def configure_gemini():
    if not API_KEY:
        error_msg = "GEMINI_API_KEY environment variable not set!"
        console.print(f"[bold red]{error_msg}")
        write_report(generate_error_report(error_msg))
        sys.exit(1)
    genai.configure(api_key=API_KEY)

# --- Git Logic ---
def get_merge_base(repo):
    """Find the common ancestor between HEAD and origin/main."""
    origin_main = repo.commit('origin/main')
    head = repo.commit('HEAD')
    return repo.git.merge_base(head, origin_main)

def detect_risky_moves(repo, merge_base):
    """Detect files moved in HEAD but modified in origin/main."""
    # Diff from merge_base to HEAD (PR branch)
    pr_diff = repo.git.diff('--name-status', f'{merge_base}..HEAD').splitlines()
    # Diff from merge_base to origin/main
    main_diff = repo.git.diff('--name-status', f'{merge_base}..origin/main').splitlines()

    moved_files = {}
    for line in pr_diff:
        if line.startswith('R'):
            parts = line.split('\t')
            if len(parts) == 3:
                _, old_path, new_path = parts
                moved_files[old_path] = new_path
    modified_in_main = set()
    for line in main_diff:
        if line.startswith('M'):
            _, path = line.split('\t')
            modified_in_main.add(path)
    # Conflict: file moved in PR, but modified in main at old path
    conflicts = []
    for old_path, new_path in moved_files.items():
        if old_path in modified_in_main:
            conflicts.append({'old_path': old_path, 'new_path': new_path})
    return conflicts

def analyze_with_gemini(conflicts):
    prompt = (
        "You are a Senior DevOps Architect. A risky merge has been detected. "
        "The user moved files that were edited by someone else.\n"
        "Output 1: Explain the conflict context clearly.\n"
        "Output 2: Provide exact git commands to resolve it (e.g., git checkout origin/main -- <file>).\n"
        f"Conflicts: {conflicts}"
    )
    model = genai.GenerativeModel('gemini-pro')
    response = model.generate_content(prompt)
    return response.text

def main():
    configure_gemini()
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(description="🤖 AI Agent is scanning repository...", total=None)
        try:
            repo = Repo(os.getcwd())
        except Exception as e:
            error_msg = f"Error accessing git repository: {e}"
            console.print(f"[bold red]{error_msg}")
            write_report(generate_error_report(error_msg))
            sys.exit(1)
        
        try:
            # Fetch latest origin/main
            repo.remotes.origin.fetch()
        except Exception as e:
            error_msg = f"Error fetching origin: {e}"
            console.print(f"[bold red]{error_msg}")
            write_report(generate_error_report(error_msg))
            sys.exit(1)
        
        try:
            merge_base = get_merge_base(repo)
            conflicts = detect_risky_moves(repo, merge_base)
        except Exception as e:
            error_msg = f"Error analyzing repository: {e}"
            console.print(f"[bold red]{error_msg}")
            write_report(generate_error_report(error_msg))
            sys.exit(1)
    
    console.print(Panel("System Status: AI Agent Live", style="green"))
    if conflicts:
        console.print(f"[bold yellow]High Risk: Semantic Merge Conflicts Detected![/bold yellow]\n")
        for c in conflicts:
            console.print(f"[red]- {c['old_path']} → {c['new_path']}")
        try:
            gemini_report = analyze_with_gemini(conflicts)
            console.print(Panel.fit(gemini_report, title="Gemini Analysis", style="cyan"), markup=True)
            write_report(generate_conflict_report(conflicts, gemini_report))
        except Exception as e:
            error_msg = f"Error calling Gemini API: {e}"
            console.print(f"[bold red]{error_msg}")
            write_report(generate_error_report(error_msg))
        sys.exit(1)
    else:
        console.print("[bold green]✅ No risky semantic merge conflicts detected.")
        write_report(generate_success_report())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Merge Bot")
    parser.add_argument('--server', action='store_true', help='Run a web server showing bot status')
    args = parser.parse_args()
    if args.server:
        run_server()
    else:
        main()
