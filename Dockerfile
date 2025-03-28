# Gunakan Python sebagai base image
FROM python:3.9

# Set working directory
WORKDIR /app

# Copy semua file ke dalam container
COPY . .

# Install dependensi
RUN pip install --no-cache-dir -r requirements.txt

# Jalankan aplikasi dengan Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
