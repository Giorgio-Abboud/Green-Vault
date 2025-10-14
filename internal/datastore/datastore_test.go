package datastore

import (
	"context"
	"testing"
	"time"

	"gorm.io/driver/sqlite"
	"gorm.io/gorm"

	"github.com/google/uuid"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

/************ test helpers ************/

func newTestDB(t *testing.T) *gorm.DB {
	t.Helper()
	db, err := gorm.Open(sqlite.Open("file::memory:?cache=shared"), &gorm.Config{})
	if err != nil {
		t.Fatalf("open sqlite: %v", err)
	}
	if err := db.AutoMigrate(&models.User{}, &models.UserFill{}, &models.Metric{}); err != nil {
		t.Fatalf("migrate: %v", err)
	}
	return db
}

func newStore(t *testing.T) *Store {
	t.Helper()
	return New(newTestDB(t))
}

/************ CreateUser ************/

func TestCreateUser(t *testing.T) {
	store := newStore(t)
	ctx := context.Background()

	for _, tc := range []struct {
		name    string
		user    models.User
		wantErr bool
	}{
		{
			name: "ok",
			user: models.User{
				ID:           uuid.New(),
				Email:        "ok@example.com",
				Name:         "Ok",
				LastName:     "User",
				PasswordHash: "hashed",
			},
			wantErr: false,
		},
		{
			name: "missing email",
			user: models.User{
				ID:           uuid.New(),
				Email:        "",
				Name:         "X",
				LastName:     "Y",
				PasswordHash: "hashed",
			},
			wantErr: true,
		},
		{
			name: "missing id",
			user: models.User{
				ID:           uuid.Nil,
				Email:        "noid@example.com",
				Name:         "X",
				LastName:     "Y",
				PasswordHash: "hashed",
			},
			wantErr: true,
		},
		{
			name: "duplicate email",
			user: models.User{
				ID:           uuid.New(),
				Email:        "ok@example.com",
				Name:         "A",
				LastName:     "B",
				PasswordHash: "hashed",
			},
			wantErr: true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			_, err := store.CreateUser(ctx, &tc.user)
			if (err != nil) != tc.wantErr {
				t.Fatalf("CreateUser err=%v wantErr=%v", err, tc.wantErr)
			}
		})
	}
}

/************ GetUserByEmail ************/

func TestGetUserByEmail(t *testing.T) {
	store := newStore(t)
	ctx := context.Background()

	u := models.User{
		ID:           uuid.New(),
		Email:        "findme@example.com",
		Name:         "Roary",
		LastName:     "Panther",
		PasswordHash: "hashed",
	}
	if _, err := store.CreateUser(ctx, &u); err != nil {
		t.Fatalf("seed CreateUser: %v", err)
	}

	for _, tc := range []struct {
		name     string
		email    string
		wantErr  bool
		wantSame bool
	}{
		{
			name:     "ok",
			email:    "findme@example.com",
			wantErr:  false,
			wantSame: true,
		},
		{
			name:     "empty email",
			email:    "",
			wantErr:  true,
			wantSame: false,
		},
		{
			name:     "not found",
			email:    "random@example.com",
			wantErr:  true,
			wantSame: false,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got, err := store.GetUserByEmail(ctx, tc.email)
			if tc.wantErr {
				if err == nil {
					t.Fatal("expected error, got nil")
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if tc.wantSame && got.Email != u.Email {
				t.Fatalf("got %q want %q", got.Email, u.Email)
			}
		})
	}
}

/************ GetUserByID ************/

func TestGetUserByID(t *testing.T) {
	store := newStore(t)
	ctx := context.Background()

	idTest := uuid.New()
	u := models.User{
		ID:           idTest,
		Email:        "myemail@email.com",
		Name:         "Roary",
		LastName:     "Panther",
		PasswordHash: "hashed",
	}
	if _, err := store.CreateUser(ctx, &u); err != nil {
		t.Fatalf("seed CreateUser: %v", err)
	}

	for _, tc := range []struct {
		name     string
		id       uuid.UUID
		wantErr  bool
		wantSame bool
	}{
		{
			name:     "ok",
			id:       idTest,
			wantErr:  false,
			wantSame: true,
		},
		{
			name:    "empty uuid",
			id:      uuid.Nil,
			wantErr: true,
		},
		{
			name:    "not found",
			id:      uuid.New(),
			wantErr: true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			got, err := store.GetUserByID(ctx, tc.id)
			if tc.wantErr {
				if err == nil {
					t.Fatal("expected error, got nil")
				}
				return
			}
			if err != nil {
				t.Fatalf("unexpected error: %v", err)
			}
			if tc.wantSame && got.ID != u.ID {
				t.Fatalf("got %q want %q", got.Email, u.Email)
			}
		})
	}
}

