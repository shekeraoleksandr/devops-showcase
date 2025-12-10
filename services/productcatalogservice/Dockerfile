FROM --platform=$BUILDPLATFORM golang:1.25.1-alpine AS builder
ARG TARGETOS
ARG TARGETARCH
WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download
COPY . .

RUN GOOS=${TARGETOS} GOARCH=${TARGETARCH} CGO_ENABLED=0 go build -ldflags="-s -w" -o /productcatalogservice .

FROM gcr.io/distroless/static
WORKDIR /src
COPY --from=builder /productcatalogservice /src/server
COPY products.json .

ENV GOTRACEBACK=single

EXPOSE 3550
ENTRYPOINT ["/src/server"]