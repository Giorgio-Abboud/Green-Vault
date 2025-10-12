package handlers

import (
	"net/http"
	"net/http/httptest"
	"strings"
	"testing"

	"github.com/google/uuid"
)

func TestSaveFill(t *testing.T) {
	app := newTestApp(t)

	for _, tc := range []struct {
		name       string
		bodyJSON   any
		wantStatus int
		wantOK     bool
	}{
		{
			name:       "bad json",
			bodyJSON:   "{not-json}",
			wantStatus: http.StatusBadRequest,
			wantOK:     false,
		},
		{
			name: "bad timestamp",
			bodyJSON: map[string]any{
				"fill": map[string]any{
					"timestamp": "not-a-time",
					"price":     1.0,
					"quantity":  1,
					"side":      "buy",
					"symbol":    "XYZ",
					"mode":      "Analyze",
					"result":    "SUCCESS",
				},
				"metrics": map[string]any{},
			},
			wantStatus: http.StatusBadRequest,
			wantOK:     false,
		},
		{
			name: "valid json",
			bodyJSON: map[string]any{
				"fill": map[string]any{
					"timestamp": "2025-10-06T14:00:00Z",
					"price":     100.5,
					"quantity":  10,
					"side":      "buy",
					"symbol":    "AAPL",
					"mode":      "Analyze",
					"result":    "SUCCESS",
				},
				"metrics": map[string]any{
					"vwap_slippage":    0.15,
					"shortfall":        0.04,
					"effective_spread": 0.02,
					"realized_spread":  0.01,
					"market_impact":    0.05,
					"drift":            0.03,
				},
				"client_request_id": "abc-123",
			},
			wantStatus: http.StatusCreated,
			wantOK:     true,
		},
	} {
		t.Run(tc.name, func(t *testing.T) {
			var req *http.Request
			switch v := tc.bodyJSON.(type) {
			case string:
				req = httptest.NewRequest("POST", "/v1/fills", strings.NewReader(v))
				req.Header.Set("Content-Type", "application/json")
			default:
				req = httptest.NewRequest("POST", "/v1/fills", mustJSONBody(t, v))
				req.Header.Set("Content-Type", "application/json")
			}
			rr := httptest.NewRecorder()

			req = withUser(req, uuid.New())

			SaveFill(app).ServeHTTP(rr, req)

			if rr.Code != tc.wantStatus {
				t.Fatalf("status = %d; want %d. body=%s", rr.Code, tc.wantStatus, rr.Body.String())
			}
			res := decodeStdResp(t, rr)
			if res.Ok != tc.wantOK {
				t.Fatalf("ok = %v; want %v. body=%s", res.Ok, tc.wantOK, rr.Body.String())
			}
			if tc.wantOK {
				if _, ok := res.Data["fill_id"]; !ok {
					t.Fatalf("missing fill_id in response: %v", res.Data)
				}
				if _, ok := res.Data["metric_id"]; !ok {
					t.Fatalf("missing metric_id in response: %v", res.Data)
				}
			}
		})
	}
}
