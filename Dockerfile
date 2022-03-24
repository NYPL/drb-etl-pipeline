FROM python:3.8
ADD . /src
WORKDIR /src

RUN pip install -r requirements.txt

RUN pip install elasticsearch>8.0.0

EXPOSE 80

ENTRYPOINT [ "python",  "/src/main.py" ]
