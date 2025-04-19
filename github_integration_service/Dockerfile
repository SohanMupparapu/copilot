# Use the official slim Python image as a base
FROM python:3.9-slim

# Install wkhtmltopdf and its dependencies
RUN apt-get update && apt-get install -y \
    wkhtmltopdf \
    --no-install-recommends && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . ./

# Expose the port the Flask app runs on
EXPOSE 5050


# Use Gunicorn for production. Alternatively, you can use `python app.py`.
CMD ["gunicorn", "--bind", "0.0.0.0:5050", "app:app"]