package inserter

import "log"

type Inserter struct {
	SchemaVersion int    `json:"schema_version"`
	EventType     string `json:"event_type"`
	RequestID     string `json:"request_id"`
	Timestamp     string `json:"timestamp"`
	Price         string `json:"price"`
	Quantity      string `json:"quantity"`
	Side          string `json:"side"`
	Ok            bool   `json:"ok"`
	TS            string `json:"ts"`
}

func (ins *Inserter) Insert() {
	log.Printf("Saved: timestamp=%s price=%s quantity=%s side=%s ok=%v req=%s ts=%s",
		ins.Timestamp, ins.Price, ins.Quantity, ins.Side, ins.Ok, ins.RequestID, ins.TS)
}
