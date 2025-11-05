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
	ErrMissingUserFillData = errors.New("user_fill must have id, user_id, symbol, timestamp, side, and mode")
	ErrMissingMetricData   = errors.New("metric must have id and user_fill_id")
	ErrUserNotFound = errors.New("user not found")
)

// ---------- Users ----------

func (s *Store) CreateUser(ctx context.Context, u *models.User) (*models.User, error) {
	if u == nil || u.ID == uuid.Nil || u.Email == "" || u.PasswordHash == "" || u.Name == "" || u.LastName == "" {
		return nil, ErrMissingUserFields
	}
	if err := s.DB.WithContext(ctx).Create(u).Error; err != nil {
		return nil, err
	}
	return u, nil
}

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

func (s *Store) GetUserByID(ctx context.Context, id uuid.UUID) (*models.User, error) {
	if id == uuid.Nil {
		return nil, errors.New("id required")
	}
	var u models.User
	if err := s.DB.WithContext(ctx).First(&u, "id = ?", id).Error; err != nil {
		return nil, err
	}
	return &u, nil
}

func (s *Store) UpdateUser(ctx context.Context, u *models.User) (*models.User, error) {
	if u == nil || u.ID == uuid.Nil || u.Email == "" || u.PasswordHash == "" || u.Name == "" || u.LastName == "" {
		return nil, ErrMissingUserFields
	}
	if err := s.DB.WithContext(ctx).Save(u).Error; err != nil {
		return nil, err
	}
	return u, nil
}

func (s *Store) DeleteUser(ctx context.Context, id uuid.UUID) error {
	if id == uuid.Nil {
		return ErrMissingUserFields
	}
	result := s.DB.WithContext(ctx).Delete(&models.User{}, "id = ?", id)
	if result.Error != nil {
		return result.Error
	}
	if result.RowsAffected == 0 {
		return ErrUserNotFound
	}

	return nil
}


// ---------- User Fills ----------

func (s *Store) CreateUserFill(ctx context.Context, uf *models.UserFill) (*models.UserFill, error) {
	if uf == nil || uf.ID == uuid.Nil || uf.UserID == uuid.Nil || uf.Symbol == "" || uf.Side == "" || uf.Mode == "" || uf.Timestamp.IsZero() {
		return nil, ErrMissingUserFillData
	}
	// NOTE: uf.Price and uf.Quantity may be 0 — allowed here.
	if err := s.DB.WithContext(ctx).Create(uf).Error; err != nil {
		return nil, err
	}
	return uf, nil
}

// ---------- Metrics ----------

func (s *Store) CreateMetric(ctx context.Context, m *models.Metric) (*models.Metric, error) {
	if m == nil || m.ID == uuid.Nil || m.UserFillID == uuid.Nil {
		return nil, ErrMissingMetricData
	}
	// all floats may be 0 — allowed here
	if err := s.DB.WithContext(ctx).Create(m).Error; err != nil {
		return nil, err
	}
	return m, nil
}
