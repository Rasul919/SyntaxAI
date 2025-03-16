FROM python:3.8 AS builder 
 
COPY requirements.txt . 
 
RUN pip install --user -r requirements.txt 
 
FROM python:3.8 
 
WORKDIR /code 
 
COPY --from=builder /root/.local /root/.local 
 
COPY ./src . 
 
ENV PATH=/root/.local/bin:$PATH 
 
CMD ["python", "-u", "./bot.py"]
