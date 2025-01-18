package database

import (
	"fmt"
	"log"
	"os"

	"context"

	"github.com/jackc/pgx/v5"
	"github.com/joho/godotenv"
)

func Connect() *pgx.Conn{
	err := godotenv.Load()
	if err != nil {
		log.Fatal("Error loading .env file:", err)
	}
	
	host := os.Getenv("DB_HOST")
	port := os.Getenv("DB_PORT")
	user := os.Getenv("DB_USER")
	password := os.Getenv("DB_PASSWORD")
	dbname := os.Getenv("DB_NAME")

	connStr := fmt.Sprintf("postgres://%s:%s@%s:%s/%s",
		user, password, host, port, dbname)

	_, err = pgx.ParseConfig(connStr)
	if err != nil {
		log.Fatal("Unable to parse connection string:", err)
	}

	pool, err := pgx.Connect(context.Background(), connStr)
	if err != nil {
		log.Fatal("Unable to connect to database:", err)
	}

	fmt.Println("Successfully connected to the database!")
	return pool
}