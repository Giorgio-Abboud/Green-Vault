package handlers

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/google/uuid"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

func TestSignup(t *testing.T) {
	app := newTestApp(t)

	// seed a duplicate email directly through the Store
	_, err := app.Store.CreateUser(context.Background(), &models.User{
		ID:           uuid.New(),
		Email:        "dupe@example.com",
		Name:         "Seed",
		LastName:     "User",
		PasswordHash: "seed-hash",
	})
	if err != nil {
		t.Fatalf("seed dupe: %v", err)
	}

	for _, tc := range []struct {
		name       string
		bodyJSON   map[string]any
		wantStatus int
		wantOK     bool
	}{
		{
			name: "valid_request",
			bodyJSON: map[string]any{
				"email":     "User@EXAMPLE.com",
				"name":      "Roary",
				"last_name": "Panther",
				"password":  "fiu",
			},
			wantStatus: http.StatusCreated,
			wantOK:     true,
		},
		{
			name: "bad_json",
			bodyJSON: map[string]any{
				"email": 123,
			},
			wantStatus: http.StatusBadRequest,
			wantOK:     false,
		},
		{
			name: "duplicate_email",
			bodyJSON: map[string]any{
				"email":     "dupe@example.com",
				"name":      "A",
				"last_name": "B",
				"password":  "pw",
			},
			wantStatus: http.StatusConflict,
			wantOK:     false,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest("POST", "/v1/users", mustJSONBody(t, tc.bodyJSON))
			req.Header.Set("Content-Type", "application/json")

			rr := httptest.NewRecorder()
			Signup(app).ServeHTTP(rr, req)

			if rr.Code != tc.wantStatus {
				t.Fatalf("status = %d; want %d. body=%s", rr.Code, tc.wantStatus, rr.Body.String())
			}
			res := decodeStdResp(t, rr)
			if res.Ok != tc.wantOK {
				t.Fatalf("ok = %v; want %v. body=%s", res.Ok, tc.wantOK, rr.Body.String())
			}
		})
	}
}

func TestLogin(t *testing.T) {
	app := newTestApp(t)

	// Seed a user via Signup to produce a real bcrypt hash
	seed := map[string]any{
		"email":     "ok@example.com",
		"name":      "Ok",
		"last_name": "User",
		"password":  "secret123",
	}
	{
		req := httptest.NewRequest("POST", "/v1/users", mustJSONBody(t, seed))
		req.Header.Set("Content-Type", "application/json")
		rr := httptest.NewRecorder()
		Signup(app).ServeHTTP(rr, req)
		if rr.Code != http.StatusCreated {
			t.Fatalf("seed signup failed: %d %s", rr.Code, rr.Body.String())
		}
	}

	for _, tc := range []struct {
		name       string
		bodyJSON   map[string]any
		wantStatus int
		wantOK     bool
	}{
		{
			name: "wrong email",
			bodyJSON: map[string]any{
				"email":    "wrong@example.com",
				"password": "secret123",
			},
			wantStatus: http.StatusUnauthorized,
			wantOK:     false,
		},
		{
			name: "wrong password",
			bodyJSON: map[string]any{
				"email":    "ok@example.com",
				"password": "badpw",
			},
			wantStatus: http.StatusUnauthorized,
			wantOK:     false,
		},
		{
			name: "ok",
			bodyJSON: map[string]any{
				"email":    "ok@example.com",
				"password": "secret123",
			},
			wantStatus: http.StatusOK,
			wantOK:     true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest("POST", "/v1/login", mustJSONBody(t, tc.bodyJSON))
			req.Header.Set("Content-Type", "application/json")
			rr := httptest.NewRecorder()

			Login(app).ServeHTTP(rr, req)

			if rr.Code != tc.wantStatus {
				t.Fatalf("status = %d; want %d. body=%s", rr.Code, tc.wantStatus, rr.Body.String())
			}
			res := decodeStdResp(t, rr)
			if res.Ok != tc.wantOK {
				t.Fatalf("ok = %v; want %v. body=%s", res.Ok, tc.wantOK, rr.Body.String())
			}
		})
	}
}

func TestMe(t *testing.T) {
	app := newTestApp(t)
	req := httptest.NewRequest("GET", "/v1/me", nil)
	rr := httptest.NewRecorder()

	Me(app).ServeHTTP(rr, req)

	if rr.Code != http.StatusUnauthorized {
		t.Fatalf("status = %d; want %d", rr.Code, http.StatusUnauthorized)
	}
	res := decodeStdResp(t, rr)
	if res.Ok {
		t.Fatal("expected ok=false for unauthorized")
	}
	if !strings.Contains(res.Error, "unauthorized") {
		t.Fatalf("expected 'unauthorized' error, got: %s", res.Error)
	}
}
