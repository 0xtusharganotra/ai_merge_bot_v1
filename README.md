# AI Merge Bot v1

An intelligent DevOps tool designed to detect and analyze risky semantic merge conflicts in Git repositories. The bot leverages Google's Gemini AI to provide detailed explanations and actionable resolutions for detected conflicts.

## Overview

AI Merge Bot v1 focuses on scenarios where files have been moved in a pull request (PR) branch but have also been modified in the main branch. These situations can lead to semantic merge conflicts that traditional Git merge algorithms might miss.

## Technologies Used

- **Python 3.9**
- **GitPython**: For interacting with Git repositories programmatically
- **Rich**: For beautiful console output and progress indicators
- **Google Generative AI (Gemini)**: For advanced conflict analysis and resolution suggestions
- **Docker**: For containerized deployment

## Prerequisites

- Docker (for containerized usage)
- Python 3.9+ (for local usage)
- Google Gemini API key ([Get one here](https://ai.google.dev/))

## Setup

### Getting a Gemini API Key

1. Visit [Google AI Studio](https://ai.google.dev/)
2. Sign in with your Google account
3. Generate an API key
4. Keep the key secure and never commit it to version control

### Environment Variable Setup

The bot requires the `GEMINI_API_KEY` environment variable to be set. This key is used to authenticate with Google's Gemini AI service.

## Usage

### Option 1: Using Docker (Recommended)

#### Build the Docker Image

```bash
docker build -t ai-merge-agent .
```

#### Run the Docker Container

```bash
docker run --rm \
  -v "$(pwd):/workspace" \
  -w /workspace \
  -e GEMINI_API_KEY="your_api_key_here" \
  ai-merge-agent
```

**Important Notes:**
- Replace `your_api_key_here` with your actual Gemini API key
- The `-e GEMINI_API_KEY="..."` flag passes the environment variable to the container
- The `-v` flag mounts your current directory to `/workspace` in the container
- The `-w` flag sets the working directory inside the container

#### Example with Real Repository

```bash
cd /path/to/your/git/repository
docker run --rm \
  -v "$(pwd):/workspace" \
  -w /workspace \
  -e GEMINI_API_KEY="${GEMINI_API_KEY}" \
  ai-merge-agent
```

### Option 2: Local Python Execution

#### Install Dependencies

```bash
pip install -r requirements.txt
```

#### Set Environment Variable

**On Linux/macOS:**
```bash
export GEMINI_API_KEY="your_api_key_here"
```

**On Windows (Command Prompt):**
```cmd
set GEMINI_API_KEY=your_api_key_here
```

**On Windows (PowerShell):**
```powershell
$env:GEMINI_API_KEY="your_api_key_here"
```

#### Run the Bot

```bash
python agent.py
```

Make sure you are in the root directory of your Git repository.

### Option 3: GitHub Actions Integration

The bot can be integrated into your GitHub Actions workflow to automatically check pull requests.

#### Setup Steps

1. Go to your GitHub repository → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `GEMINI_API_KEY`
4. Value: Your Gemini API key
5. Click "Add secret"

The workflow file `.github/workflows/ai-merge-guard.yml` is already configured to use this secret.

## How It Works

1. **Environment Setup**: The bot checks for the `GEMINI_API_KEY` environment variable
2. **Repository Analysis**:
   - Fetches the latest `origin/main` branch
   - Finds the merge base between the current `HEAD` and `origin/main`
   - Detects files that have been moved in the PR branch and also modified in the main branch
3. **Conflict Analysis**:
   - If risky moves are detected, the bot uses Gemini AI to explain the conflict and suggest exact Git commands to resolve it
   - The analysis is printed to the console and saved to `comment.txt`
   - If no conflicts are found, a success message is displayed

## Output

- **Console**: Rich-formatted status messages and analysis
- **comment.txt**: Detailed report saved in the working directory

## Error Handling

- The bot will exit with a clear error message if `GEMINI_API_KEY` is not set
- If the repository cannot be accessed, an error will be displayed
- If risky semantic merge conflicts are detected, the bot exits with status code 1

## Project Structure

```
.
├── agent.py              # Main script containing all logic
├── requirements.txt      # Python dependencies
├── Dockerfile           # Docker container configuration
├── README.md           # This file
└── .github/
    └── workflows/
        └── ai-merge-guard.yml  # GitHub Actions workflow
```

## Security Notes

- **Never commit your GEMINI_API_KEY to version control**
- Use environment variables or secrets management systems
- In CI/CD pipelines, use encrypted secrets (e.g., GitHub Secrets)
- The Dockerfile declares the `GEMINI_API_KEY` environment variable but does not set a default value for security

## Troubleshooting

### "GEMINI_API_KEY environment variable not set! Exiting."

**Solution**: Make sure you've set the environment variable correctly:
- For Docker: Use the `-e GEMINI_API_KEY="your_key"` flag
- For local execution: Export the variable in your shell
- For GitHub Actions: Add the secret in repository settings

### Docker container doesn't have access to the API key

**Solution**: Verify you're passing the environment variable with the `-e` flag:
```bash
docker run --rm -e GEMINI_API_KEY="your_key" ...
```

### Git repository not found

**Solution**: Ensure you're mounting the correct directory and setting the working directory:
```bash
docker run --rm -v "$(pwd):/workspace" -w /workspace ...
```

## Contributing

Contributions are welcome! Please ensure that:
- Code follows the existing style
- New features include appropriate documentation
- Environment variables are handled securely

## License

This project is provided as-is for educational and production use.

---

**Note**: This bot is designed for use in CI/CD pipelines or as a pre-merge check for teams practicing trunk-based development.
