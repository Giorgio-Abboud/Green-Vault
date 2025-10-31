package handlers

import (
	"bytes"
	"context"
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"sync"
	"testing"

	"github.com/google/uuid"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

/*** Fake in-memory store (for unit tests) ***/

type fakeStore struct {
	mu      sync.Mutex
	users   map[string]models.User        // key: email
	fills   map[uuid.UUID]models.UserFill // key: fill ID
	metrics map[uuid.UUID]models.Metric   // key: metric ID
}

func newFakeStore() *fakeStore {
	return &fakeStore{
		users:   map[string]models.User{},
		fills:   map[uuid.UUID]models.UserFill{},
		metrics: map[uuid.UUID]models.Metric{},
	}
}

func (f *fakeStore) CreateUser(_ context.Context, u *models.User) (*models.User, error) {
	f.mu.Lock()
	defer f.mu.Unlock()

	if u == nil || u.ID == uuid.Nil || u.Email == "" || u.PasswordHash == "" {
		return nil, errors.New("invalid user params")
	}
	if _, exists := f.users[u.Email]; exists {
		return nil, errors.New("duplicate email")
	}
	f.users[u.Email] = *u
	cp := u
	return cp, nil
}

func (f *fakeStore) GetUserByEmail(_ context.Context, email string) (*models.User, error) {
	f.mu.Lock()
	defer f.mu.Unlock()

	u, ok := f.users[email]
	if !ok {
		return nil, errors.New("not found")
	}
	return &u, nil
}

func (f *fakeStore) GetUserByID(_ context.Context, id uuid.UUID) (*models.User, error) {
	f.mu.Lock()
	defer f.mu.Unlock()
	for _, u := range f.users {
		if u.ID == id {
			uu := u
			return &uu, nil
		}
	}
	return nil, errors.New("not found")
}

func (f *fakeStore) CreateUserFill(_ context.Context, uf *models.UserFill) (*models.UserFill, error) {
	f.mu.Lock()
	defer f.mu.Unlock()

	if uf == nil || uf.ID == uuid.Nil {
		return nil, errors.New("invalid fill params")
	}
	f.fills[uf.ID] = *uf
	return uf, nil
}

func (f *fakeStore) CreateMetric(_ context.Context, m *models.Metric) (*models.Metric, error) {
	f.mu.Lock()
	defer f.mu.Unlock()

	if m == nil || m.ID == uuid.Nil || m.UserFillID == uuid.Nil {
		return nil, errors.New("invalid metric params")
	}
	f.metrics[m.ID] = *m
	return m, nil
}

func (f *fakeStore) UpdateUser(_ context.Context, u *models.User) (*models.User, error) {
	f.mu.Lock()
	defer f.mu.Unlock()

	if u == nil || u.ID == uuid.Nil || u.Email == "" {
		return nil, errors.New("invalid user params")
	}

	// Find the existing user by ID
	var existingEmail string
	found := false
	for email, user := range f.users {
		if user.ID == u.ID {
			existingEmail = email
			found = true
			break
		}
	}
	if !found {
		return nil, errors.New("user not found")
	}

	// Update the record in place
	f.users[existingEmail] = *u

	// Return a copy of the updated user
	cp := *u
	return &cp, nil
}

/*** App helper for tests ***/

func newTestApp(t *testing.T) *App {
	t.Helper()
	return &App{
		Store:     newFakeStore(),
		JWTSecret: "test-secret",
	}
}

func withUser(req *http.Request, userID uuid.UUID) *http.Request {
	ctx := context.WithValue(req.Context(), ctxUserIDKey, userID)
	return req.WithContext(ctx)
}

/*** JSON helpers ***/

func mustJSONBody(t *testing.T, v any) *bytes.Reader {
	t.Helper()
	b, err := json.Marshal(v)
	if err != nil {
		t.Fatalf("marshal: %v", err)
	}
	return bytes.NewReader(b)
}

type stdResp struct {
	Ok    bool           `json:"ok"`
	Data  map[string]any `json:"data"`
	Error string         `json:"error"`
}

func decodeStdResp(t *testing.T, rr *httptest.ResponseRecorder) stdResp {
	t.Helper()
	var r stdResp
	if err := json.Unmarshal(rr.Body.Bytes(), &r); err != nil {
		t.Fatalf("decode: %v\nbody=%s", err, rr.Body.String())
	}
	return r
}