import sys
import os
from git import Repo
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
import google.generativeai as genai

REPORT_FILE = "comment.txt"

# --- Rich UI Setup ---
console = Console()

# --- Gemini Setup ---
# Assumes GOOGLE_API_KEY is set in the environment
API_KEY = os.getenv("GOOGLE_API_KEY")
if not API_KEY:
    console.print("[bold red]GOOGLE_API_KEY environment variable not set! Exiting.")
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
    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), transient=True) as progress:
        progress.add_task(description="🤖 AI Agent is scanning repository...", total=None)
        try:
            repo = Repo(os.getcwd())
        except Exception as e:
            console.print(f"[bold red]Error: {e}")
            sys.exit(1)
        # Fetch latest origin/main
        repo.remotes.origin.fetch()
        merge_base = get_merge_base(repo)
        conflicts = detect_risky_moves(repo, merge_base)
    console.print(Panel("System Status: AI Agent Live", style="green"))
    if conflicts:
        console.print(f"[bold yellow]High Risk: Semantic Merge Conflicts Detected![/bold yellow]\n")
        for c in conflicts:
            console.print(f"[red]- {c['old_path']} → {c['new_path']}")
        gemini_report = analyze_with_gemini(conflicts)
        console.print(Panel.fit(gemini_report, title="Gemini Analysis", style="cyan"), markup=True)
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write(gemini_report)
        sys.exit(1)
    else:
        console.print("[bold green]No risky semantic merge conflicts detected.")
        with open(REPORT_FILE, "w", encoding="utf-8") as f:
            f.write("No risky semantic merge conflicts detected.")

if __name__ == "__main__":
    main()
