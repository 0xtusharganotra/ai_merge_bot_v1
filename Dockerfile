FROM python:3.9-slim

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt agent.py ./

RUN pip install --no-cache-dir -r requirements.txt

# GEMINI_API_KEY environment variable is required at runtime
# Pass it using: docker run -e GEMINI_API_KEY=your_key_here ...
ENV GEMINI_API_KEY=""

ENTRYPOINT ["python", "/app/agent.py"]
