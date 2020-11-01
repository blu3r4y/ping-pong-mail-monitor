FROM python:3.9

WORKDIR /usr/src/app

VOLUME ["/usr/src/data"]

EXPOSE 80

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ .
RUN chmod 755 /usr/src/app/start.sh

CMD [ "/bin/sh", "/usr/src/app/start.sh" ]
