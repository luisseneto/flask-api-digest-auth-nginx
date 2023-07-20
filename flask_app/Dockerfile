FROM python:3.6.7

WORKDIR usr/src/servidor/flask_app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["gunicorn", "-w", "1", "-b", "0.0.0.0:8000", "wsgi:server"]