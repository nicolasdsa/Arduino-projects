import pandas as pd
import psycopg2
from psycopg2 import sql
from geopy.geocoders import Nominatim
from datetime import datetime

def get_coordinates(location: str) -> (float, float):
    """Get latitude and longitude for a given location."""
    geolocator = Nominatim(user_agent="crime_mapping")
    try:
        loc = geolocator.geocode(location)
        if loc:
            return loc.latitude, loc.longitude
    except Exception as e:
        record_error(location, None, str(e), None)
    return None, None

def record_error(location: str, neighborhood: str, error_message: str, crime_id: int):
    """Record errors in a dedicated table and associate them with crimes."""
    conn = psycopg2.connect(
        dbname="crimap", user="postgres", password="postgres", host="localhost", port="5434"
    )
    cur = conn.cursor()

    # Insert or get location error ID
    cur.execute("""
    INSERT INTO location_errors (location, neighborhood, error_message, is_city)
    VALUES (%s, %s, %s, %s)
    ON CONFLICT (location, neighborhood, is_city) DO UPDATE SET error_message = EXCLUDED.error_message
    RETURNING id;
    """, (location, neighborhood, error_message, neighborhood is None))
    location_error_id = cur.fetchone()[0]

    # Associate the location error with the crime
    if crime_id:
        cur.execute("""
        INSERT INTO crime_location_errors (crime_id, location_error_id)
        VALUES (%s, %s) ON CONFLICT DO NOTHING;
        """, (crime_id, location_error_id))
    conn.commit()

    cur.close()
    conn.close()

