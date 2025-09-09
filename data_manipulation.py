#https://moodle.prf.ujep.cz/mod/assign/view.php?id=14765

import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom

def convert_xlsx_to_csv():
    """Převod XLSX na CSV s filtrováním pouze okresů z Ústeckého kraje"""
    
    print("Převod XLSX na CSV s filtrováním pouze okresů z Ústeckého kraje...")
    
    # Načtení dat o praktických lékařích pro získání okresů Ústeckého kraje
    print("Načítání dat o praktických lékařích...")
    df_lekari = pd.read_csv("data/prakticke_lekarstvi_dospeli.csv")
    
    # Filtrování pouze Ústeckého kraje
    df_lekari_ustecky = df_lekari[df_lekari['Kraj'] == 'Ústecký kraj']
    print(f"Nalezeno {len(df_lekari_ustecky)} lékařů v Ústeckém kraji")
    
    # Získání unikátních okresů z Ústeckého kraje
    okresy_ustecky = df_lekari_ustecky['Okres'].unique()
    print(f"Okresy v Ústeckém kraji: {list(okresy_ustecky)}")
    
    # Načtení Excel souboru
    df = pd.read_excel("data/1300722503.xlsx")
    print(f"Načteno {len(df)} řádků z Excel souboru")
    
    # Odstranění prázdných řádků
    df = df.dropna(how='all')
    print(f"Po odstranění prázdných řádků: {len(df)} řádků")
    
    # Inicializace výsledného seznamu
    result_data = []
    current_district = None
        
    print("\nZpracovávání dat...")
    
    for index, row in df.iterrows():
        # Kontrola, zda je řádek okresem (začíná "Okres")
        if pd.notna(row.iloc[0]) and str(row.iloc[0]).startswith("Okres"):
            current_district = str(row.iloc[0])
            # Zkontrolovat, zda je okres z Ústeckého kraje
            okres_bez_prefixu = current_district.replace("Okres ", "")
            if okres_bez_prefixu in okresy_ustecky:
                print(f"Nalezen okres z Ústeckého kraje: {current_district}")
            else:
                print(f"Přeskočen okres mimo Ústecký kraj: {current_district}")
                current_district = None  # Reset pro další řádky
            continue
            
        # Kontrola, zda je řádek obcí
        is_obec = False
        obec_data = {}
        
        # Kontrola prvního sloupce (kód okresu)
        if pd.notna(row.iloc[0]):
            kod_okresu_str = str(row.iloc[0])
            if kod_okresu_str.startswith('CZ') and len(kod_okresu_str) == 6:
                try:
                    kod_okresu = int(kod_okresu_str[2:])  # Vezme poslední 4 číslice
                    if 1000 <= kod_okresu <= 9999:  # 4-místný kód okresu
                        is_obec = True
                        obec_data['kod_okresu'] = kod_okresu
                except (ValueError, TypeError):
                    pass
        
        # Kontrola druhého sloupce (kód obce)
        if pd.notna(row.iloc[1]):
            try:
                kod_obce = int(row.iloc[1])
                if 100000 <= kod_obce <= 999999:  # 6-místný kód obce
                    is_obec = True
                    obec_data['kod_obce'] = kod_obce
            except (ValueError, TypeError):
                pass
        
        # Kontrola třetího sloupce (název obce) - pokud první je prázdný
        if not is_obec and pd.isna(row.iloc[0]) and pd.notna(row.iloc[2]):
            nazev_obce = str(row.iloc[2]).strip()
            if nazev_obce and not nazev_obce.isdigit():
                is_obec = True
                obec_data['nazev_obce'] = nazev_obce
        
        if is_obec and current_district and current_district.startswith("Okres "):
            # Přidání dat obce
            obec_data.update({
                'okres': current_district,
                'nazev_obce': obec_data.get('nazev_obce', str(row.iloc[2]) if pd.notna(row.iloc[2]) else ''),
                'pocet_obyvatel_celkem': int(row.iloc[3]) if pd.notna(row.iloc[3]) else 0,
                'pocet_obyvatel_muzi': int(row.iloc[4]) if pd.notna(row.iloc[4]) else 0,
                'pocet_obyvatel_zeny': int(row.iloc[5]) if pd.notna(row.iloc[5]) else 0,
                'prumerny_vek_celkem': float(row.iloc[6]) if pd.notna(row.iloc[6]) else 0.0,
                'prumerny_vek_muzi': float(row.iloc[7]) if pd.notna(row.iloc[7]) else 0.0,
                'prumerny_vek_zeny': float(row.iloc[8]) if pd.notna(row.iloc[8]) else 0.0
            })
            
            result_data.append(obec_data)
    
    if not result_data:
        print("Nebyla nalezena žádná data o obcích!")
        return
        
    # Vytvoření DataFrame
    df_result = pd.DataFrame(result_data)

    # Uložení do CSV
    output_file = "data/obyvatele_obci.csv"
    df_result.to_csv(output_file, index=False, encoding='utf-8')
    
    print(f"\nÚspěšně převedeno {len(df_result)} obcí")
    print(f"Uloženo jako: {output_file}")
    print(f"\nNáhled dat:")
    print(df_result.head())
    
    print(f"\nStatistiky:")
    print(f"- Celkem obcí: {len(df_result)}")
    print(f"- Unikátních okresů: {df_result['okres'].nunique()}")
    print(f"- Celkem obyvatel: {df_result['pocet_obyvatel_celkem'].sum():,}")
    
    return df_result

if __name__ == "__main__":
    convert_xlsx_to_csv()
