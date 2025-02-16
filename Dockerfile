FROM python:3.8 AS builder
COPY requirements.txt .



RUN pip install --user -r requirements.txt



WORKDIR /code


COPY --from=builder /root/.local  /root/.local
COPY ./src .


ENV PAV=/root/.local:$PATH


CMD ["python", "u", "./bot.py"] 
