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

func TestFilterMetricsBySymbol(t *testing.T) {
    app := newTestApp(t)

    // seed user
    u, err := app.Store.CreateUser(context.Background(), &models.User{
        ID:           uuid.New(),
        Email:        "metricseed@example.com",
        Name:         "Seed",
        LastName:     "User",
        PasswordHash: "hashed",
    })
    if err != nil {
        t.Fatalf("seed user: %v", err)
    }

    // seed fills + metrics
    fill := models.UserFill{
        ID:        uuid.New(),
        UserID:    u.ID,
        Symbol:    "TSLA",
        Timestamp: time.Now().UTC(), // <-- fixed: time.Now not Time.Now
        Price:     100.0,
        Side:      "buy",
        Quantity:  10,
        Mode:      "Estimate",
        Result:    "SUCCESS",
    }
    if _, err := app.Store.CreateUserFill(context.Background(), &fill); err != nil {
        t.Fatalf("seed fill: %v", err)
    }

    metric := models.Metric{
        ID:              uuid.New(),
        UserFillID:      fill.ID,
        VwapSlippage:    0.1,
        Shortfall:       0.01,
        EffectiveSpread: 0.02,
        RealizedSpread:  0.03,
        MarketImpact:    0.04,
        Drift:           0.05,
    }
    if _, err := app.Store.CreateMetric(context.Background(), &metric); err != nil {
        t.Fatalf("seed metric: %v", err)
    }

    tests := []struct {
        name       string
        bodyJSON   map[string]any
        userID     uuid.UUID
        wantStatus int
        wantOK     bool
    }{
        {
            name: "missing symbol",
            bodyJSON: map[string]any{
                "symbol": "",
            },
            userID:     u.ID,
            wantStatus: http.StatusUnprocessableEntity,
            wantOK:     false,
        },
        {
            name: "symbol too long",
            bodyJSON: map[string]any{
                "symbol": "ABCDEFGHIJK",
            },
            userID:     u.ID,
            wantStatus: http.StatusUnprocessableEntity,
            wantOK:     false,
        },
        {
            name: "unauthorized",
            bodyJSON: map[string]any{
                "symbol": "TSLA",
            },
            userID:     uuid.Nil,
            wantStatus: http.StatusUnauthorized,
            wantOK:     false,
        },
        {
            name: "valid symbol",
            bodyJSON: map[string]any{
                "symbol": "TSLA",
            },
            userID:     u.ID,
            wantStatus: http.StatusOK,
            wantOK:     true,
        },
        {
            name: "no metrics for symbol",
            bodyJSON: map[string]any{
                "symbol": "AMZN",
            },
            userID:     u.ID,
            wantStatus: http.StatusOK,
            wantOK:     true,
        },
    }

    for _, tc := range tests {
        t.Run(tc.name, func(t *testing.T) {

            req := httptest.NewRequest("POST", "/v1/metrics/filter", mustJSONBody(t, tc.bodyJSON))
            req.Header.Set("Content-Type", "application/json")
            req = withUser(req, tc.userID)

            rr := httptest.NewRecorder()
            FilterMetricsBySymbol(app).ServeHTTP(rr, req)

            if rr.Code != tc.wantStatus {
                t.Fatalf("status = %d; want %d. body=%s",
                    rr.Code, tc.wantStatus, rr.Body.String())
            }

            res := decodeStdResp(t, rr)
            if res.Ok != tc.wantOK {
                t.Fatalf("ok = %v; want %v. body=%s",
                    res.Ok, tc.wantOK, rr.Body.String())
            }

            // validate returned data only for successful case
            if tc.name == "valid symbol" {
                data := res.Data // already map[string]any

                // symbol must be present and correct
                if sym, ok := data["symbol"].(string); !ok || sym != "TSLA" {
                    t.Fatalf("got symbol %v; want TSLA", data["symbol"])
                }

                // metrics field exists and is an array
                metricsAny, ok := data["metrics"]
                if !ok {
                    t.Fatalf("missing metrics field")
                }

                switch metrics := metricsAny.(type) {
                case []any:
                    if len(metrics) == 0 {
                        t.Fatalf("expected metrics for TSLA, got none")
                    }
                case []map[string]any:
                    if len(metrics) == 0 {
                        t.Fatalf("expected metrics for TSLA, got none")
                    }
                default:
                    t.Fatalf("metrics field has unexpected type: %T", metricsAny)
                }
            }
        })
    }
}

