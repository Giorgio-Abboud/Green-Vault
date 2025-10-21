# Single-stage build & run (no cross-stage venv copy)
FROM cgr.dev/chainguard/python:latest-dev

WORKDIR /app

# Install deps into a local venv
COPY requirements.txt .
RUN python -m venv /app/.venv \
 && /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# Add venv to PATH for both build & runtime
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy app code
COPY . .

EXPOSE 8000
ENTRYPOINT ["uvicorn"]
CMD ["cmd.main:app","--host","0.0.0.0","--port","8000"]
