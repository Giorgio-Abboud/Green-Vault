package handlers

import (
	"encoding/json"
	"net/http"
	"regexp"
	"strings"
	"time"

	"github.com/google/uuid"
	"golang.org/x/crypto/bcrypt"

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

type App struct {
	Store     Store
	JWTSecret string
}

var (
	reEmail    = regexp.MustCompile(`^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$`)
	reLower    = regexp.MustCompile(`[a-z]`)
	reUpper    = regexp.MustCompile(`[A-Z]`)
	reDigit    = regexp.MustCompile(`\d`)
	reSymbol   = regexp.MustCompile(`[^A-Za-z0-9]`)
	reName     = regexp.MustCompile(`^[A-Za-z' -]{2,100}$`)
	reLastName = regexp.MustCompile(`^[A-Za-z' -]{2,100}$`)
)

// POST /v1/users
func Signup(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		reqID := uuid.NewString()

		type in struct {
			Email    string `json:"email"`
			Name     string `json:"name"`
			LastName string `json:"last_name"`
			Password string `json:"password"`
		}

		var body in
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			WriteError(w, http.StatusBadRequest, &Options{Error: err.Error()})
			return
		}

		// SignUp validation section
		fieldErrs := make(map[string]string)

		// Normalize inputs
		email := strings.ToLower(strings.TrimSpace(body.Email))
		name := strings.TrimSpace(body.Name)
		lastName := strings.TrimSpace(body.LastName)
		password := body.Password

		// Email validation
		if email == "" {
			fieldErrs["email"] = "required"
		} else if len(email) > 254 {
			fieldErrs["email"] = "too long"
		} else if !reEmail.MatchString(email) {
			fieldErrs["email"] = "invalid format"
		} else {
			// Check if email already exists in the DB
			if existing, err := app.Store.GetUserByEmail(r.Context(), email); err == nil && existing != nil {
				WriteError(w, http.StatusConflict, &Options{Error: ErrDuplicateEmail.Error()})
				return
			}
		}

		// Password validation
		if password == "" {
			fieldErrs["password"] = "required"
		} else {
			if len(password) < 12 {
				fieldErrs["password"] = "too short (min 12 chars)"
			} else if len(password) > 128 {
				fieldErrs["password"] = "too long (max 128 chars)"
			} else {
				switch {
				case !reLower.MatchString(password):
					fieldErrs["password"] = "must contain a lowercase letter"
				case !reUpper.MatchString(password):
					fieldErrs["password"] = "must contain an uppercase letter"
				case !reDigit.MatchString(password):
					fieldErrs["password"] = "must contain a digit"
				case !reSymbol.MatchString(password):
					fieldErrs["password"] = "must contain a symbol"
				}
			}
		}

		// Name validation
		if name == "" {
			fieldErrs["name"] = "required"
		} else if len(name) > 100 {
			fieldErrs["name"] = "too long"
		} else {
			if !reName.MatchString(name) {
				fieldErrs["name"] = "invalid characters"
			}
		}

		// Last name validation
		if lastName == "" {
			fieldErrs["last_name"] = "required"
		} else if len(lastName) > 100 {
			fieldErrs["last_name"] = "too long"
		} else {
			if !reLastName.MatchString(lastName) {
				fieldErrs["last_name"] = "invalid characters"
			}
		}

		// If any validation errors exist, return 422
		if len(fieldErrs) > 0 {
			WriteError(w, http.StatusUnprocessableEntity, &Options{
				Error:       ErrValidationFailed.Error(),
				RequestID:   reqID,
				FieldErrors: fieldErrs,
			})
			return
		}

		// Passed validation, generate hash
		hash, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
		if err != nil {
			WriteError(w, http.StatusInternalServerError, &Options{Error: err.Error()})
			return
		}

		u := &models.User{
			ID:           uuid.New(),
			Email:        email,
			Name:         name,
			LastName:     lastName,
			PasswordHash: string(hash),
		}

		out, err := app.Store.CreateUser(r.Context(), u)
		if err != nil {
			WriteError(w, http.StatusConflict, &Options{Error: err.Error()})
			return
		}

		WriteJSON(w, http.StatusCreated, &Options{
			Data: map[string]any{
				"id":    out.ID,
				"email": out.Email,
			},
		})
	}
}

