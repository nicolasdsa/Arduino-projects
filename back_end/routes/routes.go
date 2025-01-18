package routes

import (
	"net/http"

	"crimemap.com/map/controllers"
)

func CarregaRotas() {
	http.Handle("/getAll", controllers.GetCrimesHandler(nil))
	//http.Handle("/getAll", middlewares.MethodNotAllowedHandler(http.HandlerFunc(controllers.GetAllCrimes)))

}