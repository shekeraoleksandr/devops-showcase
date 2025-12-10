FROM --platform=linux/amd64 mcr.microsoft.com/dotnet/sdk:10.0.100-noble AS builder
WORKDIR /app
COPY cartservice.csproj .
RUN dotnet restore cartservice.csproj
COPY . .
RUN dotnet publish cartservice.csproj \
    -p:PublishSingleFile=true \
    --self-contained true \
    -p:PublishTrimmed=true \
    -p:TrimMode=full \
    -c release \
    -o /cartservice

FROM --platform=linux/amd64 mcr.microsoft.com/dotnet/runtime-deps:10.0.0-noble-chiseled

WORKDIR /app
COPY --from=builder /cartservice .
EXPOSE 7070
ENV DOTNET_EnableDiagnostics=0 \
    ASPNETCORE_HTTP_PORTS=7070
USER 1000
ENTRYPOINT ["/app/cartservice"]