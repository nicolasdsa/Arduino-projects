package dto

import (
	"errors"
	"time"
)

type CrimeFilter struct {
	East       *float64 `json:"east"`
	West       *float64 `json:"west"`
	South      *float64 `json:"south"`
	North      *float64 `json:"north"`
	StartDate  string   `json:"startDate"`
	EndDate    string   `json:"endDate"`
	ExcludedIDs []int    `json:"excludedIDs,omitempty"`
	Subcategories []int    `json:"subCategories,omitempty"`
}

func (cf *CrimeFilter) Validate() error {
	// Validar coordenadas
	if cf.East == nil || cf.West == nil || cf.South == nil || cf.North == nil {
		return errors.New("all coordinates (east, west, south, north) must be provided")
	}

	if *cf.East < -180 || *cf.East > 180 || *cf.West < -180 || *cf.West > 180 {
		return errors.New("longitude must be between -180 and 180")
	}

	if *cf.South < -90 || *cf.South > 90 || *cf.North < -90 || *cf.North > 90 {
		return errors.New("latitude must be between -90 and 90")
	}

	// Validar datas
	if cf.StartDate == "" || cf.EndDate == "" {
		return errors.New("both startDate and endDate must be provided")
	}

	_, err := time.Parse("2006-01-02", cf.StartDate)
	if err != nil {
		return errors.New("invalid startDate format, must be YYYY-MM-DD")
	}

	_, err = time.Parse("2006-01-02", cf.EndDate)
	if err != nil {
		return errors.New("invalid endDate format, must be YYYY-MM-DD")
	}

	return nil
}