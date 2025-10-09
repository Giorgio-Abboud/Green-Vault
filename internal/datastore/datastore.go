package datastore

import (
	"context"
	"errors"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
	"github.com/google/uuid"
	"gorm.io/gorm"
)

type Store struct {
	DB *gorm.DB
}

func New(db *gorm.DB) *Store { return &Store{DB: db} }

// ---------- Errors ----------
var (
	ErrMissingUserFields   = errors.New("user must have id, email, name, last_name, and password_hash")
	ErrMissingUserFillData = errors.New("user_fill must have id, user_id, symbol, timestamp, and mode")
	ErrMissingMetricData   = errors.New("metric must have id and user_fill_id")
)

// ---------- Users ----------

// CreateUser creates a new user to the database
func (s *Store) CreateUser(ctx context.Context, u *models.User) (*models.User, error) {
	if u == nil || u.ID == (uuid.Nil) || u.Email == "" || u.PasswordHash == "" || u.Name == "" || u.LastName == "" {
		return nil, errors.New("missing required user fields")
	}
	if err := s.DB.WithContext(ctx).Create(u).Error; err != nil {
		return nil, err
	}
	return u, nil
}

// GetUserByEmail returns the user with the requested email
func (s *Store) GetUserByEmail(ctx context.Context, email string) (*models.User, error) {
	if email == "" {
		return nil, errors.New("email required")
	}
	var u models.User
	if err := s.DB.WithContext(ctx).First(&u, "email = ?", email).Error; err != nil {
		return nil, err
	}
	return &u, nil
}

// ---------- User Fills ----------

// CreateUserFill creates a new set of fills for the provided user
func (s *Store) CreateUserFill(ctx context.Context, uf *models.UserFill) (*models.UserFill, error) {
	if uf == nil || uf.ID == (uuid.Nil) || uf.UserID == (uuid.Nil) || uf.Symbol == "" || uf.Side == "" || uf.Quantity == "" || uf.Price == "" || uf.Mode == "" {
		return nil, errors.New("missing required user fill fields")
	}
	if err := s.DB.WithContext(ctx).Create(uf).Error; err != nil {
		return nil, err
	}
	return uf, nil
}

// ---------- Metrics ----------

// CreateMetric creates a new set of metrics for the provided fills
func (s *Store) CreateMetric(ctx context.Context, m *models.Metric) (*models.Metric, error) {
	if m == nil || m.ID == (uuid.Nil) || m.UserFillID == (uuid.Nil) {
		return nil, errors.New("missing required metric fields")
	}
	if err := s.DB.WithContext(ctx).Create(m).Error; err != nil {
		return nil, err
	}
	return m, nil
}
