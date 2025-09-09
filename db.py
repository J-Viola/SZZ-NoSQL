import pymongo as pm

# Test připojení k MongoDB
print("Testování připojení k MongoDB...")

try:
    client = pm.MongoClient("mongodb://root:root@localhost:27017/?authSource=admin", serverSelectionTimeoutMS=5000)
    server_info = client.server_info()
    print("Připojení k MongoDB úspěšné!")
    print(f"Verze MongoDB: {server_info['version']}")
    
    # Test databáze
    db = client["SZZ"]
    collections = db.list_collection_names()
    print(f"Kolekce v databázi SZZ: {collections}")
    
    # Počty dokumentů v kolekcích
    for collection_name in collections:
        count = db[collection_name].count_documents({})
        print(f"  - {collection_name}: {count} dokumentů")
    
except pm.errors.ServerSelectionTimeoutError:
    print("Nepodařilo se připojit k MongoDB!")
    print("Ujistěte se, že je MongoDB spuštěné:")
    print("ocker compose up -d")
except Exception as e:
    print(f"Chyba: {e}")

finally:
    if 'client' in locals():
        client.close()
        print("Připojení uzavřeno")
