package main

import (
	"encoding/json"
	"log"
	"os"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"

	inserter "github.com/Giorgio-Abboud/Green-Vault/internal/package/insert"
)

func env(k, d string) string {
	if v := os.Getenv(k); v != "" {
		return v
	}
	return d
}

func main() {
	brokerURL := env("BROKER_URL", "amqp://guest:guest@rabbitmq:5672/")
	queue := env("QUEUE_NAME", "calc.success")

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

		ins.Insert()

		time.Sleep(100 * time.Millisecond)
		_ = msg.Ack(false)
	}
}

func must(err error) {
	if err != nil {
		log.Fatal(err)
	}
}
