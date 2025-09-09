#https://moodle.prf.ujep.cz/mod/assign/view.php?id=14765

import pymongo as pm
import math

# Připojení k MongoDB
client = pm.MongoClient("mongodb://root:root@localhost:27017/?authSource=admin")
db = client["SZZ"]

# Kolekce
obce = db["obce"]
lekari = db["lekari"]

print("Pipelines pro analýzu dat - Ústecký kraj")
print("=" * 50)

# 1. Počty praktických ordinací v jednotlivých obcích
print("\n1. Počty praktických ordinací v jednotlivých obcích:")
print("-" * 50)
pipeline1 = [
    {
        "$group": {
            "_id": "$obec",
            "pocet_ordinaci": {"$sum": 1},
            "okres": {"$first": "$okres"}
        }
    },
    {
        "$sort": {"pocet_ordinaci": -1}
    }
]

result1 = list(lekari.aggregate(pipeline1))
print(f"Celkem obcí s ordinacemi: {len(result1)}")
print("\nTop 20 obcí s nejvíce ordinacemi:")
for i, item in enumerate(result1[:20], 1):
    print(f"  {i:2d}. {item['_id']} ({item['okres']}): {item['pocet_ordinaci']} ordinací")

# 2. Počty praktických ordinací na obyvatele v obcích
print("\n\n2. Počty praktických ordinací na obyvatele v obcích:")
print("-" * 50)
pipeline2 = [
    {
        "$group": {
            "_id": "$obec_okres",
            "obec": {"$first": "$obec"},
            "okres": {"$first": "$okres"},
            "pocet_ordinaci": {"$sum": 1}
        }
    },
    {
        "$lookup": {
            "from": "obce",
            "localField": "_id",
            "foreignField": "obec_okres",
            "as": "obec_info"
        }
    },
    {
        "$unwind": "$obec_info"
    },
    {
        "$addFields": {
            "pocet_obyvatel": "$obec_info.pocet_obyvatel",
            "prumerny_vek": "$obec_info.prumerny_vek",
            "pomer_na_1000": {
                "$cond": {
                    "if": {"$gt": ["$obec_info.pocet_obyvatel", 0]},
                    "then": {
                        "$multiply": [
                            {"$divide": ["$pocet_ordinaci", "$obec_info.pocet_obyvatel"]},
                            1000
                        ]
                    },
                    "else": 0
                }
            }
        }
    },
    {
        "$project": {
            "_id": "$obec",
            "obec": 1,
            "okres": 1,
            "pocet_ordinaci": 1,
            "pocet_obyvatel": 1,
            "prumerny_vek": 1,
            "pomer_na_1000": 1
        }
    },
    {
        "$sort": {"pomer_na_1000": -1}
    }
]

result2 = list(lekari.aggregate(pipeline2))
print(f"Celkem obcí s ordinacemi a daty o obyvatelstvu: {len(result2)}")
print("\nTop 20 obcí s nejvyšším poměrem ordinací na obyvatele:")
for i, item in enumerate(result2[:20], 1):
    print(f"  {i:2d}. {item['_id']} ({item['okres']}): {item['pomer_na_1000']:.2f} ordinací na 1000 obyvatel")
    print(f"      ({item['pocet_ordinaci']} ordinací, {item['pocet_obyvatel']:,} obyvatel, průměrný věk: {item['prumerny_vek']:.1f} let)")

# 3. Počty praktických ordinací na obyvatele v okresech
print("\n\n3. Počty praktických ordinací na obyvatele v okresech:")
print("-" * 50)
pipeline3 = [
    # Začneme s daty o obcích a spočítáme obyvatele podle okresů
    {
        "$group": {
            "_id": "$okres",
            "pocet_obyvatel": {"$sum": "$pocet_obyvatel"}
        }
    },
    # Spojíme s daty o ordinacích
    {
        "$lookup": {
            "from": "lekari",
            "localField": "_id",
            "foreignField": "okres",
            "as": "ordinace_v_okrese"
        }
    },
    {
        "$addFields": {
            "pocet_ordinaci": {"$size": "$ordinace_v_okrese"}
        }
    },
    {
        "$addFields": {
            "pomer_na_1000": {
                "$cond": {
                    "if": {"$gt": ["$pocet_obyvatel", 0]},
                    "then": {
                        "$multiply": [
                            {"$divide": ["$pocet_ordinaci", "$pocet_obyvatel"]},
                            1000
                        ]
                    },
                    "else": 0
                }
            }
        }
    },
    {
        "$sort": {"pomer_na_1000": -1}
    }
]

result3 = list(obce.aggregate(pipeline3))
print(f"Celkem okresů: {len(result3)}")
print("\nOkresy seřazené podle poměru ordinací na obyvatele:")
for i, item in enumerate(result3, 1):
    print(f"  {i}. {item['_id']}: {item['pomer_na_1000']:.2f} ordinací na 1000 obyvatel")
    print(f"     ({item['pocet_ordinaci']} ordinací, {item['pocet_obyvatel']:,} obyvatel)")

# 4. Minimální, průměrné a maximální vzdálenosti mezi ordinacemi (s MongoDB geografickou podporou)
print("\n\n4. Statistiky vzdáleností mezi ordinacemi:")
print("-" * 50)

# Vytvoření 2dsphere indexu pro geografické dotazy
print("Vytváření geografického indexu...")
try:
    lekari.create_index([("lat", 1), ("lng", 1)], name="geo_index")
    print("Geografický index vytvořen")
except Exception as e:
    print(f"Index již existuje nebo chyba: {e}")

# Získání všech ordinací s koordináty
pipeline4 = [
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
            "nazev_zarizeni": 1
        }
    }
]

