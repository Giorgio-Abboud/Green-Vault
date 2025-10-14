package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
)

var ErrUnauthorized = errors.New("unauthorized")

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

// WriteValidationError sends a structured 422 response with per-field errors.
func WriteValidationError(w http.ResponseWriter, reqID string, fieldErrs map[string]string) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(http.StatusUnprocessableEntity)

	resp := map[string]any{
		"ok":           false,
		"req_id":       reqID,
		"error":        "validation failed",
		"field_errors": fieldErrs,
	}
	_ = json.NewEncoder(w).Encode(resp)
}