// POST /v1/login
func Login(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		reqID := uuid.NewString()
		type in struct {
			Email    string `json:"email"`
			Password string `json:"password"`
		}
		var body in
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			WriteError(w, http.StatusBadRequest, &Options{Error: err.Error()})
			return
		}

		// Login validation section
		fieldErrs := make(map[string]string)

		// Normalize inputs
		email := strings.ToLower(strings.TrimSpace(body.Email))
		password := body.Password

		// Email validation
		if email == "" {
			fieldErrs["email"] = "required"
		} else if len(email) > 254 {
			fieldErrs["email"] = "too long"
		} else if !reEmail.MatchString(email) {
			fieldErrs["email"] = "invalid format"
		}

		// Password validation
		if password == "" {
			fieldErrs["password"] = "required"
		}

		// If any validation errors exist, return 422
		if len(fieldErrs) > 0 {
			WriteError(w, http.StatusUnprocessableEntity, &Options{
				Error:       ErrValidationFailed.Error(),
				RequestID:   reqID,
				FieldErrors: fieldErrs,
			})
			return
		}

		// Passed validation, query user
		u, err := app.Store.GetUserByEmail(r.Context(), email)
		if err != nil {
			WriteError(w, http.StatusUnauthorized, &Options{Error: ErrInvalidCredentials.Error()})
			return
		}
		if bcrypt.CompareHashAndPassword([]byte(u.PasswordHash), []byte(body.Password)) != nil {
			WriteError(w, http.StatusUnauthorized, &Options{Error: ErrInvalidCredentials.Error()})
			return
		}

		if err := app.issueSession(w, u.ID); err != nil {
			WriteError(w, http.StatusInternalServerError, &Options{Error: err.Error()})
			return
		}
		WriteJSON(w, http.StatusOK, &Options{
			Data: map[string]any{
				"id":    u.ID,
				"email": u.Email,
			},
		})
	}
}

// POST /v1/logout
func Logout(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		app.clearSession(w)
		WriteJSON(w, http.StatusOK, &Options{
			Data: map[string]any{
				"message": "logged out",
			},
		})
	}
}

// GET /v1/me   (protected)
func Me(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		uid := CurrentUserID(r)
		if uid == uuid.Nil {
			WriteError(w, http.StatusUnauthorized, &Options{Error: ErrUnauthorized.Error()})
			return
		}
		u, err := app.Store.GetUserByID(r.Context(), uid)
		if err != nil {
			WriteError(w, http.StatusInternalServerError, &Options{Error: ErrLookup.Error()})
			return
		}
		WriteJSON(w, http.StatusOK, &Options{
			Data: map[string]any{
				"id":        u.ID,
				"email":     u.Email,
				"name":      u.Name,
				"last_name": u.LastName,
			},
		})
	}
}

