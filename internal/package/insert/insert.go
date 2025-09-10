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
	Request       string `json:"request"`
	Successful    bool   `json:"successful"`
	Ok            bool   `json:"ok"`
	TS            string `json:"ts"`
}

func (ins *Inserter) Insert() {
	log.Printf(
		"Saved: ts=%s price=%s qty=%s side=%s request=%s successful=%v ok=%v req_id=%s at=%s",
		ins.Timestamp, ins.Price, ins.Quantity, ins.Side,
		ins.Request, ins.Successful, ins.Ok, ins.RequestID, ins.TS,
	)
}
