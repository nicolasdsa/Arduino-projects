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
	//CrimeTime      time.Time      `json:"crime_time"`
	Latitude    float64 `json:"latitude"`
	Longitude   float64 `json:"longitude"`
}

func GetCrimesWithinCoordinatesAndDate(ctx context.Context, conn *pgx.Conn, filter dto.CrimeFilter) ([]Crime, error) {
	conn = database.Connect()
	if conn == nil {
			return nil, fmt.Errorf("database connection is nil")
	}
	defer conn.Close(ctx)
	
	query := `
        SELECT 
            id,
            ST_X(geom) AS longitude,
            ST_Y(geom) AS latitude,
            crime_date
        FROM crimes
        WHERE ST_Within(
            geom,
            ST_MakeEnvelope($1, $2, $3, $4, 4326)
        )
        AND crime_date >= $5
        AND crime_date <= $6
    `

	rows, err := conn.Query(ctx, query, filter.West, filter.South, filter.East, filter.North, filter.StartDate, filter.EndDate)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var crimes []Crime
	for rows.Next() {
		var crime Crime
		err := rows.Scan(&crime.ID, &crime.Longitude, &crime.Latitude, &crime.CrimeDate)
		if err != nil {
			log.Printf("Error scanning row: %v", err)
			continue
		}
		crimes = append(crimes, crime)
	}

	if rows.Err() != nil {
		return nil, rows.Err()
	}

	return crimes, nil
}
	