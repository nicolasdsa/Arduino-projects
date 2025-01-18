package routes

import (
	"net/http"

	"crimemap.com/map/controllers"
	"crimemap.com/map/middlewares"
)

func CarregaRotas() {
	//http.Handle("/getAll", controllers.GetCrimesHandler(nil))
	http.Handle("/getAll", middlewares.CorsMiddleware(controllers.GetCrimesHandler(nil)))

}