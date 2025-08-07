# Use an official Python runtime as the base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the application code and inventory file
COPY inventory.py .
COPY inventory.txt .

# Command to run the application interactively
CMD ["python", "inventory.py"]