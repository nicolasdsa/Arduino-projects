import pandas as pd

# Carregar o CSV
file_path = "excel_handler/SPJ_DADOS_ABERTOS_OCORRENCIAS_JAN_NOV2024.csv"  # Substitua pelo caminho do seu arquivo
df = pd.read_csv(file_path, encoding="ISO-8859-1", sep=';')

# Nome da coluna que deseja checar
coluna = "Tipo Enquadramento"  # Substitua pelo nome da sua coluna

# Obter valores distintos
valores_filtrados = df[df[coluna].str.contains("residencia", na=False, case=False)][coluna].unique()

#valores_distintos = df[coluna].dropna().unique()

# Exibir os valores distintos
print(f"Valores distintos na coluna '{coluna}':")
for valor in valores_filtrados:
    print(valor)
