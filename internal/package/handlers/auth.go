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

func Signup(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		type UserInfo struct {
			Email    string `json:"email"`
			Name     string `json:"name"`
			LastName string `json:"last_name"`
			Password string `json:"password"`
		}
		var body UserInfo
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

		u := models.User{
			ID:           uuid.New(),
			Email:        email,
			Name:         body.Name,
			LastName:     body.LastName,
			PasswordHash: string(hash),
		}

		created, err := app.Store.CreateUser(r.Context(), &u)
		if err != nil {
			WriteError(w, http.StatusConflict, err)
			return
		}
		WriteJSON(w, http.StatusCreated, map[string]any{
			"id":    created.ID,
			"email": created.Email,
		})
	}
}

func Login(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		type UserRequest struct {
			Email    string `json:"email"`
			Password string `json:"password"`
		}
		var body UserRequest
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

		// TODO: issue secure cookie or JWT; for now return user summary
		WriteJSON(w, http.StatusOK, map[string]any{"id": u.ID, "email": u.Email})
	}
}

func Me(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// TODO: read cookie/JWT, load user by id
		WriteError(w, http.StatusNotImplemented, errors.New("not implemented"))
	}
}
