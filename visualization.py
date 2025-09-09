#https://moodle.prf.ujep.cz/mod/assign/view.php?id=14765

import pymongo as pm
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import folium
from folium import plugins
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from collections import Counter
import os
import warnings
warnings.filterwarnings('ignore')

# Vytvoření složky pro vizualizace
os.makedirs('visualization', exist_ok=True)

# Nastavení pro české znaky
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['figure.figsize'] = (12, 8)

# Připojení k MongoDB
client = pm.MongoClient("mongodb://root:root@localhost:27017/?authSource=admin")
db = client["SZZ"]

# Kolekce
obce = db["obce"]
lekari = db["lekari"]

print("🗺️ Vytváření vizualizací dat o praktických ordinacích")
print("=" * 60)

# 1. Mapa s ordinacemi
print("\n1. Vytváření mapy s ordinacemi...")

# Získání dat s koordináty
pipeline_map = [
    {
        "$match": {
            "lat": {"$ne": None, "$exists": True},
            "lng": {"$ne": None, "$exists": True}
        }
    },
    {
        "$project": {
            "obec": 1,
            "okres": 1,
            "lat": 1,
            "lng": 1,
            "nazev_zarizeni": 1,
            "telefon": 1,
            "email": 1
        }
    }
]

ordinace_data = list(lekari.aggregate(pipeline_map))
print(f"Nalezeno {len(ordinace_data)} ordinací s koordináty")