ordinace_s_koordinatami = list(lekari.aggregate(pipeline4))
print(f"Ordinací s koordináty: {len(ordinace_s_koordinatami)}")

if len(ordinace_s_koordinatami) > 1:
    # Použití MongoDB geografických funkcí pro výpočet vzdáleností
    print("Výpočet vzdáleností pomocí MongoDB geografických funkcí...")
    
    # Pipeline pro nalezení nejbližších dvojic mezi různými obcemi
    pipeline_nearest = [
        {
            "$match": {
                "lat": {"$ne": None, "$exists": True},
                "lng": {"$ne": None, "$exists": True}
            }
        },
        {
            "$lookup": {
                "from": "lekari",
                "let": {"current_lat": "$lat", "current_lng": "$lng", "current_obec": "$obec"},
                "pipeline": [
                    {
                        "$match": {
                            "$expr": {
                                "$and": [
                                    {"$ne": ["$lat", None]},
                                    {"$ne": ["$lng", None]},
                                    {"$ne": ["$obec", "$$current_obec"]}  # Různé obce
                                ]
                            }
                        }
                    },
                    {
                        "$addFields": {
                            "distance": {
                                "$multiply": [
                                    6371,  # Poloměr Země v km
                                    {
                                        "$acos": {
                                            "$add": [
                                                {
                                                    "$multiply": [
                                                        {"$sin": {"$degreesToRadians": "$lat"}},
                                                        {"$sin": {"$degreesToRadians": "$$current_lat"}}
                                                    ]
                                                },
                                                {
                                                    "$multiply": [
                                                        {"$cos": {"$degreesToRadians": "$lat"}},
                                                        {"$cos": {"$degreesToRadians": "$$current_lat"}},
                                                        {"$cos": {"$degreesToRadians": {"$subtract": ["$lng", "$$current_lng"]}}}
                                                    ]
                                                }
                                            ]
                                        }
                                    }
                                ]
                            }
                        }
                    },
                    {
                        "$sort": {"distance": 1}
                    },
                    {
                        "$limit": 1
                    }
                ],
                "as": "nearest"
            }
        },
        {
            "$unwind": "$nearest"
        },
        {
            "$project": {
                "ordinace1": {
                    "obec": "$obec",
                    "nazev": "$nazev_zarizeni",
                    "lat": "$lat",
                    "lng": "$lng"
                },
                "ordinace2": {
                    "obec": "$nearest.obec",
                    "nazev": "$nearest.nazev_zarizeni",
                    "lat": "$nearest.lat",
                    "lng": "$nearest.lng"
                },
                "distance": "$nearest.distance"
            }
        },
        {
            "$sort": {"distance": 1}
        }
    ]
    
    # Spuštění pipeline pro nejbližší dvojice
    nearest_pairs = list(lekari.aggregate(pipeline_nearest))
    
    if nearest_pairs:
        # Výpočet všech vzdáleností pro statistiky
        all_distances = []
        for pair in nearest_pairs:
            all_distances.append(pair['distance'])
        
        # Přidání opačných dvojic (A->B a B->A)
        reverse_pairs = []
        for pair in nearest_pairs:
            reverse_pairs.append({
                "ordinace1": pair["ordinace2"],
                "ordinace2": pair["ordinace1"],
                "distance": pair["distance"]
            })
        
        all_pairs = nearest_pairs + reverse_pairs
        all_distances = [pair['distance'] for pair in all_pairs]
        
        if all_distances:
            min_vzdalenost = min(all_distances)
            max_vzdalenost = max(all_distances)
            prum_vzdalenost = sum(all_distances) / len(all_distances)
            
            print(f"\nStatistiky vzdáleností:")
            print(f"  Minimální vzdálenost: {min_vzdalenost:.2f} km")
            print(f"  Maximální vzdálenost: {max_vzdalenost:.2f} km")
            print(f"  Průměrná vzdálenost: {prum_vzdalenost:.2f} km")
            
            # Nejblíže dvojice
            nearest = [pair for pair in nearest_pairs if abs(pair['distance'] - min_vzdalenost) < 0.01]
            print(f"\nNejblíže ordinace ({min_vzdalenost:.2f} km):")
            for pair in nearest[:5]:  # Top 5
                print(f"  - {pair['ordinace1']['obec']} ({pair['ordinace1']['nazev']})")
                print(f"    {pair['ordinace2']['obec']} ({pair['ordinace2']['nazev']})")
            
            # Nejvzdálenější dvojice
            farthest = [pair for pair in all_pairs if abs(pair['distance'] - max_vzdalenost) < 0.01]
            print(f"\nNejvzdálenější ordinace ({max_vzdalenost:.2f} km):")
            for pair in farthest[:3]:  # Top 3
                print(f"  - {pair['ordinace1']['obec']} ({pair['ordinace1']['nazev']})")
                print(f"    {pair['ordinace2']['obec']} ({pair['ordinace2']['nazev']})")
            
            # Rozdělení vzdáleností
            do_5km = len([d for d in all_distances if d <= 5])
            do_10km = len([d for d in all_distances if d <= 10])
            
            print(f"\nRozdělení vzdáleností mezi ordinacemi:")
            print(f"  Do 5 km: {do_5km} dvojic ({do_5km/len(all_distances)*100:.1f}%)")
            print(f"  Do 10 km: {do_10km} dvojic ({do_10km/len(all_distances)*100:.1f}%)")
        else:
            print("  Nebyly nalezeny žádné vzdálenosti k výpočtu")
    else:
        print("  Nebyly nalezeny žádné dvojice ordinací")
else:
    print("  Nedostatek ordinací s koordináty pro výpočet vzdáleností")

