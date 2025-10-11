package handlers

import (
	"context"
	"errors"
	"net/http"
	"time"

	"github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

const sessionCookieName = "gv_session"

type ctxKey string

const ctxUserIDKey ctxKey = "uid"

// issueSession creates a JWT for the user and sets it as a secure-ish cookie.
func (a *App) issueSession(w http.ResponseWriter, userID uuid.UUID) error {
	claims := jwt.RegisteredClaims{
		Subject:   userID.String(),
		ExpiresAt: jwt.NewNumericDate(time.Now().Add(24 * time.Hour)),
		IssuedAt:  jwt.NewNumericDate(time.Now()),
	}
	t := jwt.NewWithClaims(jwt.SigningMethodHS256, claims)
	signed, err := t.SignedString([]byte(a.JWTSecret))
	if err != nil {
		return err
	}

	http.SetCookie(w, &http.Cookie{
		Name:     sessionCookieName,
		Value:    signed,
		Path:     "/",
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
		Secure:   false, // set true when serving over https
		MaxAge:   24 * 3600,
	})
	return nil
}

// clearSession removes the cookie.
func (a *App) clearSession(w http.ResponseWriter) {
	http.SetCookie(w, &http.Cookie{
		Name:     sessionCookieName,
		Value:    "",
		Path:     "/",
		HttpOnly: true,
		SameSite: http.SameSiteLaxMode,
		Secure:   false,
		MaxAge:   -1,
	})
}

// parseSession reads & validates the JWT cookie and returns the userID.
func (a *App) parseSession(r *http.Request) (uuid.UUID, error) {
	c, err := r.Cookie(sessionCookieName)
	if err != nil {
		return uuid.Nil, err
	}
	token, err := jwt.ParseWithClaims(c.Value, &jwt.RegisteredClaims{}, func(t *jwt.Token) (any, error) {
		return []byte(a.JWTSecret), nil
	}, jwt.WithValidMethods([]string{jwt.SigningMethodHS256.Name}))
	if err != nil {
		return uuid.Nil, err
	}
	rc, ok := token.Claims.(*jwt.RegisteredClaims)
	if !ok || !token.Valid {
		return uuid.Nil, errors.New("invalid token")
	}
	id, err := uuid.Parse(rc.Subject)
	if err != nil {
		return uuid.Nil, err
	}
	return id, nil
}

// AuthMiddleware enforces a valid session and injects userID in context.
func AuthMiddleware(app *App) func(http.Handler) http.Handler {
	return func(next http.Handler) http.Handler {
		return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
			uid, err := app.parseSession(r)
			if err != nil || uid == uuid.Nil {
				WriteError(w, http.StatusUnauthorized, errors.New("unauthorized"))
				return
			}
			ctx := context.WithValue(r.Context(), ctxUserIDKey, uid)
			next.ServeHTTP(w, r.WithContext(ctx))
		})
	}
}

// CurrentUserID returns the authed user id from context (or uuid.Nil).
func CurrentUserID(r *http.Request) uuid.UUID {
	if v := r.Context().Value(ctxUserIDKey); v != nil {
		if id, ok := v.(uuid.UUID); ok {
			return id
		}
	}
	return uuid.Nil
}
