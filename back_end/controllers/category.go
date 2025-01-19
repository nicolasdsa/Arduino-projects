package controllers

import (
	"encoding/json"
	"net/http"

	"crimemap.com/map/models"
	"github.com/jackc/pgx/v5"
)

func GetCategories(conn *pgx.Conn) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		categories, err := models.GetCategoriesWithSubcategories()
		if err != nil {
			http.Error(w, "Error fetching categories: "+err.Error(), http.StatusInternalServerError)
			return
		}
		w.Header().Set("Content-Type", "application/json")
		json.NewEncoder(w).Encode(categories)
	}
}
