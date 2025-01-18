package middlewares

import (
	"net/http"
)

// Middleware para configurar CORS
func CorsMiddleware(next http.Handler) http.Handler {
    return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
        // Configura os cabeçalhos CORS
        w.Header().Set("Access-Control-Allow-Origin", "http://127.0.0.1:4200")
        w.Header().Set("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

        // Lidar com preflight requests (OPTIONS)
        if r.Method == http.MethodOptions {
            w.WriteHeader(http.StatusOK)
            return
        }

        // Chama o próximo handler
        next.ServeHTTP(w, r)
    })
}
