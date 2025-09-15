FROM python:3.11-slim

# Install build deps and ODBC driver prerequisites (Debian-based)
RUN apt-get update && apt-get install -y \
    curl gnupg apt-transport-https unixodbc unixodbc-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# Optional: Install Microsoft ODBC Driver 18 for SQL Server (see MS docs)
# RUN curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
#   && curl https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
#   && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18 \
#   && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY app ./app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

ENV APP_HOST=0.0.0.0 APP_PORT=8000
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
