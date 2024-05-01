# Use the official Python image as the base image
FROM python:3.9

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the working directory
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Django project files to the working directory
COPY . .

# Set environment variables for database configuration
ARG DB_NAME
ARG DB_HOST
ARG DB_USER
ARG DB_PASSWORD

ENV DB_NAME=$DB_NAME
ENV DB_HOST=$DB_HOST
ENV DB_USER=$DB_USER
ENV DB_PASSWORD=$DB_PASSWORD

# Set the entrypoint script
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Run the entrypoint script before running the server
CMD ["/app/entrypoint.sh"]

# Expose the port that Django runs on
EXPOSE 8000
