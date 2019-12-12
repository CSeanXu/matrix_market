FROM python:3.7

ENV PYTHONUNBUFFERED 1

RUN pip install pipenv

RUN mkdir /code
WORKDIR /code
COPY . /code/

RUN pipenv lock --requirements > requirements.txt
RUN pip install -r requirements.txt

RUN make undebug

ENTRYPOINT ["uwsgi", "--ini", "/code/uwsgi.ini"]
