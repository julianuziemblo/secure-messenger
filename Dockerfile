FROM python:3.10.16-slim

WORKDIR /app

COPY *.py requirements.txt ./

RUN pip install -r requirements.txt

EXPOSE 2137:2137

ENTRYPOINT [ "python", "./app.py" ] 
