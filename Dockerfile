FROM python:3.10

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY ./blockchain /code/blockchain
COPY ./model /code/model

CMD ["uvicorn", "blockchain.main:blockchain", "--host", "0.0.0.0", "--port", "8000"]
