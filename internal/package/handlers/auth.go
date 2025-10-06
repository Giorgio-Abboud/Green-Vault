package handlers

import (
	"encoding/json"
	"net/http"
	"strings"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"
	"gorm.io/gorm"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

type appIf interface {
	GetDB() *gorm.DB
	GetSecret() string
}
type App struct {
	DB        *gorm.DB
	JWTSecret string
}

func (a *App) GetDB() *gorm.DB   { return a.DB }
func (a *App) GetSecret() string { return a.JWTSecret }

// expose constructors that accept *App from main
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
			http.Error(w, "bad json", 400)
			return
		}

		// TODO: validate inputs (email format, pw length, etc.)
		email := strings.ToLower(strings.TrimSpace(body.Email))
		hash, _ := bcrypt.GenerateFromPassword([]byte(body.Password), bcrypt.DefaultCost)

		u := models.User{
			ID:           uuid.New(),
			Email:        email,
			Name:         body.Name,
			LastName:     body.LastName,
			PasswordHash: string(hash),
		}
		if err := app.DB.Create(&u).Error; err != nil {
			http.Error(w, err.Error(), 409)
			return
		}
		writeJSON(w, 201, map[string]any{"id": u.ID, "email": u.Email})
	}
}

func Login(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		type in struct {
			Email    string `json:"email"`
			Password string `json:"password"`
		}
		var body in
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			http.Error(w, "bad json", 400)
			return
		}
		email := strings.ToLower(strings.TrimSpace(body.Email))

		var u models.User
		if err := app.DB.First(&u, "email = ?", email).Error; err != nil {
			http.Error(w, "invalid credentials", 401)
			return
		}
		if bcrypt.CompareHashAndPassword([]byte(u.PasswordHash), []byte(body.Password)) != nil {
			http.Error(w, "invalid credentials", 401)
			return
		}

		// TODO: issue secure cookie or JWT (for now, return user id)
		// setCookie(w, sessionToken)
		writeJSON(w, 200, map[string]any{"id": u.ID, "email": u.Email})
	}
}

func Me(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		// TODO: read cookie/JWT, load user by id
		// TEMP: this is a stub — return 501 to remind us to implement
		http.Error(w, "not implemented", 501)
	}
}

// ---- helpers ----
func writeJSON(w http.ResponseWriter, code int, v any) {
	w.Header().Set("content-type", "application/json")
	w.WriteHeader(code)
	_ = json.NewEncoder(w).Encode(v)
}
