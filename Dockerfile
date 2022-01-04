FROM alpine:3.15
# install python and pip3
RUN apk upgrade --no-cache \
  && apk add --no-cache \
    musl \
    build-base \
    python3 \
    python3-dev \
    py3-pip \
    curl \
  && pip3 install --no-cache-dir --upgrade pip \
  && rm -rf /var/cache/* \
  && rm -rf /root/.cache/*

# install atom gaiad
ENV GAIA_VERSION v6.0.0
RUN curl -LIo /usr/local/bin/gaiad \
  https://github.com/cosmos/gaia/releases/download/$GAIA_VERSION/gaiad-$GAIA_VERSION-linux-amd64 \
  && chmod +x /usr/local/bin/gaiad

# setup repository
WORKDIR /staketaxcsv

# install requirements
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt

# copy rest
COPY . .

# executable
ENTRYPOINT [ "/staketaxcsv/docker-entrypoint.sh" ]