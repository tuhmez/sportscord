FROM python:3.8.8-slim

COPY . .
RUN pip install -U -r requirements.txt

ENV TZ=America/Chicago

CMD [ "python", "-u", "main.py" ]
