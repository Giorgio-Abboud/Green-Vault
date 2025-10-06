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
		Timestamp time.Time `json:"timestamp"`
		Price     string    `json:"price"`
		Quantity  string    `json:"quantity"`
		Side      string    `json:"side"`
		Symbol    string    `json:"symbol"`
		Result    string    `json:"result"`
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
		// TODO: require auth, get userID from session/JWT
		// TEMP: stub user id (replace!)
		userID := uuid.Nil
		_ = userID

		var in SaveFillIn
		if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
			http.Error(w, "bad json", 400)
			return
		}
		// TODO: validate payload (side in {BUY,SELL}, symbol non-empty, etc.)

		fillID := uuid.New()
		metricID := uuid.New()

		err := app.DB.Transaction(func(tx *gorm.DB) error {
			uf := models.UserFill{
				ID:        fillID,
				UserID:    userID, // <- replace when auth implemented
				Symbol:    in.Fill.Symbol,
				Timestamp: in.Fill.Timestamp,
				Price:     in.Fill.Price,
				Side:      in.Fill.Side,
				Quantity:  in.Fill.Quantity,
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
			http.Error(w, err.Error(), 500)
			return
		}
		writeJSON(w, 201, map[string]any{"fill_id": fillID, "metric_id": metricID})
	}
}
