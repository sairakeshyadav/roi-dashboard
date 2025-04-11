# Dockerfile
FROM python:3.10-slim

# Set environment vars
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy app code
COPY . .

# Expose the port Streamlit runs on
EXPOSE 8501

# Command to run Streamlit
CMD ["streamlit", "run", "roi_dashboard.py", "--server.port=8501", "--server.enableCORS=false"]
