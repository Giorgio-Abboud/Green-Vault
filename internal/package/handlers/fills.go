package handlers

import (
	"encoding/json"
	"net/http"
	"time"

	"github.com/google/uuid"
	"gorm.io/gorm"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

type SaveFillIn struct {
	Fill struct {
		Timestamp string `json:"timestamp"` // RFC3339 string
		Price     string `json:"price"`
		Quantity  string `json:"quantity"`
		Side      string `json:"side"`
		Symbol    string `json:"symbol"`
		Mode      string `json:"mode"`
		Result    string `json:"result"`
	} `json:"fill"`
	Metrics struct {
		VwapSlippage    string `json:"vwap_slippage"`
		Shortfall       string `json:"shortfall"`
		EffectiveSpread string `json:"effective_spread"`
		RealizedSpread  string `json:"realized_spread"`
		MarketImpact    string `json:"market_impact"`
		Drift           string `json:"drift"`
	} `json:"metrics"`
	ClientRequestID string `json:"client_request_id"`
}

func SaveFill(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// TODO: replace with real user id from auth/session
		userID := uuid.Nil

		var in SaveFillIn
		if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
			WriteError(w, http.StatusBadRequest, err)
			return
		}

		ts, err := time.Parse(time.RFC3339, in.Fill.Timestamp)
		if err != nil {
			WriteError(w, http.StatusBadRequest, err)
			return
		}

		fillID := uuid.New()
		metricID := uuid.New()

		err = app.DB.Transaction(func(tx *gorm.DB) error {
			uf := models.UserFill{
				ID:        fillID,
				UserID:    userID,
				Symbol:    in.Fill.Symbol,
				Timestamp: ts,
				Price:     in.Fill.Price,
				Side:      in.Fill.Side,
				Quantity:  in.Fill.Quantity,
				Mode:      in.Fill.Mode,
				Result:    in.Fill.Result,
			}
			if err := tx.Create(&uf).Error; err != nil {
				return err
			}

			m := models.Metric{
				ID:              metricID,
				UserFillID:      uf.ID,
				VwapSlippage:    in.Metrics.VwapSlippage,
				Shortfall:       in.Metrics.Shortfall,
				EffectiveSpread: in.Metrics.EffectiveSpread,
				RealizedSpread:  in.Metrics.RealizedSpread,
				MarketImpact:    in.Metrics.MarketImpact,
				Drift:           in.Metrics.Drift,
			}
			return tx.Create(&m).Error
		})

		if err != nil {
			WriteError(w, http.StatusInternalServerError, err)
			return
		}

		WriteJSON(w, http.StatusCreated, map[string]any{
			"fill_id":   fillID,
			"metric_id": metricID,
		})
	}
}
