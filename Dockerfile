FROM python:3.11-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY . .

# Create runtime directories
RUN mkdir -p logs output

# Railway runs this as a cron job — the command is defined in railway.json
CMD ["python", "parser.py", "--mode", "db"]
