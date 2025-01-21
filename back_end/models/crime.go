package models

import (
	"context"
	"fmt"
	"log"
	"time"

	"crimemap.com/map/database"
	"crimemap.com/map/dto"
	"github.com/jackc/pgx/v5"
)

type Crime struct {
	ID             int            `json:"id"`
	CrimeDate      time.Time      `json:"crime_date"`
	Latitude       float64        `json:"latitude"`
	Longitude      float64        `json:"longitude"`
	SubcategoriaId      int    		`json:"subcategory_id"`
	CrimeTime      time.Time         `json:"crime_time"`
	CategoryName   string         `json:"category_name"`
}

func GetCrimes(ctx context.Context, conn *pgx.Conn, filter dto.CrimeFilter) ([]Crime, error) {
	conn = database.Connect()
	if conn == nil {
		return nil, fmt.Errorf("database connection is nil")
	}
	defer conn.Close(ctx)

	query := `
        SELECT 
            crimes.id,
            ST_X(geom) AS longitude,
            ST_Y(geom) AS latitude,
            crime_date,
						crime_time,
						crimes.subcategory_id,
						categories.name AS category_name
        FROM crimes
				JOIN category_subcategories ON crimes.subcategory_id = category_subcategories.subcategory_id
				JOIN categories ON category_subcategories.category_id = categories.id
        WHERE ST_Within(
            geom,
            ST_MakeEnvelope($1, $2, $3, $4, 4326)
        )
        AND crime_date >= $5
        AND crime_date <= $6
    `

	args := []interface{}{
		filter.West, filter.South, filter.East, filter.North,
		filter.StartDate, filter.EndDate,
	}

	// Adiciona lógica para exclusão de IDs
	if len(filter.ExcludedIDs) > 0 {
		query += " AND crimes.id != ALL($7)"
		args = append(args, filter.ExcludedIDs)
	} else {
		// Passa um array vazio explicitamente tipado
		query += " AND  crimes.id != ALL('{}'::int[])"
	}

	rows, err := conn.Query(ctx, query, args...)
	if err != nil {
		log.Printf("Database query error: %v", err)
		return nil, err
	}
	defer rows.Close()

	var crimes []Crime
	for rows.Next() {
		var crime Crime
		if err := rows.Scan(&crime.ID, &crime.Longitude, &crime.Latitude, &crime.CrimeDate, &crime.CrimeTime, &crime.SubcategoriaId, &crime.CategoryName); err != nil {
			log.Printf("Row scan error: %v", err)
			continue
		}
		crimes = append(crimes, crime)
	}

	if rows.Err() != nil {
		log.Printf("Rows error: %v", rows.Err())
		return nil, rows.Err()
	}

	fmt.Println(crimes)

	return crimes, nil
}

