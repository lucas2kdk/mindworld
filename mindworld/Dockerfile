# Use the official Python base image
FROM python:3.12

# Set the working directory in the container
WORKDIR /app

# Copy the requirements file to the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code to the container
COPY . .

# Expose the port that Daphne will listen on
EXPOSE 8000

# Run the Daphne server with manage.py as the entrypoint
CMD ["daphne", "mindworld.asgi:application"]