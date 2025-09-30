# Use the official slim Python image as a base
FROM python:3.9-slim

RUN apt-get update && apt-get install -y \
    wget \
    xfonts-base \
    xfonts-75dpi && \
    wget https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-1/wkhtmltox_0.12.6-1.focal_amd64.deb && \
    dpkg -i wkhtmltox_0.12.6-1.focal_amd64.deb || apt-get install -f -y && \
    rm wkhtmltox_0.12.6-1.focal_amd64.deb && \
    rm -rf /var/lib/apt/lists/*

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . ./

# Expose the port the Flask app runs on
EXPOSE 5000


# Use Gunicorn for production. Alternatively, you can use `python app.py`.
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
