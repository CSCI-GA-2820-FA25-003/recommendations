# Image for a NYU Lab development environment
FROM rofrano/nyu-devops-base:su25

# Set up the Python development environment
WORKDIR /app
COPY Pipfile Pipfile.lock ./
RUN sudo python -m pip install --upgrade pip pipenv && \
    sudo pipenv install --system --dev

# Install user mode tools
COPY .devcontainer/scripts/install-tools.sh /tmp/
RUN cd /tmp && bash ./install-tools.sh

# ---------- ADD THESE LINES BELOW ----------
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
