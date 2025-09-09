# -------- Build stage --------
FROM cgr.dev/chainguard/go:latest AS build

WORKDIR /src

# Copy mod files and download deps
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the source
COPY . .

# Build the binary from cmd/insert
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -o server ./cmd/insert

# -------- Run stage --------
FROM cgr.dev/chainguard/static:latest

USER nonroot
WORKDIR /app

COPY --from=build /src/server /app/server

CMD ["/app/server"]
