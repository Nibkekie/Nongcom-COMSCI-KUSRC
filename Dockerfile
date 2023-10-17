FROM python:3.11.5
COPY . .
RUN pip install -r requirements.txt
CMD ["python","wsgi.py"]