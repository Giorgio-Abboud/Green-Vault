package handlers

import (
	"bytes"
	"encoding/json"
	"net/http/httptest"
	"testing"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

func newTestDB(t *testing.T) *gorm.DB {
	t.Helper()
	// _foreign_keys=off keeps tests isolated from FK issues while we wire auth later
	dial := sqlite.Open("file::memory:?cache=shared&_foreign_keys=off")
	db, err := gorm.Open(dial, &gorm.Config{})
	if err != nil {
		t.Fatalf("open sqlite: %v", err)
	}
	if err := db.AutoMigrate(&models.User{}, &models.UserFill{}, &models.Metric{}); err != nil {
		t.Fatalf("migrate: %v", err)
	}
	return db
}

func newTestApp(t *testing.T) *App {
	t.Helper()
	return &App{
		DB:        newTestDB(t),
		JWTSecret: "test-secret",
	}
}

// helpers
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
