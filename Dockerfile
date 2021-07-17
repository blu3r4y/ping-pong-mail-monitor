FROM python:3.9

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .

VOLUME ["/usr/src/data"]

EXPOSE 80

CMD [ "python", "start.py" ]
