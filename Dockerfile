FROM python:latest
WORKDIR /hydrostatus
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
WORKDIR /hydrostatus/src/
CMD ["python3", "hydrostatusBot.py"]