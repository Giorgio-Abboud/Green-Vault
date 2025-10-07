package models

import (
	"time"

	"github.com/google/uuid"
)

// ---------- Users ----------
type User struct {
	ID           uuid.UUID `gorm:"type:uuid;primaryKey"`
	Email        string    `gorm:"type:text;not null;uniqueIndex"`
	Name         string    `gorm:"type:text"`
	LastName     string    `gorm:"type:text"`
	PasswordHash string    `gorm:"type:text"`

	// 1-many
	UserFills []UserFill `gorm:"foreignKey:UserID;constraint:OnDelete:CASCADE;"`
}

// ---------- User Fills ----------
type UserFill struct {
	ID     uuid.UUID `gorm:"type:uuid;primaryKey"`
	UserID uuid.UUID `gorm:"type:uuid;not null;index"`

	Symbol    string    `gorm:"type:text"`
	Timestamp time.Time `gorm:"type:timestamptz"`
	Price     string    `gorm:"type:text"`
	Side      string    `gorm:"type:text"`
	Quantity  string    `gorm:"type:text"`
	Mode      string    `gorm:"type:text"`
	Result    string    `gorm:"type:text"`

	User   User
	Metric Metric `gorm:"foreignKey:UserFillID;references:ID;constraint:OnDelete:CASCADE;"`
}

// ---------- Metrics ----------
type Metric struct {
	ID         uuid.UUID `gorm:"type:uuid;primaryKey"`
	UserFillID uuid.UUID `gorm:"type:uuid;not null;uniqueIndex"`

	VwapSlippage    string `gorm:"type:text"`
	Shortfall       string `gorm:"type:text"`
	EffectiveSpread string `gorm:"type:text"`
	RealizedSpread  string `gorm:"type:text"`
	MarketImpact    string `gorm:"type:text"`
	Drift           string `gorm:"type:text"`
}
