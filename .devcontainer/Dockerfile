# Image for a NYU Lab development environment
FROM docker.io/rofrano/nyu-devops-base:su25

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN python -m pip install --upgrade pip pipenv && \
    pipenv install --system --dev

# ---------- ADD THESE LINES BELOW ----------
# Note: install-tools.sh is skipped for production builds (requires sudo which isn't allowed in OpenShift)
# Copy the entire application source code into the image
COPY . /app

# Set environment variables for Flask
ENV FLASK_APP=wsgi.py
ENV FLASK_ENV=production
ENV PORT=8080

# Expose Flask's port
EXPOSE 8080

# Default command: run Flask via Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "wsgi:app"]
# ---------- END NEW LINES ----------
