FROM python:3.9
ADD . /src
WORKDIR /src

RUN pip install --upgrade pip

RUN pip install -r requirements.txt

RUN pip install elasticsearch>8.0.0

EXPOSE 80

ENTRYPOINT [ "python",  "/src/main.py" ]
