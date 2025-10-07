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

	"github.com/Giorgio-Abboud/Green-Vault/internal/package/handlers"
	"github.com/Giorgio-Abboud/Green-Vault/internal/package/models"
)

var DB *gorm.DB

// tryLoadLocalEnv loads .env.local (and .env) if they exist.
// godotenv.Load does NOT override variables that are already set,
// so Docker-provided env remains untouched.
func tryLoadLocalEnv() {
	// Prefer .env.local for local runs
	if _, err := os.Stat(".env.local"); err == nil {
		if err := godotenv.Load(".env.local"); err == nil {
			log.Println("ℹ️  Loaded environment from .env.local")
			return
		}
	}
	// Silent if neither exists; Docker/host env will be used.
}

func connectDatabase() {
	// Connect to Postgres
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
	DB = db
}

func dbMigrate() {
	// Run migrations
	if err := DB.AutoMigrate(&models.User{}, &models.UserFill{}, &models.Metric{}); err != nil {
		log.Fatalf("failed to migrate tables: %v", err)
	}
}

func main() {
	// Load local env, safe in Docker.
	tryLoadLocalEnv()

	// Connect to Postgres database
	connectDatabase()

	// Run migrations to database
	dbMigrate()

	log.Println("✅ Database connected and migrations applied!")

	secret := os.Getenv("JWT_SECRET")
	if secret == "" {
		secret = "change-me"
	}

	// Use the App type from the handlers package
	app := &handlers.App{
		DB:        DB,
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
		rt.Post("/login", handlers.Login(app))    // login -> set cookie/JWT
		rt.Get("/me", handlers.Me(app))           // whoami (auth required)
		rt.Post("/fills", handlers.SaveFill(app)) // save fill+metrics (auth required)
	})

	port := os.Getenv("API_PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("Go API listening on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, r))
}
