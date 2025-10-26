package handlers

import (
	"encoding/json"
	"fmt"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/google/uuid"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

type SaveFillIn struct {
	Fill struct {
		Timestamp string  `json:"timestamp"` // RFC3339 string from UI
		Price     float64 `json:"price"`     // number
		Quantity  int64   `json:"quantity"`  // number (int)
		Side      string  `json:"side"`
		Symbol    string  `json:"symbol"`
		Mode      string  `json:"mode"`
		Result    string  `json:"result"`
	} `json:"fill"`
	Metrics struct {
		VwapSlippage    float64 `json:"vwap_slippage"`
		Shortfall       float64 `json:"shortfall"`
		EffectiveSpread float64 `json:"effective_spread"`
		RealizedSpread  float64 `json:"realized_spread"`
		MarketImpact    float64 `json:"market_impact"`
		Drift           float64 `json:"drift"`
	} `json:"metrics"`
	ClientRequestID string `json:"client_request_id"`
}

// POST /v1/fills (protected)
func SaveFill(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		userID := CurrentUserID(r)
		if userID == uuid.Nil {
			WriteError(w, http.StatusUnauthorized, &Options{Error: ErrUnauthorized.Error()})
			return
		}

		var in SaveFillIn
		if err := json.NewDecoder(r.Body).Decode(&in); err != nil {
			WriteError(w, http.StatusBadRequest, &Options{Error: err.Error()})
			return
		}

		// Validation block
		fieldErrs := map[string]string{}
		reqID := uuid.New().String()

		// Timestamp (RFC3339)
		tsStr := strings.TrimSpace(in.Fill.Timestamp)
		ts, err := time.Parse(time.RFC3339, tsStr)
		if err != nil {
			fieldErrs["timestamp"] = "must be valid RFC3339 datetime (e.g. 2025-10-12T14:00:00Z)"
		}

		// Side (buy/sell)
		side := strings.ToLower(strings.TrimSpace(in.Fill.Side))
		if side != "buy" && side != "sell" {
			fieldErrs["side"] = "must be 'buy' or 'sell'"
		}

		// Mode (analyze/estimate)
		mode := strings.ToLower(strings.TrimSpace(in.Fill.Mode))
		if mode != "analyze" && mode != "estimate" {
			fieldErrs["mode"] = "must be 'analyze' or 'estimate'"
		}

		// Symbol (uppercase letters + digits)
		if !regexp.MustCompile(`^[A-Z0-9]+$`).MatchString(in.Fill.Symbol) {
			fieldErrs["symbol"] = "must contain only uppercase letters and digits (A-Z, 0-9), no spaces"
		}

		// Price precision (max 8 decimals)
		if in.Fill.Price <= 0 {
			fieldErrs["price"] = "must be a positive number"
		} else {
			s := fmt.Sprintf("%.10f", in.Fill.Price)
			parts := strings.SplitN(s, ".", 2)
			if len(parts) == 2 && len(strings.TrimRight(parts[1], "0")) > 8 {
				fieldErrs["price"] = "must have at most 8 decimal places"
			}
		}

		// Quantity (int64)
		if in.Fill.Quantity <= 0 {
			fieldErrs["quantity"] = "must be a positive integer"
		}

		// Metrics (float64 values)
		if in.Metrics.VwapSlippage == 0 &&
			in.Metrics.Shortfall == 0 &&
			in.Metrics.EffectiveSpread == 0 &&
			in.Metrics.RealizedSpread == 0 &&
			in.Metrics.MarketImpact == 0 &&
			in.Metrics.Drift == 0 {
			fieldErrs["metrics"] = "metrics must contain numeric values"
		}

		// If any validation failed
		if len(fieldErrs) > 0 {
			WriteError(w, http.StatusUnprocessableEntity, &Options{
				Error:       ErrValidationFailed.Error(),
				RequestID:   reqID,
				FieldErrors: fieldErrs,
			})
			return
		}

		fillID := uuid.New()
		metricID := uuid.New()

		// Normalize validated values
		uf := &models.UserFill{
			ID:        fillID,
			UserID:    userID,
			Symbol:    in.Fill.Symbol,
			Timestamp: ts,
			Price:     in.Fill.Price,
			Side:      side,
			Quantity:  in.Fill.Quantity,
			Mode:      mode,
			Result:    in.Fill.Result,
		}

		if _, err := app.Store.CreateUserFill(r.Context(), uf); err != nil {
			WriteError(w, http.StatusInternalServerError, &Options{Error: err.Error()})
			return
		}

		m := &models.Metric{
			ID:              metricID,
			UserFillID:      uf.ID,
			VwapSlippage:    in.Metrics.VwapSlippage,
			Shortfall:       in.Metrics.Shortfall,
			EffectiveSpread: in.Metrics.EffectiveSpread,
			RealizedSpread:  in.Metrics.RealizedSpread,
			MarketImpact:    in.Metrics.MarketImpact,
			Drift:           in.Metrics.Drift,
		}
		if _, err := app.Store.CreateMetric(r.Context(), m); err != nil {
			WriteError(w, http.StatusInternalServerError, &Options{Error: err.Error()})
			return
		}

		WriteJSON(w, http.StatusCreated, &Options{
			Data: map[string]any{
				"ok":        true,
				"req_id":    reqID,
				"fill_id":   fillID,
				"metric_id": metricID,
			},
		})
	}
}
