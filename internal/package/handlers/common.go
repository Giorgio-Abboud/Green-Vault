package handlers

import (
	"encoding/json"
	"net/http"
)

// JSONResponse defines the unified structure for all API responses.
type JSONResponse struct {
	Ok    bool        `json:"ok"`
	Data  interface{} `json:"data,omitempty"`
	Error string      `json:"error,omitempty"`
}

// WriteJSON sends a JSON response with a status code and payload.
func WriteJSON(w http.ResponseWriter, status int, data any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	resp := JSONResponse{Ok: true, Data: data}
	_ = json.NewEncoder(w).Encode(resp)
}

// WriteError sends a standardized JSON error response.
func WriteError(w http.ResponseWriter, status int, err error) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	resp := JSONResponse{Ok: false, Error: err.Error()}
	_ = json.NewEncoder(w).Encode(resp)
}
