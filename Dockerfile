FROM python:3.11
ENV PYTHONUNBUFFERED 1
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
RUN python manage.py collectstatic --noinput || true
CMD sh -c "python manage.py makemigrations && python manage.py migrate && gunicorn chigo.wsgi:application --bind 0.0.0.0:10000"