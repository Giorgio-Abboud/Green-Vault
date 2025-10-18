package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
)

var (
	ErrDuplicateEmail     = errors.New("email already registered")
	ErrUnauthorized       = errors.New("unauthorized")
	ErrValidationFailed   = errors.New("validation failed")
	ErrInvalidCredentials = errors.New("invalid credentials")
)

// JSONResponse defines the unified structure for all API responses.
type JSONResponse struct {
	Ok          bool        `json:"ok"`
	Data        interface{} `json:"data,omitempty"`
	Error       string      `json:"error,omitempty"`
	RequestID   string      `json:"req_id,omitempty"`
	FieldErrors interface{} `json:"field_errors,omitempty"`
}

// Options is used to build JSONResponse easily (internal use only).
type Options struct {
	Data        interface{}
	Error       string
	RequestID   string
	FieldErrors interface{}
}

// WriteJSON sends a standardized success JSON response.
func WriteJSON(w http.ResponseWriter, status int, opts *Options) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	resp := JSONResponse{
		Ok:          true,
		Data:        opts.Data,
		RequestID:   opts.RequestID,
		FieldErrors: opts.FieldErrors,
	}

	_ = json.NewEncoder(w).Encode(resp)
}

// WriteError sends a standardized JSON error response.
func WriteError(w http.ResponseWriter, status int, opts *Options) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)

	resp := JSONResponse{
		Ok:          false,
		Error:       opts.Error,
		RequestID:   opts.RequestID,
		FieldErrors: opts.FieldErrors,
	}

	_ = json.NewEncoder(w).Encode(resp)
}
