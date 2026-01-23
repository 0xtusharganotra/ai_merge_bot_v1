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
        error_msg = "❌ GEMINI_API_KEY environment variable not set!"
        console.print(f"[bold red]{error_msg}")
        write_report(error_msg)
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
            error_msg = f"❌ Error accessing git repository: {e}"
            console.print(f"[bold red]{error_msg}")
            write_report(error_msg)
            sys.exit(1)
        
        try:
            # Fetch latest origin/main
            repo.remotes.origin.fetch()
        except Exception as e:
            error_msg = f"❌ Error fetching origin: {e}"
            console.print(f"[bold red]{error_msg}")
            write_report(error_msg)
            sys.exit(1)
        
        try:
            merge_base = get_merge_base(repo)
            conflicts = detect_risky_moves(repo, merge_base)
        except Exception as e:
            error_msg = f"❌ Error analyzing repository: {e}"
            console.print(f"[bold red]{error_msg}")
            write_report(error_msg)
            sys.exit(1)
    
    console.print(Panel("System Status: AI Agent Live", style="green"))
    if conflicts:
        console.print(f"[bold yellow]High Risk: Semantic Merge Conflicts Detected![/bold yellow]\n")
        for c in conflicts:
            console.print(f"[red]- {c['old_path']} → {c['new_path']}")
        try:
            gemini_report = analyze_with_gemini(conflicts)
            console.print(Panel.fit(gemini_report, title="Gemini Analysis", style="cyan"), markup=True)
            write_report(gemini_report)
        except Exception as e:
            error_msg = f"❌ Error calling Gemini API: {e}"
            console.print(f"[bold red]{error_msg}")
            write_report(error_msg)
        sys.exit(1)
    else:
        console.print("[bold green]✅ No risky semantic merge conflicts detected.")
        write_report("✅ No risky semantic merge conflicts detected.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Merge Bot")
    parser.add_argument('--server', action='store_true', help='Run a web server showing bot status')
    args = parser.parse_args()
    if args.server:
        run_server()
    else:
        main()