def create_database():
    """Creates the database schema."""
    conn = psycopg2.connect(
        dbname="crimap", user="postgres", password="postgres", host="localhost", port="5434"
    )
    cur = conn.cursor()

    # Enable PostGIS extension
    cur.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cities (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        geom GEOMETRY(POINT, 4326) NOT NULL,
        UNIQUE (name, geom)
    );

    CREATE TABLE IF NOT EXISTS neighborhoods (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        geom GEOMETRY(POINT, 4326) NOT NULL,
        UNIQUE (name, geom)
    );

    CREATE TABLE IF NOT EXISTS city_neighborhoods (
        city_id INT NOT NULL REFERENCES cities(id),
        neighborhood_id INT NOT NULL REFERENCES neighborhoods(id),
        PRIMARY KEY (city_id, neighborhood_id)
    );

    CREATE TABLE IF NOT EXISTS categories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL
    );

    CREATE TABLE IF NOT EXISTS subcategories (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS category_subcategories (
        category_id INT NOT NULL REFERENCES categories(id),
        subcategory_id INT NOT NULL REFERENCES subcategories(id),
        PRIMARY KEY (category_id, subcategory_id)
    );

    CREATE TABLE IF NOT EXISTS crimes (
        id SERIAL PRIMARY KEY,
        crime_date DATE NOT NULL,
        crime_time TIME NOT NULL,
        subcategory_id INT NOT NULL REFERENCES subcategories(id),
        city_id INT NOT NULL REFERENCES cities(id),
        neighborhood_id INT REFERENCES neighborhoods(id),
        geom GEOMETRY(POINT, 4326) NOT NULL
    );     
    
    CREATE TABLE IF NOT EXISTS location_errors (
        id SERIAL PRIMARY KEY,
        location TEXT NOT NULL,
        neighborhood TEXT,
        error_message TEXT NOT NULL,
        is_city BOOLEAN NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE (location, neighborhood, is_city)
    );

    CREATE TABLE IF NOT EXISTS crime_location_errors (
        id SERIAL PRIMARY KEY,
        crime_id INT NOT NULL REFERENCES crimes(id) ON DELETE CASCADE,
        location_error_id INT NOT NULL REFERENCES location_errors(id) ON DELETE CASCADE,
        UNIQUE (crime_id, location_error_id)
    );          

    CREATE INDEX IF NOT EXISTS idx_crimes_geom ON crimes USING GIST (geom);
    CREATE INDEX IF NOT EXISTS idx_cities_geom ON cities USING GIST (geom);
    CREATE INDEX IF NOT EXISTS idx_neighborhoods_geom ON neighborhoods USING GIST (geom);
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert_or_get_id(cur, table: str, conflict_columns: list[str], values: dict) -> int:
    """Insert a record if it doesn't exist, and return its ID."""
    # Attempt to insert the record
    cur.execute(sql.SQL("""
        INSERT INTO {table} ({columns})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_columns}) DO NOTHING
        RETURNING id;
        """).format(
        table=sql.Identifier(table),
        columns=sql.SQL(", ").join(map(sql.Identifier, values.keys())),
        placeholders=sql.SQL(", ").join(sql.Placeholder() for _ in values.keys()),
        conflict_columns=sql.SQL(", ").join(map(sql.Identifier, conflict_columns))
    ), tuple(values.values()))

    # If the record was inserted, fetch the returned ID
    result = cur.fetchone()
    if result:
        cur.connection.commit()
        return result[0]

    # Perform SELECT to fetch the ID based on the given parameters
    cur.execute(sql.SQL("""
        SELECT id FROM {table} WHERE {conditions};
        """).format(
        table=sql.Identifier(table),
        conditions=sql.SQL(" AND ").join(
            sql.SQL("{} = ST_GeomFromText(%s, 4326)").format(sql.Identifier(k))
            if k == "geom" else sql.SQL("{} = %s").format(sql.Identifier(k))
            for k in conflict_columns
        )
    ), tuple(values[k] for k in conflict_columns))

    result = cur.fetchone()
    if result:
        return result[0]
    else:
        raise ValueError(f"Could not find or insert record in table {table} with values: {values}")

def preload_cache(cur):
    """Preload the coordinates cache with data from the database."""
    coordinates_cache = {}
    cur.execute("""
        SELECT c.name AS city, n.name AS neighborhood, ST_AsText(c.geom) AS city_geom, ST_AsText(n.geom) AS neighborhood_geom
        FROM cities c
        LEFT JOIN city_neighborhoods cn ON c.id = cn.city_id
        LEFT JOIN neighborhoods n ON cn.neighborhood_id = n.id;
    """)

    for record in cur.fetchall():
        city = record[0]
        neighborhood = record[1]
        city_geom = record[2]
        neighborhood_geom = record[3]
        coordinates_cache[(city, neighborhood)] = (city_geom, neighborhood_geom)

    return coordinates_cache

def process_csv(file_path, crime_categories, start_date: str, end_date: str):
    """Process the CSV file and insert data into the database."""
    # Convert start_date and end_date to datetime objects
    start_datetime = datetime.strptime(start_date + " 00:00:00", "%Y-%m-%d %H:%M:%S")
    end_datetime = datetime.strptime(end_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")

    # Load the CSV file
    df = pd.read_csv(file_path, encoding="ISO-8859-1", sep=';')

    # Filter rows by date range
    df["Data Fato"] = pd.to_datetime(df["Data Fato"], errors="coerce")
    df = df[(df["Data Fato"] >= start_datetime) & (df["Data Fato"] <= end_datetime)]

    # Normalize city and neighborhood names to lowercase
    df["Municipio Fato"] = df["Municipio Fato"].str.strip().str.lower()
    df["Bairro"] = df["Bairro"].str.strip().str.lower()

    conn = psycopg2.connect(
        dbname="crimap", user="postgres", password="postgres", host="localhost", port="5434"
    )
    cur = conn.cursor()

    # Preload cache with existing database data
    coordinates_cache = preload_cache(cur)

    for _, row in df.iterrows():
        crime_type_description = row["Tipo Enquadramento"].upper()
        category_name = next((k for k, v in crime_categories.items() if crime_type_description in v), None)
        if not category_name:
            continue

        # Insert or get category ID
        print(category_name)
        category_id = insert_or_get_id(
            cur, "categories", ["name"], {"name": category_name}
        )

        # Insert or get subcategory ID
        subcategory_id = insert_or_get_id(
            cur, "subcategories", ["name"], {"name": crime_type_description, "display_name": row["Tipo Enquadramento"]}
        )

        # Link category to subcategory
        cur.execute(sql.SQL("""
            INSERT INTO category_subcategories (category_id, subcategory_id)
            VALUES (%s, %s) ON CONFLICT DO NOTHING;
            """),
            (category_id, subcategory_id)
        )
        conn.commit()

        city = row["Municipio Fato"]
        neighborhood = row["Bairro"] if pd.notna(row["Bairro"]) else None

        # Check if the city and neighborhood combination already has coordinates in cache
        cache_key = (city, neighborhood)
        if cache_key in coordinates_cache:
            city_geom, neighborhood_geom = coordinates_cache[cache_key]
        else:
            city_lat, city_lon = get_coordinates(city)
            if city_lat is None or city_lon is None:
                record_error(city, None, "City coordinates not found.", None)
                city_geom = "SRID=4326;POINT(0 0)"
            else:
                city_geom = f"SRID=4326;POINT({city_lon} {city_lat})"

            neighborhood_geom = None
            if neighborhood:
                neighborhood_lat, neighborhood_lon = get_coordinates(f"{neighborhood}, {city}")
                if neighborhood_lat is None or neighborhood_lon is None:
                    record_error(city, neighborhood, "Neighborhood coordinates not found.", None)
                    neighborhood_geom = city_geom
                else:
                    neighborhood_geom = f"SRID=4326;POINT({neighborhood_lon} {neighborhood_lat})"

            # Cache the geometries
            coordinates_cache[cache_key] = (city_geom, neighborhood_geom)

        city_id = insert_or_get_id(
            cur, 
            "cities", 
            ["name"], 
            {"name": city, "geom": city_geom}
        )

        neighborhood_id = None
        if neighborhood:

            neighborhood_id = insert_or_get_id(
                cur, 
                "neighborhoods", 
                ["name", "geom"], 
                {"name": neighborhood, "geom": neighborhood_geom}
            )

            # Link city to neighborhood
            cur.execute(sql.SQL("""
                INSERT INTO city_neighborhoods (city_id, neighborhood_id)
                VALUES (%s, %s) ON CONFLICT DO NOTHING;
                """),
                (city_id, neighborhood_id)
            )
            conn.commit()

        crime_geom = neighborhood_geom if neighborhood else city_geom

        cur.execute(
            sql.SQL("""
                INSERT INTO crimes (crime_date, crime_time, subcategory_id, city_id, neighborhood_id, geom)
                VALUES (%s, %s, %s, %s, %s, %s) RETURNING id;
                """),
            (
                row["Data Fato"],
                row["Hora Fato"],
                subcategory_id,
                city_id,
                neighborhood_id,
                crime_geom
            )
        )
        crime_id = cur.fetchone()[0]
        conn.commit()

        # Record errors for invalid locations
        if city_geom == "SRID=4326;POINT(0 0)":
            record_error(city, None, "City coordinates not found.", crime_id)
        if neighborhood and neighborhood_geom == city_geom:
            record_error(city, neighborhood, "Neighborhood coordinates not found.", crime_id)

    conn.close()


def main():
    """Main function to initialize the database and process the CSV."""
    create_database()

    tipos_desejados = {
    "Roubo/Furto de telefone celular": [
        "FURTO DE TELEFONE CELULAR", "ROUBO DE TELEFONE CELULAR"
    ],
    "Roubo/Furto de veículos": [
        "FURTO DE VEICULO", "ROUBO DE VEICULO", "ROUBO DE VEICULO COM LESOES", "ROUBO DE VEICULO COM MORTE"
    ],
    "Homicídios": [
        "HOMICIDIO CULPOSO DIRECAO VEIC AUTOMOTOR", "HOMICIDIO DOLOSO", 
        "HOMICIDIO CULPOSO", "HOMICIDIO DECORRENTE DE OPOSICAO A INTERVENCAO POLICIAL", 
        "HOMICIDIO DOLOSO NA DIRECAO DE VEICULO AUTOMOTOR"
    ],
    "Casos relacionados a entorpecentes": [
        "ENTORPECENTES - TRAFICO", "ENTORPECENTES  POSSE", "ENTORPECENTE  ASSOCIACAO"
    ],
    "Lesão corporal": [
        "LESAO CORPORAL", "LESAO CORPORAL LEVE", "LESAO CORPORAL CULPOSA", 
        "LESAO CORPORAL GRAVE", "LESAO CORPORAL GRAVISSIMA", "LESAO CORPORAL SEGUIDA DE MORTE", 
        "LESAO CORPORAL DECORRENTE DE OPOSICAO A INTERVENCAO POLICIAL"
    ],
    "Crimes contra residências": [
        "FURTO/ARROMBAMENTO DE RESIDENCIA", "FURTO SIMPLES EM RESIDENCIA", 
        "ROUBO A RESIDENCIA COM LESOES", "ROUBO A RESIDENCIA", "ROUBO A RESIDENCIA COM MORTE"
    ],
    "Crimes sexuais": [
        "ESTUPRO", "ESTUPRO DE VULNERAVEL", "IMPORTUNACAO SEXUAL", 
        "ASSÉDIO SEXUAL", "EXPLORACAO SEXUAL INFANTO-JUVENIL", 
        "DIVULGACAO DE CENA DE ESTUPRO DE SEXO OU DE PORNOGRAFIA"
    ],
    "Ameaças e violência psicológica": [
        "AMEACA", "VIOLENCIA PSICOLOGICA CONTRA MULHER ART 147B", 
        "VIOLACAO SEXUAL MEDIANTE FRAUDE", "PERSEGUICAO"
    ],
    "Crimes contra o patrimônio": [
        "FURTO SIMPLES", "FURTO QUALIFICADO", "FURTO/ARROMBAMENTO", 
        "FURTO EM VEICULO", "FURTO DE DOCUMENTO", "FURTO DE FIOS E CABOS", 
        "FURTO/ARROMBAMENTO ESTABELECIMENTO COMERCIAL", "ROUBO A ESTABELECIMENTO COMERCIAL", 
        "ROUBO A ESTABELECIMENTO COMERCIAL COM MORTE", "ROUBO DE DOCUMENTO", 
        "DANO", "DANO QUALIFICADO"
    ],
    "Crimes ambientais e contra animais": [
        "CRUELDADE CONTRA ANIMAIS", "MAUS TRATOS", "OMISSAO DE CAUTELA NA GUARDA OU CONDUCAO DE ANIMAIS", 
        "CRIMES CONTRA A FAUNA", "OUTROS CRIMES CONTRA MEIO AMBIENTE", "CRIME CONTRA A ADMINISTRACAO AMBIENTAL"
    ],
    "Crimes cibernéticos": [
        "INVASAO DE DISPOSITIVO INFORMATICO", "MODIFICACAO OU ALTERACAO NAO AUTORIZADA DE SISTEMA DE INFORMACOES", 
        "DIVULGACAO DE CENA DE ESTUPRO DE SEXO OU DE PORNOGRAFIA", 
        "CONDUTAS RELAC. A PEDOFILIA NA INTERNET E OTR MEIOS DE COMUNIC."
    ],
    "Outros roubos e furtos": [
        "OUTROS FURTOS", "OUTROS ROUBOS", "FURTO DE DEFENSIVO AGRICOLA", 
        "FURTO DE ARMA", "ROUBO DE ARMA", "ROUBO DE ARMA COM LESOES"
    ],
    "Fraudes e estelionatos": [
        "ESTELIONATO", "OUTRAS FRAUDES", "FRAUDE NO PAGAMENTO POR MEIO DE CHEQUE", 
        "ESTELIONATO  FRAUDE ELETRONICA", 
        "ESTELIONATO  FRAUDE COM A UTILIZACAO DE ATIVOS VIRTUAIS VALORES MOBILIARIOS OU ATIVOS FINANCEIROS"
    ],
    "Crimes envolvendo armas": [
        "POSSE OU PORTE ILEGAL DE ARMA DE FOGO DE USO PROIBIDO", 
        "POSSE OU PORTE ILEGAL DE ARMA DE FOGO DE USO RESTRITO", 
        "PORTE ILEGAL DE ARMA DE FOGO DE USO PERMITIDO", 
        "POSSE IRREGULAR DE ARMA DE FOGO DE USO PERMITIDO", 
        "PORTE ARMA BRANCA"
    ],
    "Crimes diversos": [
        "DESACATO", "RESISTENCIA", "DESOBEDIENCIA", "PECULATO", 
        "APOLOGIA DE CRIME OU CRIMINOSO", "FALSIDADE IDEOLOGICA","RECEPTACAO DE VEICULO"
    ]
    }

    file_path = "excel_handler/SPJ_DADOS_ABERTOS_OCORRENCIAS_JAN_NOV2024.csv"  # Caminho do arquivo

    start_date = "2024-01-12"  # Data inicial
    end_date = "2024-01-31"    # Data final

    process_csv(file_path, tipos_desejados, start_date, end_date)

if __name__ == "__main__":
    main()