if ordinace_data:
    # Vytvoření mapy
    # Střed Ústeckého kraje
    center_lat = 50.6583
    center_lng = 13.9372
    
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=9,
        tiles='OpenStreetMap'
    )
    
    # Dynamické získání všech okresů z dat
    vsechny_okresy = [ord['okres'] for ord in ordinace_data]
    vsechny_okresy = list(set(vsechny_okresy))  # Odstranění duplicit
    print(f"Nalezené okresy v datech: {vsechny_okresy}")
    
    # Definice barev pro okresy
    barvy = ['red', 'blue', 'green', 'orange', 'purple', 'darkred', 'black', 'gray', 'brown', 'pink']
    okresy_colors = {}
    for i, okres in enumerate(vsechny_okresy):
        okresy_colors[okres] = barvy[i % len(barvy)]
    
    print(f"Přiřazené barvy: {okresy_colors}")
    
    # Přidání ordinací na mapu
    for i, ord in enumerate(ordinace_data):
        color = okresy_colors.get(ord['okres'], 'gray')
        
        # Popup s informacemi
        popup_text = f"""
        <b>{ord['nazev_zarizeni']}</b><br>
        <b>Obec:</b> {ord['obec']}<br>
        <b>Okres:</b> {ord['okres']}<br>
        <b>Telefon:</b> {ord.get('telefon', 'N/A')}<br>
        <b>Email:</b> {ord.get('email', 'N/A')}
        """
        
        folium.CircleMarker(
            location=[ord['lat'], ord['lng']],
            radius=6,
            popup=folium.Popup(popup_text, max_width=300),
            color=color,
            fill=True,
            fillColor=color,
            fillOpacity=0.7
        ).add_to(m)
    
    # Dynamické vytvoření legendy pro všechny okresy
    legend_items = []
    for okres in vsechny_okresy:
        barva = okresy_colors[okres]
        legend_items.append(f'<p><span style="color:{barva}; font-size:16px">●</span> {okres}</p>')
    
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 200px; height: {140 + len(vsechny_okresy) * 20}px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px; border-radius: 5px; box-shadow: 0 0 15px rgba(0,0,0,0.2)">
    <p><b>Okresy ({len(vsechny_okresy)}):</b></p>
    {''.join(legend_items)}
    </div>
    '''
    
    # Přidání legendy jako HTML element
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Uložení mapy
    m.save('visualization/mapa_ordinaci.html')
    print("Mapa uložena jako 'visualization/mapa_ordinaci.html'")

# 2. Grafy a statistiky
print("\n2. Vytváření grafů a statistik...")

# Příprava dat pro grafy
df_lekari = pd.DataFrame(list(lekari.find()))
df_obce = pd.DataFrame(list(obce.find()))

# Graf 1: Počet ordinací podle okresů (interaktivní HTML)
print("\nVytváření interaktivního grafu ordinací podle okresů...")
okresy_counts = df_lekari['okres'].value_counts().reset_index()
okresy_counts.columns = ['okres', 'pocet_ordinaci']

# Přidání detailních informací pro tooltip
okresy_detailed = []
for okres in okresy_counts['okres']:
    okres_data = df_lekari[df_lekari['okres'] == okres]
    obce_v_okrese = okres_data['obec'].nunique()
    total_ordinace = len(okres_data)
    
    # Top 3 obce v okrese
    top_obce = okres_data['obec'].value_counts().head(3)
    top_obce_str = ', '.join([f"{obec} ({pocet})" for obec, pocet in top_obce.items()])
    
    okresy_detailed.append({
        'okres': okres,
        'pocet_ordinaci': total_ordinace,
        'pocet_obci': obce_v_okrese,
        'top_obce': top_obce_str
    })

df_okresy_detailed = pd.DataFrame(okresy_detailed)

fig1 = px.bar(df_okresy_detailed, 
              x='okres', 
              y='pocet_ordinaci',
              title='Počet praktických ordinací podle okresů - Ústecký kraj',
              color='pocet_ordinaci',
              color_continuous_scale='viridis',
              hover_data={
                  'okres': True,
                  'pocet_ordinaci': True,
                  'pocet_obci': True,
                  'top_obce': True
              },
              labels={
                  'okres': 'Okres',
                  'pocet_ordinaci': 'Počet ordinací',
                  'pocet_obci': 'Počet obcí s ordinacemi',
                  'top_obce': 'Top obce (počet ordinací)'
              })

fig1.update_layout(
    xaxis_tickangle=-45,
    showlegend=False,
    height=500,
    hovermode='closest'
)

# Přidání hodnot na sloupce
fig1.update_traces(
    texttemplate='%{y}',
    textposition='outside',
    hovertemplate='<b>%{x}</b><br>' +
                  'Ordinací: %{y}<br>' +
                  'Obcí s ordinacemi: %{customdata[0]}<br>' +
                  'Top obce: %{customdata[1]}<extra></extra>'
)

fig1.write_html('visualization/ordinace_podle_okresu_interaktivni.html')
print("Interaktivní graf uložen jako 'visualization/ordinace_podle_okresu_interaktivni.html'")

# Graf 2: Top 15 obcí s nejvíce ordinacemi (interaktivní)
print("\nVytváření interaktivního grafu top obcí...")
top_obce_data = df_lekari['obec'].value_counts().head(15).reset_index()
top_obce_data.columns = ['obec', 'pocet_ordinaci']

# Přidání detailních informací o obcích
obce_detailed = []
for obec in top_obce_data['obec']:
    obec_data = df_lekari[df_lekari['obec'] == obec]
    okres = obec_data['okres'].iloc[0]
    pocet_ordinaci = len(obec_data)
    
    # Informace o obyvatelstvu z obce kolekce
    obec_info = df_obce[df_obce['nazev_obce'] == obec]
    if not obec_info.empty:
        pocet_obyvatel = obec_info['pocet_obyvatel'].iloc[0]
        prumerny_vek = obec_info['prumerny_vek'].iloc[0]
        pomer_na_1000 = (pocet_ordinaci / pocet_obyvatel) * 1000 if pocet_obyvatel > 0 else 0
    else:
        pocet_obyvatel = "N/A"
        prumerny_vek = "N/A"
        pomer_na_1000 = "N/A"
    
    # Názvy ordinací
    nazvy_ordinaci = obec_data['nazev_zarizeni'].tolist()
    nazvy_str = ', '.join(nazvy_ordinaci[:3])  # První 3 ordinace
    if len(nazvy_ordinaci) > 3:
        nazvy_str += f" a {len(nazvy_ordinaci) - 3} dalších"
    
    obce_detailed.append({
        'obec': obec,
        'okres': okres,
        'pocet_ordinaci': pocet_ordinaci,
        'pocet_obyvatel': pocet_obyvatel,
        'prumerny_vek': prumerny_vek,
        'pomer_na_1000': pomer_na_1000,
        'nazvy_ordinaci': nazvy_str
    })

df_obce_detailed = pd.DataFrame(obce_detailed)

fig2 = px.bar(df_obce_detailed, 
              x='pocet_ordinaci', 
              y='obec',
              orientation='h',
              title='Top 15 obcí s nejvíce praktickými ordinacemi',
              color='pocet_ordinaci',
              color_continuous_scale='viridis',
              hover_data={
                  'obec': True,
                  'okres': True,
                  'pocet_ordinaci': True,
                  'pocet_obyvatel': True,
                  'prumerny_vek': True,
                  'pomer_na_1000': True,
                  'nazvy_ordinaci': True
              },
              labels={
                  'obec': 'Obec',
                  'okres': 'Okres',
                  'pocet_ordinaci': 'Počet ordinací',
                  'pocet_obyvatel': 'Počet obyvatel',
                  'prumerny_vek': 'Průměrný věk',
                  'pomer_na_1000': 'Ordinací na 1000 obyvatel',
                  'nazvy_ordinaci': 'Názvy ordinací'
              })

fig2.update_layout(
    height=600,
    showlegend=False,
    hovermode='closest',
    yaxis={'categoryorder': 'total ascending'}
)

fig2.update_traces(
    hovertemplate='<b>%{y}</b><br>' +
                  'Okres: %{customdata[0]}<br>' +
                  'Ordinací: %{x}<br>' +
                  'Obyvatel: %{customdata[1]:,}<br>' +
                  'Průměrný věk: %{customdata[2]:.1f} let<br>' +
                  'Ordinací na 1000 obyvatel: %{customdata[3]:.2f}<br>' +
                  'Ordinace: %{customdata[4]}<extra></extra>'
)

fig2.write_html('visualization/top_obce_ordinace_interaktivni.html')
print("Interaktivní graf uložen jako 'visualization/top_obce_ordinace_interaktivni.html'")

# Graf 3: Rozdělení ordinací podle velikosti obcí (interaktivní)
print("\nVytváření interaktivního koláčového grafu...")
if not df_obce.empty and not df_lekari.empty:
    # Spojení dat
    df_merged = df_lekari.merge(df_obce, left_on='obec', right_on='nazev_obce', how='left')
    
    # Kategorizace obcí podle počtu obyvatel
    def kategorizuj_obec(pocet_obyvatel):
        if pd.isna(pocet_obyvatel):
            return 'Neznámá velikost'
        elif pocet_obyvatel < 1000:
            return 'Do 1 000 obyvatel'
        elif pocet_obyvatel < 5000:
            return '1 000 - 5 000 obyvatel'
        elif pocet_obyvatel < 10000:
            return '5 000 - 10 000 obyvatel'
        elif pocet_obyvatel < 50000:
            return '10 000 - 50 000 obyvatel'
        else:
            return 'Nad 50 000 obyvatel'
    
    df_merged['kategorie_obce'] = df_merged['pocet_obyvatel'].apply(kategorizuj_obec)
    
    # Příprava dat pro interaktivní koláčový graf
    kategorie_stats = []
    for kategorie in df_merged['kategorie_obce'].unique():
        kategorie_data = df_merged[df_merged['kategorie_obce'] == kategorie]
        pocet_ordinaci = len(kategorie_data)
        pocet_obci = kategorie_data['obec'].nunique()
        
        # Průměrný počet obyvatel v kategorii
        prum_obyvatel = kategorie_data['pocet_obyvatel'].mean()
        
        # Průměrný počet ordinací na obec
        prum_ordinaci_na_obec = pocet_ordinaci / pocet_obci if pocet_obci > 0 else 0
        
        kategorie_stats.append({
            'kategorie': kategorie,
            'pocet_ordinaci': pocet_ordinaci,
            'pocet_obci': pocet_obci,
            'prum_obyvatel': prum_obyvatel,
            'prum_ordinaci_na_obec': prum_ordinaci_na_obec
        })
    
    df_kategorie_stats = pd.DataFrame(kategorie_stats)
    
    # Vytvoření koláčového grafu s pevnými tooltips
    hover_texts = []
    for _, row in df_kategorie_stats.iterrows():
        hover_text = (f"<b>{row['kategorie']}</b><br>" +
                     f"Ordinací: {row['pocet_ordinaci']}<br>" +
                     f"Obcí: {row['pocet_obci']}<br>" +
                     f"Průměr obyvatel: {row['prum_obyvatel']:,.0f}<br>" +
                     f"Průměr ordinací/obec: {row['prum_ordinaci_na_obec']:.1f}")
        hover_texts.append(hover_text)
    
    fig3 = go.Figure(data=[go.Pie(
        labels=df_kategorie_stats['kategorie'],
        values=df_kategorie_stats['pocet_ordinaci'],
        textinfo='percent+label',
        textposition='inside',
        hovertemplate='%{customdata}<extra></extra>',
        customdata=hover_texts
    )])
    
    fig3.update_layout(
        title='Rozdělení ordinací podle velikosti obcí',
        height=600,
        showlegend=True
    )
    
    fig3.write_html('visualization/ordinace_podle_velikosti_obci_interaktivni.html')
    print("Interaktivní koláčový graf uložen jako 'visualization/ordinace_podle_velikosti_obci_interaktivni.html'")

# Graf 4: Interaktivní heatmapa okresů vs. obce
print("\nVytváření interaktivní heatmapy...")

if not df_lekari.empty:
    # Top 15 obcí s nejvíce ordinacemi
    top_15_obce = df_lekari['obec'].value_counts().head(15).index.tolist()
    
    # Příprava dat pro heatmapu s detailními informacemi
    heatmap_detailed = []
    for obec in top_15_obce:
        obec_data = df_lekari[df_lekari['obec'] == obec]
        for okres in df_lekari['okres'].unique():
            pocet_v_okrese = len(obec_data[obec_data['okres'] == okres])
            if pocet_v_okrese > 0:
                # Informace o obyvatelstvu
                obec_info = df_obce[df_obce['nazev_obce'] == obec]
                pocet_obyvatel = obec_info['pocet_obyvatel'].iloc[0] if not obec_info.empty else "N/A"
                prumerny_vek = obec_info['prumerny_vek'].iloc[0] if not obec_info.empty else "N/A"
                
                # Názvy ordinací v této obci a okrese
                ordinace_v_okrese = obec_data[obec_data['okres'] == okres]
                nazvy_ordinaci = ordinace_v_okrese['nazev_zarizeni'].tolist()
                nazvy_str = ', '.join(nazvy_ordinaci[:2])  # První 2 ordinace
                if len(nazvy_ordinaci) > 2:
                    nazvy_str += f" a {len(nazvy_ordinaci) - 2} dalších"
                
                heatmap_detailed.append({
                    'obec': obec,
                    'okres': okres,
                    'pocet_ordinaci': pocet_v_okrese,
                    'pocet_obyvatel': pocet_obyvatel,
                    'prumerny_vek': prumerny_vek,
                    'nazvy_ordinaci': nazvy_str
                })
    
    df_heatmap_detailed = pd.DataFrame(heatmap_detailed)
    
    # Vytvoření pivot tabulky pro heatmapu
    heatmap_pivot = df_heatmap_detailed.pivot_table(
        index='okres', 
        columns='obec', 
        values='pocet_ordinaci', 
        fill_value=0
    )
    
    # Interaktivní heatmapa
    fig4 = px.imshow(heatmap_pivot.values,
                     x=heatmap_pivot.columns,
                     y=heatmap_pivot.index,
                     color_continuous_scale='YlOrRd',
                     title='Heatmapa: Počet ordinací podle okresů a obcí (Top 15 obcí)',
                     labels={
                         'x': 'Obec',
                         'y': 'Okres',
                         'color': 'Počet ordinací'
                     })
    
    # Přidání textu do buněk
    fig4.update_traces(
        text=heatmap_pivot.values,
        texttemplate="%{text}",
        textfont={"size": 12},
        hovertemplate='<b>%{y} - %{x}</b><br>' +
                      'Ordinací: %{z}<br>' +
                      '<extra></extra>'
    )
    
    fig4.update_layout(
        height=600,
        xaxis_tickangle=-45,
        hovermode='closest'
    )
    
    fig4.write_html('visualization/heatmapa_okresy_obce_interaktivni.html')
    print("Interaktivní heatmapa uložena jako 'visualization/heatmapa_okresy_obce_interaktivni.html'")

# 5. Statistiky a souhrn
print("\n4. Souhrnné statistiky:")
print("-" * 40)

total_ordinace = len(df_lekari)
total_obce = len(df_obce)
obce_s_ordinacemi = df_lekari['obec'].nunique()
okresy_s_ordinacemi = df_lekari['okres'].nunique()

print(f"Celkem ordinací: {total_ordinace}")
print(f"Celkem obcí v datech: {total_obce}")
print(f"Obcí s ordinacemi: {obce_s_ordinacemi}")
print(f"Okresů s ordinacemi: {okresy_s_ordinacemi}")

# Průměrný počet ordinací na obec
if obce_s_ordinacemi > 0:
    prumer_ordinaci_na_obec = total_ordinace / obce_s_ordinacemi
    print(f"Průměrný počet ordinací na obec: {prumer_ordinaci_na_obec:.2f}")

# Okres s nejvíce ordinacemi
if not df_lekari.empty:
    top_okres = df_lekari['obec'].value_counts().head(1).index[0]
    top_okres_pocet = df_lekari['obec'].value_counts().head(1).values[0]
    print(f"Obec s nejvíce ordinacemi: {top_okres} ({top_okres_pocet} ordinací)")

print("\nVšechny interaktivní vizualizace byly vytvořeny!")
print("\nVytvořené soubory se nacházejí ve složce 'visualization/':")
print("- mapa_ordinaci.html - Interaktivní mapa s ordinacemi")
print("- ordinace_podle_okresu_interaktivni.html - Interaktivní graf ordinací podle okresů")
print("- top_obce_ordinace_interaktivni.html - Interaktivní graf top obcí s ordinacemi")
print("- ordinace_podle_velikosti_obci_interaktivni.html - Interaktivní koláčový graf podle velikosti obcí")
print("- heatmapa_okresy_obce_interaktivni.html - Interaktivní heatmapa okresů vs. obcí")
