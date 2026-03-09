# Updated Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install PDM globally (cached layer)
RUN pip install --no-cache-dir pdm

# Copy project metadata for dependency resolution (cached)
COPY pyproject.toml pdm.lock* /app/

# Install dependencies during build for better caching (non-editable for prod-like, but dev allows override via volumes)
RUN pdm install --no-editable --no-self

# Copy all code (including apps, config, etc.)
COPY . /app

ENV PYTHONUNBUFFERED=1

# Default command (overridable in docker-compose; no migrate here to avoid running on build)
CMD ["pdm", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]