/************ CreateUserFill ************/

func TestCreateUserFill(t *testing.T) {
	store := newStore(t)
	ctx := context.Background()

	// seed a user
	u := models.User{
		ID:           uuid.New(),
		Email:        "fills@example.com",
		Name:         "F",
		LastName:     "L",
		PasswordHash: "hashed",
	}
	if _, err := store.CreateUser(ctx, &u); err != nil {
		t.Fatalf("seed user: %v", err)
	}

	for _, tc := range []struct {
		name    string
		fill    models.UserFill
		wantErr bool
	}{
		{
			name: "ok",
			fill: models.UserFill{
				ID:        uuid.New(),
				UserID:    u.ID,
				Symbol:    "AAPL",
				Timestamp: time.Now().UTC(),
				Price:     100.5,
				Side:      "buy",
				Quantity:  10,
				Mode:      "Analyze",
				Result:    "SUCCESS",
			},
			wantErr: false,
		},
		{
			name: "missing fields",
			fill: models.UserFill{
				ID:     uuid.Nil,
				UserID: uuid.Nil,
				Symbol: "",
				Mode:   "",
			},
			wantErr: true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			_, err := store.CreateUserFill(ctx, &tc.fill)
			if (err != nil) != tc.wantErr {
				t.Fatalf("CreateUserFill err=%v wantErr=%v", err, tc.wantErr)
			}
		})
	}
}

/************ CreateMetric ************/

func TestCreateMetric(t *testing.T) {
	store := newStore(t)
	ctx := context.Background()

	// seed user + fill
	u := models.User{
		ID:           uuid.New(),
		Email:        "metric@example.com",
		Name:         "Met",
		LastName:     "Ric",
		PasswordHash: "hashed",
	}
	if _, err := store.CreateUser(ctx, &u); err != nil {
		t.Fatalf("seed user: %v", err)
	}
	f := models.UserFill{
		ID:        uuid.New(),
		UserID:    u.ID,
		Symbol:    "TSLA",
		Timestamp: time.Now().UTC(),
		Price:     250.0,
		Side:      "sell",
		Quantity:  5,
		Mode:      "Estimate",
		Result:    "SUCCESS",
	}
	if _, err := store.CreateUserFill(ctx, &f); err != nil {
		t.Fatalf("seed fill: %v", err)
	}

	for _, tc := range []struct {
		name    string
		metric  models.Metric
		wantErr bool
	}{
		{
			name: "ok",
			metric: models.Metric{
				ID:              uuid.New(),
				UserFillID:      f.ID,
				VwapSlippage:    0.1,
				Shortfall:       0.02,
				EffectiveSpread: 0.01,
				RealizedSpread:  0.005,
				MarketImpact:    0.03,
				Drift:           0.01,
			},
			wantErr: false,
		},
		{
			name: "missing fields",
			metric: models.Metric{
				ID:         uuid.Nil,
				UserFillID: uuid.Nil,
			},
			wantErr: true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			_, err := store.CreateMetric(ctx, &tc.metric)
			if (err != nil) != tc.wantErr {
				t.Fatalf("CreateMetric err=%v wantErr=%v", err, tc.wantErr)
			}
		})
	}
}