// PUT /v1/users/me   (protected)
func EditProfile(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		reqID := uuid.NewString()

		type in struct {
			OldPassword     string `json:"old_password"`
			NewPassword     string `json:"new_password"`
			ConfirmPassword string `json:"confirm_password"`
		}

		var body in
		if err := json.NewDecoder(r.Body).Decode(&body); err != nil {
			WriteError(w, http.StatusBadRequest, &Options{Error: err.Error()})
			return
		}

		// Edit Profile validation section
		fieldErrs := make(map[string]string)

		// Normalize inputs
		oldPassword := body.OldPassword
		newPassword := body.NewPassword
		confirmPassword := body.ConfirmPassword

		// Old password validation
		if oldPassword == "" {
			fieldErrs["old_password"] = "required"
		}

		// New password validation
		if newPassword == "" {
			fieldErrs["new_password"] = "required"
		} else {
			if len(newPassword) < 12 {
				fieldErrs["new_password"] = "too short (min 12 chars)"
			} else if len(newPassword) > 128 {
				fieldErrs["new_password"] = "too long (max 128 chars)"
			} else {
				switch {
				case !reLower.MatchString(newPassword):
					fieldErrs["new_password"] = "must contain a lowercase letter"
				case !reUpper.MatchString(newPassword):
					fieldErrs["new_password"] = "must contain an uppercase letter"
				case !reDigit.MatchString(newPassword):
					fieldErrs["new_password"] = "must contain a digit"
				case !reSymbol.MatchString(newPassword):
					fieldErrs["new_password"] = "must contain a symbol"
				}
			}
		}

		// Confirm password validation
		if confirmPassword == "" {
			fieldErrs["confirm_password"] = "required"
		} else if confirmPassword != newPassword {
			fieldErrs["confirm_password"] = "does not match"
		}

		// If any validation errors exist, return 422
		if len(fieldErrs) > 0 {
			WriteError(w, http.StatusUnprocessableEntity, &Options{
				Error:       ErrValidationFailed.Error(),
				RequestID:   reqID,
				FieldErrors: fieldErrs,
			})
			return
		}

		// Passed validation, get user of the current session
		uid := CurrentUserID(r)
		if uid == uuid.Nil {
			WriteError(w, http.StatusUnauthorized, &Options{Error: ErrUnauthorized.Error()})
			return
		}
		u, err := app.Store.GetUserByID(r.Context(), uid)
		if err != nil {
			WriteError(w, http.StatusInternalServerError, &Options{Error: ErrLookup.Error()})
			return
		}

		// Compare old password matches user's password
		if bcrypt.CompareHashAndPassword([]byte(u.PasswordHash), []byte(oldPassword)) != nil {
			WriteError(w, http.StatusUnauthorized, &Options{Error: ErrInvalidCredentials.Error()})
			return
		}

		// Generate hash for updated password
		newHash, err := bcrypt.GenerateFromPassword([]byte(newPassword), bcrypt.DefaultCost)
		if err != nil {
			WriteError(w, http.StatusInternalServerError, &Options{Error: err.Error()})
			return
		}

		u.PasswordHash = string(newHash)

		// Update the user with the new password
		out, err := app.Store.UpdateUser(r.Context(), u)
		if err != nil {
			WriteError(w, http.StatusConflict, &Options{Error: err.Error()})
			return
		}

		WriteJSON(w, http.StatusOK, &Options{
			Data: map[string]any{
				"id":        out.ID,
				"email":     out.Email,
				"name":      out.Name,
				"last_name": out.LastName,
			},
		})
	}
}

func DeleteUser(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		reqID := uuid.NewString()

		// Get current logged-in user's ID
		uid := CurrentUserID(r)
		if uid == uuid.Nil {
			WriteError(w, http.StatusUnauthorized, &Options{
				Error: ErrUnauthorized.Error(),
			})
			return
		}

		// Delete the user from the database
		u, err := app.Store.DeleteUser(r.Context(), uid)
		if err != nil {
			WriteError(w, http.StatusInternalServerError, &Options{
				Error:     err.Error(),
				RequestID: reqID,
			})
			return
		}

		// Clear session cookie after successful deletion
		app.clearSession(w)

		// Send confirmation response
		WriteJSON(w, http.StatusNoContent, &Options{
			Data: map[string]any{
				"message":    "account deleted successfully",
				"user_id":    uid,
				"name":       u.Name,
				"email":      u.Email,
				"deleted_at": time.Now().UTC(),
			},
			RequestID: reqID,
		})
	}
}

func ListUserFillsAndMetrics(app *App) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		reqID := uuid.NewString()

		uid := CurrentUserID(r)
		if uid == uuid.Nil {
			WriteError(w, http.StatusUnauthorized, &Options{
				Error:     ErrUnauthorized.Error(),
				RequestID: reqID,
			})
			return
		}

		// Optional filter if provided
		symbol := r.URL.Query().Get("symbol")

		fills, err := app.Store.ListUserFillsWithMetrics(
			r.Context(),
			uid,
			symbol, // pass symbol filter
		)
		if err != nil {
			WriteError(w, http.StatusInternalServerError, &Options{
				Error:     ErrLookup.Error(),
				RequestID: reqID,
			})
			return
		}

		WriteJSON(w, http.StatusOK, &Options{
			RequestID: reqID,
			Data: map[string]any{
				"user_id": uid,
				"fills":   fills,
			},
		})
	}
}
