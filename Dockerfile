FROM python:3.10

RUN mkdir /code
RUN mkdir /output
RUN mkdir /spec
WORKDIR /code
COPY requirements.txt .
RUN python -m pip install -r requirements.txt
COPY . .
RUN python setup.py install

ENTRYPOINT [ "/usr/local/bin/asyncapi-codegen", "--output", "/output" ]
