FROM python:3.10-alpine
WORKDIR /monbot

RUN apk update && apk upgrade
RUN apk add postgresql-dev gcc python3-dev musl-dev

RUN pip install python-telegram-bot==13.7
RUN pip install paramiko
RUN pip install python-dotenv
RUN pip install psycopg2-binary

COPY bot.py .

CMD ["python", "bot.py"]
