package handlers

import (
	"context"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
	"github.com/google/uuid"
)

// Store is the minimal API that handlers depend on.
// The real datastore.Store satisfies this interface.
// Tests can provide a fake implementation.
type Store interface {
	CreateUser(ctx context.Context, u *models.User) (*models.User, error)
	GetUserByEmail(ctx context.Context, email string) (*models.User, error)
	GetUserByID(ctx context.Context, id uuid.UUID) (*models.User, error)
	CreateUserFill(ctx context.Context, uf *models.UserFill) (*models.UserFill, error)
	CreateMetric(ctx context.Context, m *models.Metric) (*models.Metric, error)
}
