FROM python:3.10.16-slim

WORKDIR /app

COPY *.py requirements.txt ./

RUN python -m venv .venv && . .venv/bin/activate
RUN pip install -r requirements.txt

ENTRYPOINT [ "python", "./app.py" ] 
