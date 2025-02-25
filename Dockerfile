FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt
RUN apt-get update && apt-get install -y sqlite3

COPY ./blockchain /code/blockchain
COPY ./model /code/model

CMD ["uvicorn", "blockchain.main:blockchain", "--host", "0.0.0.0", "--port", "8000"]
