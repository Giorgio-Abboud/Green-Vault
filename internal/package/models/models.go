package models

import (
	"time"

	"github.com/google/uuid"
)

// -------------------- Users --------------------
type User struct {
	UserID   uuid.UUID `gorm:"type:uuid;primaryKey"`
	Email    string    `gorm:"type:text;not null;uniqueIndex"`
	Name     string    `gorm:"type:text"`
	LastName string    `gorm:"type:text"`

	UserFills []UserFill `gorm:"constraint:OnDelete:CASCADE"`
}

// -------------------- User Fills --------------------
type UserFill struct {
	FillID    uuid.UUID `gorm:"type:uuid;primaryKey"`
	UserID    uuid.UUID `gorm:"type:uuid;not null;index"`
	Symbol    string    `gorm:"type:text"`
	Timestamp time.Time
	Price     string `gorm:"type:text"`
	Side      string `gorm:"type:text"`
	Quantity  string `gorm:"type:text"`
	Result    string `gorm:"type:text"`

	Metrics []Metric `gorm:"constraint:OnDelete:CASCADE"`

	User User `gorm:"foreignKey:UserID"`
}

// -------------------- Metrics --------------------
type Metric struct {
	MetricID   uuid.UUID `gorm:"type:uuid;primaryKey"`
	UserFillID uuid.UUID `gorm:"type:uuid;not null;index"`

	VwapSlippage    string `gorm:"type:text"`
	Shortfall       string `gorm:"type:text"`
	EffectiveSpread string `gorm:"type:text"`
	RealizedSpread  string `gorm:"type:text"`
	MarketImpact    string `gorm:"type:text"`
	Drift           string `gorm:"type:text"`

	UserFill UserFill `gorm:"foreignKey:UserFillID"`
}
