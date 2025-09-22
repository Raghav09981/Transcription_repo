# Use official Python image
FROM python:3.10

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN python -m pip install --upgrade pip
RUN pip install --default-timeout=100 -i https://pypi.org/simple -r requirements.txt

# Copy the secret into the container
COPY client_secret_1019005830189-pmjdbmhte1ueqp7j07rqhq2qfn2jkpr5.apps.googleusercontent.com.json

# Copy the rest of the project
COPY . .

# Expose the port FastAPI runs on
EXPOSE 80

# Run the FastAPI app
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80", "--reload"]
