FROM python:3.14
ADD app.py .
COPY requirements.txt .
RUN pip install -r requirements.txt  
EXPOSE 8000
CMD ["gunicorn", "app:app"]