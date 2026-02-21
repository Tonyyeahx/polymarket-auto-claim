FROM python:3.12-slim

WORKDIR /app

# Create non-root user
RUN useradd --create-home appuser

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY config.py redemption.py main.py ./

# Switch to non-root user
USER appuser

CMD ["python", "main.py"]
