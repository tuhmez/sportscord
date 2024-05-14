FROM python:3.12.3-slim

COPY . .
RUN pip install -U -r requirements.txt

ENV TZ=America/Chicago

CMD [ "python", "-u", "main.py" ]
