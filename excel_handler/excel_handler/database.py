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
        print(f"Error getting coordinates for {location}: {e}")
    return None, None

def create_database():
    """Creates the database schema."""
    conn = psycopg2.connect(
        dbname="crimap", user="postgres", password="postgres", host="localhost", port="5434"
    )
    cur = conn.cursor()
    
    # Create tables
    cur.execute("""
    CREATE TABLE IF NOT EXISTS cities (
        id SERIAL PRIMARY KEY,
        name TEXT UNIQUE NOT NULL,
        latitude FLOAT NOT NULL,
        longitude FLOAT NOT NULL
    );

    CREATE TABLE IF NOT EXISTS neighborhoods (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        city_id INT NOT NULL REFERENCES cities(id),
        latitude FLOAT NOT NULL,
        longitude FLOAT NOT NULL,
        UNIQUE (name, city_id)
    );

    CREATE TABLE IF NOT EXISTS crime_types (
        id SERIAL PRIMARY KEY,
        category TEXT NOT NULL,
        description TEXT NOT NULL,
        UNIQUE (category, description)
    );

    CREATE TABLE IF NOT EXISTS crimes (
        id SERIAL PRIMARY KEY,
        crime_date DATE NOT NULL,
        crime_time TIME NOT NULL,
        crime_type_id INT NOT NULL REFERENCES crime_types(id),
        city_id INT NOT NULL REFERENCES cities(id),
        neighborhood_id INT REFERENCES neighborhoods(id),
        latitude FLOAT NOT NULL,
        longitude FLOAT NOT NULL
    );
    """)
    conn.commit()
    cur.close()
    conn.close()

def insert_or_get_id(cur, table: str, conflict_columns: list[str], values: dict) -> int:
    """Insert a record if it doesn't exist, and return its ID."""
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

    result = cur.fetchone()
    if result:
        return result[0]

    cur.execute(sql.SQL("""
        SELECT id FROM {table} WHERE {conditions};
        """).format(
        table=sql.Identifier(table),
        conditions=sql.SQL(" AND ").join(
            sql.SQL("{} = %s").format(sql.Identifier(k)) for k in conflict_columns
        )
    ), tuple(values[k] for k in conflict_columns))

    return cur.fetchone()[0]

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

    # Prepare a dictionary for cached coordinates
    coordinates_cache = {}

    for _, row in df.iterrows():
        crime_type_description = row["Tipo Enquadramento"]
        category = next((k for k, v in crime_categories.items() if crime_type_description in v), None)
        if not category:
            # Skip if the type does not belong to any category
            continue

        # Insert or get the crime type ID
        crime_type_id = insert_or_get_id(
            cur, 
            "crime_types", 
            ["category", "description"], 
            {"category": category, "description": crime_type_description}
        )

        city = row["Municipio Fato"]
        neighborhood = row["Bairro"] if pd.notna(row["Bairro"]) else None

        # Check if the city and neighborhood combination already has coordinates in cache
        cache_key = (city, neighborhood)
        if cache_key in coordinates_cache:
            city_lat, city_lon, neighborhood_lat, neighborhood_lon = coordinates_cache[cache_key]
        else:
            city_lat, city_lon = get_coordinates(city)
            if city_lat is None or city_lon is None:
                continue

            neighborhood_lat, neighborhood_lon = (None, None)
            if neighborhood:
                neighborhood_lat, neighborhood_lon = get_coordinates(f"{neighborhood}, {city}")
                if neighborhood_lat is None or neighborhood_lon is None:
                    neighborhood_lat, neighborhood_lon = city_lat, city_lon

            # Cache the coordinates
            coordinates_cache[cache_key] = (city_lat, city_lon, neighborhood_lat, neighborhood_lon)

        city_id = insert_or_get_id(
            cur, 
            "cities", 
            ["name"], 
            {"name": city, "latitude": city_lat, "longitude": city_lon}
        )

        neighborhood_id = None
        if neighborhood:
            neighborhood_id = insert_or_get_id(
                cur, 
                "neighborhoods", 
                ["name", "city_id"], 
                {"name": neighborhood, "city_id": city_id, "latitude": neighborhood_lat, "longitude": neighborhood_lon}
            )

        latitude, longitude = (neighborhood_lat, neighborhood_lon) if neighborhood else (city_lat, city_lon)

        cur.execute(
            sql.SQL("""
                INSERT INTO crimes (crime_date, crime_time, crime_type_id, city_id, neighborhood_id, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s, %s, %s);
                """),
            (
                row["Data Fato"],
                row["Hora Fato"],
                crime_type_id,
                city_id,
                neighborhood_id,
                latitude,
                longitude
            )
        )

    conn.commit()
    cur.close()
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

    start_date = "2024-01-01"  # Data inicial
    end_date = "2024-01-05"    # Data final

    process_csv(file_path, tipos_desejados, start_date, end_date)

if __name__ == "__main__":
    main()
