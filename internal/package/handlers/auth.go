package handlers

import (
	"encoding/json"
	"errors"
	"net/http"
	"strings"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

type App struct {
	Store     Store
	JWTSecret string
}

// POST /v1/users
func Signup(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		type in struct {
			Email    string `json:"email"`
			Name     string `json:"name"`
			LastName string `json:"last_name"`
			Password string `json:"password"`
		}
		var body in
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			WriteError(w, http.StatusBadRequest, err)
			return
		}
		email := strings.ToLower(strings.TrimSpace(body.Email))
		hash, err := bcrypt.GenerateFromPassword([]byte(body.Password), bcrypt.DefaultCost)
		if err != nil {
			WriteError(w, http.StatusInternalServerError, err)
			return
		}
		u := &models.User{
			ID:           uuid.New(),
			Email:        email,
			Name:         body.Name,
			LastName:     body.LastName,
			PasswordHash: string(hash),
		}
		out, err := app.Store.CreateUser(r.Context(), u)
		if err != nil {
			WriteError(w, http.StatusConflict, err)
			return
		}
		WriteJSON(w, http.StatusCreated, map[string]any{"id": out.ID, "email": out.Email})
	}
}

// POST /v1/login
func Login(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		type in struct {
			Email    string `json:"email"`
			Password string `json:"password"`
		}
		var body in
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			WriteError(w, http.StatusBadRequest, err)
			return
		}
		email := strings.ToLower(strings.TrimSpace(body.Email))

		u, err := app.Store.GetUserByEmail(r.Context(), email)
		if err != nil {
			WriteError(w, http.StatusUnauthorized, errors.New("invalid credentials"))
			return
		}
		if bcrypt.CompareHashAndPassword([]byte(u.PasswordHash), []byte(body.Password)) != nil {
			WriteError(w, http.StatusUnauthorized, errors.New("invalid credentials"))
			return
		}

		if err := app.issueSession(w, u.ID); err != nil {
			WriteError(w, http.StatusInternalServerError, err)
			return
		}
		WriteJSON(w, http.StatusOK, map[string]any{"id": u.ID, "email": u.Email})
	}
}

// POST /v1/logout
func Logout(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		app.clearSession(w)
		WriteJSON(w, http.StatusOK, map[string]any{"message": "logged out"})
	}
}

// GET /v1/me   (protected)
func Me(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		uid := CurrentUserID(r)
		if uid == uuid.Nil {
			WriteError(w, http.StatusUnauthorized, errors.New("unauthorized"))
			return
		}
		u, err := app.Store.GetUserByID(r.Context(), uid)
		if err != nil {
			WriteError(w, http.StatusUnauthorized, errors.New("unauthorized"))
			return
		}
		WriteJSON(w, http.StatusOK, map[string]any{
			"id":        u.ID,
			"email":     u.Email,
			"name":      u.Name,
			"last_name": u.LastName,
		})
	}
}
