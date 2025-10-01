# Green-Vault
Capstone II Project

## Requirements
* Install Docker
* Install Docker Compose plugin

## Environment files and Postgres Configuration
* create ```.env.docker``` in ```internal``` folder and set it up with
```
# Connect from container to your host's Postgres
DB_URL=postgres://username:password@host.docker.internal:5432/dbname?sslmode=disable

# RabbitMQ (service name = rabbitmq in docker-compose)
BROKER_URL=amqp://guest:guest@rabbitmq:5672/
QUEUE_NAME=calc.success
```
* You must have a Postgres account (set your username and password) and create a database (dbname)
* You might have to reconfigure your postgres installation files to allow connectivity with Docker.
* Set this in ```postgresql.conf```
```
listen_addresses = '*'
```
* Set this in ```pg_hba.conf```
```
host all all {subnet_docker_network} md5
```
* Restart Postgres

## Run
* Build images
```
docker compose build ui analyzer internal
```
* Run services
```
docker compose up
```