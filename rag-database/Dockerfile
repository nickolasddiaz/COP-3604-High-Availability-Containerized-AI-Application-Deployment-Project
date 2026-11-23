FROM python:3.14
ADD ingest.py .
COPY requirements.txt .
RUN pip install -r requirements.txt
EXPOSE 5432
CMD ["python", "./ingest.py"]