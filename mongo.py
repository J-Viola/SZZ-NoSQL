import pymongo as pm
import pandas as pd

# Připojení k MongoDB
client = pm.MongoClient("mongodb://root:root@localhost:27017/?authSource=admin")
db = client["SZZ"]

print("Připojení k MongoDB úspěšné")

# Vytvoření 2 kolekcí
obce = db["obce"]
lekari = db["lekari"]

# Načtení dat o praktických lékařích
print("\nNačítání dat o praktických lékařích...")
df_lekari = pd.read_csv("data/prakticke_lekarstvi_dospeli.csv")

# Filtrování Ústeckého kraje
df_lekari_ustecky = df_lekari[df_lekari['Kraj'] == 'Ústecký kraj']
print(f"Nalezeno {len(df_lekari_ustecky)} lékařů v Ústeckém kraji")

# Získání unikátních kombinací obcí a okresů z Ústeckého kraje
obce_okresy_ustecky = df_lekari_ustecky[['Obec', 'Okres']].drop_duplicates()
print(f"Nalezeno {len(obce_okresy_ustecky)} unikátních kombinací obcí a okresů v Ústeckém kraji")

# Načtení dat o obcích
print("\nNačítání dat o obcích...")
df_obce = pd.read_csv("data/obyvatele_obci.csv")

# Převod názvů okresů z dat o obyvatelstvu (odstranění "Okres ")
df_obce['okres_bez_prefixu'] = df_obce['okres'].str.replace('Okres ', '', regex=False)

# Filtrování pouze obcí z Ústeckého kraje (všechny obce, nejen ty s ordinacemi)
df_obce_ustecky = df_obce[df_obce['okres_bez_prefixu'].isin(obce_okresy_ustecky['Okres'].unique())]
print(f"Nalezeno {len(df_obce_ustecky)} obcí z Ústeckého kraje v datech o obyvatelstvu")

# Načtení obcí do MongoDB s denormalizací
obce_docs = []
for _, row in df_obce_ustecky.iterrows():
    # Vytvoření složeného klíče pro denormalizaci
    obec_okres_key = f"{row['nazev_obce']}_{row['okres_bez_prefixu']}"
    
    doc = {
        "obec_okres": obec_okres_key,
        "kod_obce": str(row['kod_obce']),
        "nazev_obce": row['nazev_obce'],
        "okres": row['okres_bez_prefixu'],
        "pocet_obyvatel": int(row['pocet_obyvatel_celkem']),
        "prumerny_vek": float(row['prumerny_vek_celkem'])
    }
    obce_docs.append(doc)

obce.insert_many(obce_docs)
print(f"Načteno {len(obce_docs)} obcí do MongoDB")

# Načtení lékařů do MongoDB s denormalizací
lekari_docs = []
for _, row in df_lekari_ustecky.iterrows():
    # Vytvoření složeného klíče pro denormalizaci
    obec_okres_key = f"{row['Obec']}_{row['Okres']}"
    
    doc = {
        "misto_poskytovani_id": int(row['MistoPoskytovaniId']),
        "nazev_zarizeni": row['NazevZarizeni'],
        "obec": row['Obec'],
        "okres": row['Okres'],
        "obec_okres": obec_okres_key,  # Složený klíč pro denormalizaci
        "psc": row['Psc'],
        "ulice": row['Ulice'],
        "kraj": row['Kraj'],
        "telefon": row['PoskytovatelTelefon'],
        "email": row['PoskytovatelEmail'],
        "web": row['PoskytovatelWeb'],
        "obor_pece": row['OborPece'],
        "odborny_zastupce": row['OdbornyZastupce'],
        "lat": float(row['Lat']) if pd.notna(row['Lat']) else None,
        "lng": float(row['Lng']) if pd.notna(row['Lng']) else None
    }
    lekari_docs.append(doc)

lekari.insert_many(lekari_docs)
print(f"Načteno {len(lekari_docs)} praktických lékařů do MongoDB")


# Zobrazení přehledu
print(f"\nPřehled:")
print(f"  Obce (Ústecký kraj): {obce.count_documents({})} dokumentů")
print(f"  Praktičtí lékaři (Ústecký kraj): {lekari.count_documents({})} dokumentů")

