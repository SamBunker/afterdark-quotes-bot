FROM python:3.10-slim

WORKDIR ./

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the bot code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the bot
CMD ["python", "main.py"]
#CMD ["/bin/sh", "/startup.sh"]