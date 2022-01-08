
FROM python:3.9.9-slim

ENV APPHOME=/staketaxcsv

RUN apt-get update
RUN apt-get install -y curl bzip2
RUN mkdir -p ${APPHOME}

# install pip
WORKDIR $APPHOME
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

# copy rest
COPY . .

CMD [ "bash" ]
