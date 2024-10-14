FROM python:3.10-alpine
WORKDIR /monbot

RUN apk update && apk upgrade
RUN apk add postgresql-dev gcc python3-dev musl-dev

COPY requirements.txt .
COPY bot.py .

RUN pip install -r requirements.txt

CMD ["python", "bot.py"]
