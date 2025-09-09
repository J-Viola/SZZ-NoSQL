# SZZ - Analýza praktických ordinací v Ústeckém kraji

Projekt pro analýzu dat o praktických ordinacích a obyvatelstvu v Ústeckém kraji s vizualizacemi a MongoDB databází.

## Struktura projektu

```
SZZ/
├── data/                                    # Datové soubory
│   ├── 1300722503.xlsx                     # Původní Excel s daty o obyvatelstvu
│   ├── obyvatele_obci.csv                  # Zpracovaná data o obyvatelstvu
│   └── prakticke_lekarstvi_dospeli.csv    # Data o praktických lékařích
├── visualization/                          # Výstupy vizualizací
│   ├── mapa_ordinaci.html                  # Interaktivní mapa
│   ├── ordinace_podle_okresu_interaktivni.html
│   ├── top_obce_ordinace_interaktivni.html
│   ├── ordinace_podle_velikosti_obci_interaktivni.html
│   └── heatmapa_okresy_obce_interaktivni.html
├── mongo.py                                # Skript pro načtení dat do MongoDB
├── pipelines.py                            # Agregační pipeliny pro MongoDB
├── visualization.py                        # Vytvoření vizualizací a map
├── data_manipulation.py                    # Převod XLSX na CSV
├── db.py                                   # Test připojení k MongoDB
├── playground.py                           # Zkoumání dat
├── docker-compose.yaml                     # Konfigurace MongoDB
├── requirements.txt                        # Python závislosti
└── README.md                               # Tento soubor
```

## Rychlé spuštění

### 1. Instalace závislostí
```bash
pip install -r requirements.txt
```

### 2. Spuštění MongoDB
```bash
docker compose up -d
```

### 3. Test připojení k databázi
```bash
python db.py
```

### 4. Převod dat
```bash
python data_manipulation.py
```

### 5. Načtení dat do MongoDB
```bash
python mongo.py
```

### 6. Vytvoření vizualizací
```bash
python visualization.py
```

### 7. Spuštění agregačních analýz
```bash
python pipelines.py
```

## Výstupy

### Interaktivní vizualizace (HTML) - složka `visualization/`
- `mapa_ordinaci.html` - Interaktivní mapa s ordinacemi
- `ordinace_podle_okresu_interaktivni.html` - Graf ordinací podle okresů
- `top_obce_ordinace_interaktivni.html` - Top obce s ordinacemi
- `ordinace_podle_velikosti_obci_interaktivni.html` - Rozdělení podle velikosti obcí
- `heatmapa_okresy_obce_interaktivni.html` - Heatmapa okresů vs. obcí

## Databáze

### MongoDB kolekce
- **`obce`** - Data o obcích z Ústeckého kraje s ordinacemi
- **`lekari`** - Data o praktických ordinacích

### Připojení k databázi
- **Host:** localhost:27017
- **Uživatel:** root
- **Heslo:** root
- **Databáze:** SZZ

## Technologie

- **Python 3**
- **MongoDB** - NoSQL databáze
- **Docker** - Kontejnerizace
- **Plotly** - Interaktivní grafy
- **Folium** - Mapy
- **Pandas** - Zpracování dat


