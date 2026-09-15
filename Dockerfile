FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip check
COPY expertcook ./expertcook
COPY static ./static
COPY server.py proportions.json gunicorn.conf.py ./
CMD ["gunicorn", "--config", "gunicorn.conf.py", "server:app"]
