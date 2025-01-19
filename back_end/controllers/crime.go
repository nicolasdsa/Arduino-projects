package controllers

import (
	"context"
	"encoding/json"
	"fmt"
	"net/http"

	"crimemap.com/map/dto"
	"crimemap.com/map/models"
	"github.com/jackc/pgx/v5"
)

type Coordinates struct {
	East  float64 `json:"east"`
	West  float64 `json:"west"`
	South float64 `json:"south"`
	North float64 `json:"north"`
}

func GetCrimes(conn *pgx.Conn) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		var filter dto.CrimeFilter
		if err := json.NewDecoder(r.Body).Decode(&filter); err != nil {
			http.Error(w, "Invalid JSON input: "+err.Error(), http.StatusBadRequest)
			return
		}

		// Validar os filtros
		if err := filter.Validate(); err != nil {
			http.Error(w, err.Error(), http.StatusBadRequest)
			return
		}

		// Consultar os crimes no banco de dados
		crimes, err := models.GetCrimes(context.Background(), conn, filter)
		if err != nil {
			http.Error(w, "Database query error: "+err.Error(), http.StatusInternalServerError)
			return
		}

		// Retornar os crimes encontrados
		w.Header().Set("Content-Type", "application/json")
		fmt.Println(crimes)

		json.NewEncoder(w).Encode(crimes)
	}
}