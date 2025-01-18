package main

import (
	"net/http"

	"crimemap.com/map/routes"
)

func main(){
	routes.CarregaRotas();
	http.ListenAndServe(":8000", nil);
}