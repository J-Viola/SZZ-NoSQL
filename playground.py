#https://moodle.prf.ujep.cz/mod/assign/view.php?id=14765

import pandas as pd

# Playground pro zkoumání dat o praktických lékařích
print("🔍 Zkoumání dat o praktických lékařích...")

# Načtení dat
df = pd.read_csv("data/prakticke_lekarstvi_dospeli.csv")

print(f"Celkem záznamů: {len(df)}")
print(f"Sloupce: {list(df.columns)}")

# Analýza sloupce DruhZarizeni
print("\nDruhy zařízení:")
druhy = df['DruhZarizeni'].value_counts()
for druh, pocet in druhy.items():
    print(f"  - {druh}: {pocet}")

# Analýza sloupce OborPece
print("\nObory péče:")
obory = df['OborPece'].value_counts()
for obor, pocet in obory.head(10).items():
    print(f"  - {obor}: {pocet}")

# Filtrování všeobecných praktických lékařů
print("\nVšeobecní praktičtí lékaři:")
vseobecni = df[df['OborPece'].str.contains('všeobecné praktické lékařství', case=False, na=False)]
print(f"Počet: {len(vseobecni)}")

# Kontrola chybějících koordinátů
print("\nKoordináty:")
print(f"Lat: {df['Lat'].isna().sum()} chybějících z {len(df)}")
print(f"Lng: {df['Lng'].isna().sum()} chybějících z {len(df)}")

# Ukázka dat
print("\nUkázka dat:")
print(vseobecni[['NazevZarizeni', 'Obec', 'Okres', 'OborPece']].head())