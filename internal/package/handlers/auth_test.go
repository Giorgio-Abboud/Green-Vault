package handlers

import (
	"context"
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"
	"time"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"

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
			name: "invalid email",
			bodyJSON: map[string]any{
				"email":     "roary@fiu.@edu",
				"name":      "Roary",
				"last_name": "The Panther",
				"password":  "Roary!panther25",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "invalid password (short)",
			bodyJSON: map[string]any{
				"email":     "roary@fiu.edu",
				"name":      "Roary",
				"last_name": "The Panther",
				"password":  "short",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "invalid password (no uppercase)",
			bodyJSON: map[string]any{
				"email":     "roary@fiu.edu",
				"name":      "Roary",
				"last_name": "The Panther",
				"password":  "lowercasenoupper!10",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "invalid password (no lowercase)",
			bodyJSON: map[string]any{
				"email":     "roary@fiu.edu",
				"name":      "Roary",
				"last_name": "The Panther",
				"password":  "UPPERCASEPASSWORD!10",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "invalid password (no digits)",
			bodyJSON: map[string]any{
				"email":     "roary@fiu.edu",
				"name":      "Roary",
				"last_name": "The Panther",
				"password":  "UPPERCASEPASSWORD!digits?",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "invalid password (no symbols)",
			bodyJSON: map[string]any{
				"email":     "roary@fiu.edu",
				"name":      "Roary",
				"last_name": "The Panther",
				"password":  "WhereAreMySymbols2025",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "invalid name",
			bodyJSON: map[string]any{
				"email":     "roary@fiu.edu",
				"name":      "Roary]",
				"last_name": "The Panther",
				"password":  "Roary!panther25",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "invalid last name",
			bodyJSON: map[string]any{
				"email":     "roary@fiu.@edu",
				"name":      "Roary",
				"last_name": "The Panther!",
				"password":  "Roary!panther25",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "valid request",
			bodyJSON: map[string]any{
				"email":     "roary@fiu.edu",
				"name":      "Roary",
				"last_name": "The Panther",
				"password":  "Roary!panther25",
			},
			wantStatus: http.StatusCreated,
			wantOK:     true,
		},
		{
			name: "bad json",
			bodyJSON: map[string]any{
				"email": 123,
			},
			wantStatus: http.StatusBadRequest,
			wantOK:     false,
		},
		{
			name: "duplicate email",
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
		"email":     "roary@fiu.edu",
		"name":      "Roary",
		"last_name": "The Panther",
		"password":  "Roary!panther25",
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
				"password": "wrongExample25!",
			},
			wantStatus: http.StatusUnauthorized,
			wantOK:     false,
		},
		{
			name: "wrong password",
			bodyJSON: map[string]any{
				"email":    "roary@fiu.edu",
				"password": "This is not the password!25",
			},
			wantStatus: http.StatusUnauthorized,
			wantOK:     false,
		},
		{
			name: "ok",
			bodyJSON: map[string]any{
				"email":    "roary@fiu.edu",
				"password": "Roary!panther25",
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

func TestEditProfile(t *testing.T) {
	app := newTestApp(t)

	// seed an existing user with hashed password
	hashed, _ := bcrypt.GenerateFromPassword([]byte("12340987User!"), bcrypt.DefaultCost)
	u, err := app.Store.CreateUser(context.Background(), &models.User{
		ID:           uuid.New(),
		Email:        "existent@example.com",
		Name:         "Seed",
		LastName:     "User",
		PasswordHash: string(hashed),
	})
	if err != nil {
		t.Fatalf("seed user: %v", err)
	}

	for _, tc := range []struct {
		name       string
		bodyJSON   map[string]any
		wantStatus int
		wantOK     bool
	}{
		{
			name: "empty old password",
			bodyJSON: map[string]any{
				"old_password":     "",
				"new_password":     "StrongPassword!25",
				"confirm_password": "StrongPassword!25",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "empty new password",
			bodyJSON: map[string]any{
				"old_password":     "12340987User!",
				"new_password":     "",
				"confirm_password": "StrongPassword!25",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "empty confirm password",
			bodyJSON: map[string]any{
				"old_password":     "12340987User!",
				"new_password":     "StrongPassword!25",
				"confirm_password": "",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "no met requirements",
			bodyJSON: map[string]any{
				"old_password":     "12340987User!",
				"new_password":     "StrongPassword",
				"confirm_password": "StrongPassword",
			},
			wantStatus: http.StatusUnprocessableEntity,
			wantOK:     false,
		},
		{
			name: "valid update",
			bodyJSON: map[string]any{
				"old_password":     "12340987User!",
				"new_password":     "StrongPassword!25",
				"confirm_password": "StrongPassword!25",
			},
			wantStatus: http.StatusOK,
			wantOK:     true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest("PUT", "/v1/users/me", mustJSONBody(t, tc.bodyJSON))
			req = withUser(req, u.ID)
			req.Header.Set("Content-Type", "application/json")

			rr := httptest.NewRecorder()
			EditProfile(app).ServeHTTP(rr, req)

			if rr.Code != tc.wantStatus {
				t.Fatalf("status = %d; want %d. body=%s", rr.Code, tc.wantStatus, rr.Body.String())
			}
			res := decodeStdResp(t, rr)
			if res.Ok != tc.wantOK {
				t.Fatalf("ok = %v; want %v. body=%s", res.Ok, tc.wantOK, rr.Body.String())
			}

			// check updated password for valid case
			if tc.name == "valid update" {
				updated, err := app.Store.GetUserByID(context.Background(), u.ID)
				if err != nil {
					t.Fatalf("failed to fetch updated user: %v", err)
				}
				if bcrypt.CompareHashAndPassword([]byte(updated.PasswordHash), []byte("StrongPassword!25")) != nil {
					t.Fatalf("password hash was not updated")
				}
			}
		})
	}
}

func TestDeleteUser(t *testing.T) {
	app := newTestApp(t)

	hashed, _ := bcrypt.GenerateFromPassword([]byte("DeleteMe123!"), bcrypt.DefaultCost)
	u, err := app.Store.CreateUser(context.Background(), &models.User{
		ID:           uuid.New(),
		Email:        "deleteme@example.com",
		Name:         "Delete",
		LastName:     "User",
		PasswordHash: string(hashed),
	})
	if err != nil {
		t.Fatalf("seed user: %v", err)
	}

	tests := []struct {
		name       string
		authUserID uuid.UUID
		wantStatus int
		wantOK     bool
	}{
		{
			name:       "unauthorized (no user)",
			authUserID: uuid.Nil,
			wantStatus: http.StatusUnauthorized,
			wantOK:     false,
		},
		{
			name:       "valid delete",
			authUserID: u.ID,
			wantStatus: http.StatusNoContent,
			wantOK:     true,
		},
	}

	for _, tc := range tests {
		t.Run(tc.name, func(t *testing.T) {
			req := httptest.NewRequest("DELETE", "/v1/users/me", nil)
			if tc.authUserID != uuid.Nil {
				req = withUser(req, tc.authUserID)
			}

			rr := httptest.NewRecorder()
			DeleteUser(app).ServeHTTP(rr, req)

			if rr.Code != tc.wantStatus {
				t.Fatalf("status = %d; want %d. body=%s", rr.Code, tc.wantStatus, rr.Body.String())
			}

			res := decodeStdResp(t, rr)
			if res.Ok != tc.wantOK {
				t.Fatalf("ok = %v; want %v. body=%s", res.Ok, tc.wantOK, rr.Body.String())
			}

			if tc.name == "valid delete" {
				// 🧩 Verify user actually deleted from DB
				_, err := app.Store.GetUserByID(context.Background(), u.ID)
				if err == nil {
					t.Fatalf("expected user to be deleted, but found one")
				}
			}
		})
	}
}

func TestListUserFillsAndMetrics(t *testing.T) {
	app := newTestApp(t)

	// --- Seed data shared across tests ---
	// user with no fills
	userNoFills, _ := app.Store.CreateUser(context.Background(), &models.User{
		ID:           uuid.New(),
		Email:        "nofills@example.com",
		Name:         "No",
		LastName:     "Fills",
		PasswordHash: "hashed",
	})

	// user with one fill + metric
	userOneFill, _ := app.Store.CreateUser(context.Background(), &models.User{
		ID:           uuid.New(),
		Email:        "onefill@example.com",
		Name:         "One",
		LastName:     "Fill",
		PasswordHash: "hashed",
	})

	fillID := uuid.New()
	app.Store.CreateUserFill(context.Background(), &models.UserFill{
		ID:        fillID,
		UserID:    userOneFill.ID,
		Symbol:    "AAPL",
		Timestamp: time.Now().UTC(),
		Price:     180.5,
		Side:      "buy",
		Quantity:  10,
		Mode:      "Analyze",
		Result:    "SUCCESS",
	})

	app.Store.CreateMetric(context.Background(), &models.Metric{
		ID:              uuid.New(),
		UserFillID:      fillID,
		VwapSlippage:    0.1,
		Shortfall:       0.02,
		EffectiveSpread: 0.01,
		RealizedSpread:  0.005,
		MarketImpact:    0.03,
		Drift:           0.01,
	})

	for _, tc := range []struct {
		name       string
		userID     uuid.UUID
		wantStatus int
		wantOK     bool
		wantFills  int
	}{
		{
			name:       "unauthorized",
			userID:     uuid.Nil,
			wantStatus: http.StatusUnauthorized,
			wantOK:     false,
			wantFills:  0,
		},
		{
			name:       "valid - user with no fills",
			userID:     userNoFills.ID,
			wantStatus: http.StatusOK,
			wantOK:     true,
			wantFills:  0,
		},
		{
			name:       "valid - user with one fill and metric",
			userID:     userOneFill.ID,
			wantStatus: http.StatusOK,
			wantOK:     true,
			wantFills:  1,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {

			req := httptest.NewRequest("GET", "/v1/users/data", nil)
			if tc.userID != uuid.Nil {
				req = withUser(req, tc.userID)
			}

			rr := httptest.NewRecorder()
			ListUserFillsAndMetrics(app).ServeHTTP(rr, req)

			// status code check
			if rr.Code != tc.wantStatus {
				t.Fatalf("status = %d; want %d. body=%s",
					rr.Code, tc.wantStatus, rr.Body.String())
			}

			// decode standard JSON response
			res := decodeStdResp(t, rr)

			if res.Ok != tc.wantOK {
				t.Fatalf("ok = %v; want %v. body=%s",
					res.Ok, tc.wantOK, rr.Body.String())
			}

			// if unauthorized case, nothing else to check
			if tc.userID == uuid.Nil {
				return
			}

			// Extract fills array
			fillsAny, ok := res.Data["fills"]
			if !ok {
				t.Fatalf("expected 'fills' field. body=%s", rr.Body.String())
			}

			var fillsSlice []interface{}
			if fillsAny != nil {
				var ok bool
				fillsSlice, ok = fillsAny.([]interface{})
				if !ok {
					t.Fatalf("fills is %T; want []interface{}. body=%s",
						fillsAny, rr.Body.String())
				}
			}

			if len(fillsSlice) != tc.wantFills {
				t.Fatalf("fills count = %d; want %d. body=%s",
					len(fillsSlice), tc.wantFills, rr.Body.String())
			}

			// if expecting metric, verify its presence
			if tc.wantFills == 1 {
				firstFill, ok := fillsSlice[0].(map[string]any)
				if !ok {
					t.Fatalf("first fill is %T; want map[string]any",
						fillsSlice[0])
				}

				metricAny, ok := firstFill["Metric"]
				if !ok {
					metricAny, ok = firstFill["metric"]
				}
				if !ok || metricAny == nil {
					t.Fatalf("expected metric on fill but none found. body=%s",
						rr.Body.String())
				}
			}
		})
	}
}
