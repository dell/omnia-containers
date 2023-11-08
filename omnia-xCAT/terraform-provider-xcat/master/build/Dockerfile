FROM golang:latest

MAINTAINER xcat.org


#:VOLUME ["/build"]
RUN mkdir  -p /src
RUN mkdir -p /build

ENTRYPOINT cd /src && make > /build/build.log 2>&1  && [ -f "$GOPATH/bin/terraform-provider-xcat" ] && \cp -fR $GOPATH/bin/terraform-provider-xcat /build

