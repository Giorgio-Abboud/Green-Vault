package main

import (
	"log"
	"net/http"
	"os"

	"github.com/go-chi/chi/v5"
	"github.com/go-chi/cors"
	"github.com/joho/godotenv"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"

	"github.com/Giorgio-Abboud/Green-Vault/internal/datastore"
	"github.com/Giorgio-Abboud/Green-Vault/internal/package/handlers"
	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

// tryLoadLocalEnv loads .env.local (and .env) if they exist.
func tryLoadLocalEnv() {
	if _, err := os.Stat(".env.local"); err == nil {
		if err := godotenv.Load(".env.local"); err == nil {
			log.Println("ℹ️  Loaded environment from .env.local")
			return
		}
	}
}

func connectDatabase() *gorm.DB {
	dbURL := os.Getenv("DB_URL")
	if dbURL == "" {
		log.Fatal("DB_URL is not set in environment")
	}
	db, err := gorm.Open(postgres.Open(dbURL), &gorm.Config{
		DisableForeignKeyConstraintWhenMigrating: false,
	})
	if err != nil {
		log.Fatalf("failed to connect db: %v", err)
	}
	return db
}

func dbMigrate(db *gorm.DB) {
	if err := db.AutoMigrate(&models.User{}, &models.UserFill{}, &models.Metric{}); err != nil {
		log.Fatalf("failed to migrate tables: %v", err)
	}
}

func main() {
	tryLoadLocalEnv()

	db := connectDatabase()
	dbMigrate(db)
	log.Println("✅ Database connected and migrations applied!")

	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		secret = "change-me"
	}

	// Handlers App uses the store
	store := datastore.New(db)
	app := &handlers.App{
		Store:     store,
		JWTSecret: secret,
	}

	r := chi.NewRouter()
	r.Use(cors.Handler(cors.Options{
		AllowedOrigins:   []string{"http://localhost:5173"},
		AllowedMethods:   []string{"GET", "POST", "PUT", "DELETE", "OPTIONS"},
		AllowedHeaders:   []string{"*"},
		AllowCredentials: true,
		MaxAge:           300,
	}))

	// Wire handlers
	r.Route("/v1", func(rt chi.Router) {
		rt.Post("/users", handlers.Signup(app))   // signup
		rt.Post("/login", handlers.Login(app))    // login
		rt.Get("/me", handlers.Me(app))           // whoami
		rt.Post("/fills", handlers.SaveFill(app)) // save fill+metrics
	})

	port := os.Getenv("API_PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("Go API listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, r))
}
