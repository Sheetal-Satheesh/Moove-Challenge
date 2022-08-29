FROM python:3.9-alpine
RUN pip install --upgrade pip
COPY ./requirements.txt /src/requirements.txt
WORKDIR /src
RUN pip install -r requirements.txt
COPY ./src /src
WORKDIR /src
RUN python db_init.py
RUN python load_data.py

ENTRYPOINT [ "python" ]
CMD ["api.py"]
