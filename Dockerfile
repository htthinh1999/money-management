# Use the official Python image as base image
FROM python:3.12-slim

# Set environment variables
ENV APP_HOME /app
ENV PORT 8080

# Create and set the working directory
WORKDIR $APP_HOME

# Copy the Python dependencies file to the working directory
COPY ./requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy the Flask app files to the working directory
COPY . .

# Expose the port the app runs on
EXPOSE $PORT

# Command to run the Flask application
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app
