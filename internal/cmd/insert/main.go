package main

import (
	"encoding/json"
	"log"
	"os"
	"time"

	"github.com/joho/godotenv"
	amqp "github.com/rabbitmq/amqp091-go"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"

	inserter "github.com/Giorgio-Abboud/Green-Vault/internal/package/insert"
	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

var DB *gorm.DB

// tryLoadLocalEnv loads .env.local (and .env) if they exist.
// godotenv.Load does NOT override variables that are already set,
// so Docker-provided env remains untouched.
func tryLoadLocalEnv() {
	// Prefer .env.local for local runs
	if _, err := os.Stat(".env.local"); err == nil {
		if err := godotenv.Load(".env.local"); err == nil {
			log.Println("ℹ️  Loaded environment from .env.local")
			return
		}
	}
	// Silent if neither exists; Docker/host env will be used.
}

func connectDatabase() {
	// Connect to Postgres
	dbURL := os.Getenv("DB_URL")
	if dbURL == "" {
		log.Fatal("DB_URL is not set in environment")
	}

	db, err := gorm.Open(postgres.Open(dbURL), &gorm.Config{
		DisableForeignKeyConstraintWhenMigrating: false,
	})
	if err != nil {
		log.Fatalf("failed to connect db: %v", err)
	}
	DB = db
}

func dbMigrate() {
	// Run migrations
	if err := DB.AutoMigrate(&models.User{}, &models.UserFill{}, &models.Metric{}); err != nil {
		log.Fatalf("failed to migrate tables: %v", err)
	}
}

func main() {
	// Load local env only if files exist; safe in Docker.
	tryLoadLocalEnv()

	// Connect to Postgres database
	connectDatabase()

	// Run migrations to database
	dbMigrate()

	log.Println("✅ Database connected and migrations applied!")

	// RabbitMQ consumer setup
	brokerURL := os.Getenv("BROKER_URL")
	if brokerURL == "" {
		brokerURL = "amqp://guest:guest@rabbitmq:5672/"
	}
	queue := os.Getenv("QUEUE_NAME")
	if queue == "" {
		queue = "calc.success"
	}

	conn, err := amqp.Dial(brokerURL)
	must(err)
	defer conn.Close()

	ch, err := conn.Channel()
	must(err)
	defer ch.Close()

	_, err = ch.QueueDeclare(queue, true, false, false, false, nil)
	must(err)

	must(ch.Qos(10, 0, false))

	msgs, err := ch.Consume(queue, "", false, false, false, false, nil)
	must(err)

	log.Println("Inserter consuming...")
	for msg := range msgs {
		var ins inserter.Inserter
		if err := json.Unmarshal(msg.Body, &ins); err != nil {
			log.Printf("bad json: %v", err)
			_ = msg.Nack(false, false)
			continue
		}

		// For now, only log
		ins.Insert()

		// Later: map Inserter → UserFill / Metric and persist with db.Create()

		time.Sleep(100 * time.Millisecond)
		_ = msg.Ack(false)
	}
}

func must(err error) {
	if err != nil {
		log.Fatal(err)
	}
}
