# -------- Build stage --------
FROM cgr.dev/chainguard/go:latest AS build
WORKDIR /src

COPY go.mod go.sum ./
RUN go mod download
COPY . .

# Build the API (HTTP server)
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o server-api ./cmd/api

# -------- Run stage --------
FROM cgr.dev/chainguard/static:latest
USER nonroot
WORKDIR /app

COPY --from=build /src/server-api /app/server-api

# Default to the API; compose can override if needed
CMD ["/app/server-api"]
