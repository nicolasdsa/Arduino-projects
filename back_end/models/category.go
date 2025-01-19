package models

import (
	"context"
	"fmt"

	"crimemap.com/map/database"
)

type Category struct {
	ID           int           `json:"id"`
	Name         string        `json:"name"`
	Subcategories []Subcategory `json:"subcategories"`
}

type Subcategory struct {
	ID          int    `json:"id"`
	Name        string `json:"name"`
	DisplayName string `json:"display_name"`
}

func GetCategoriesWithSubcategories() ([]Category, error) {
	conn := database.Connect()
	if conn == nil {
		return nil, fmt.Errorf("database connection is nil")
	}
	defer conn.Close(context.Background())

	query := `
        SELECT c.id, c.name, sc.id, sc.name, sc.display_name
        FROM categories c
        JOIN category_subcategories cs ON c.id = cs.category_id
        JOIN subcategories sc ON cs.subcategory_id = sc.id
    `
	rows, err := conn.Query(context.Background(), query)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	categories := make(map[int]*Category)
	for rows.Next() {
		var categoryID, subcategoryID int
		var categoryName, subcategoryName, subcategoryDisplayName string
		if err := rows.Scan(&categoryID, &categoryName, &subcategoryID, &subcategoryName, &subcategoryDisplayName); err != nil {
			return nil, err
		}

		if _, exists := categories[categoryID]; !exists {
			categories[categoryID] = &Category{
				ID:           categoryID,
				Name:         categoryName,
				Subcategories: []Subcategory{},
			}
		}
		categories[categoryID].Subcategories = append(categories[categoryID].Subcategories, Subcategory{
			ID:          subcategoryID,
			Name:        subcategoryName,
			DisplayName: subcategoryDisplayName,
		})
	}

	// Converte para slice
	result := []Category{}
	for _, category := range categories {
		result = append(result, *category)
	}

	return result, nil
}
