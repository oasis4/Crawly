# Crawly Data Validator & Sync

Script zur Validierung und Synchronisierung von Lidl-Produktdaten zwischen Datenbanken.

## 📋 Workflow

```
Scraper → crawly_lidl_db
           ↓
      [Validation]  ← Prüft auf Fehler
           ↓
      [Sync]        ← Überträgt saubere Daten
           ↓
      crawly_db    ← Master-DB für API
```

## 🚀 Nutzung

### Einfach starten:
```powershell
python sync_and_validate.py
```

## ✅ Validierungen

Das Script prüft auf folgende Probleme:

| Check | Kritisch | Beschreibung |
|-------|----------|-------------|
| Fehlende Namen | ⚠️ | Produkt ohne Namen |
| Fehlende Preise | ❌ | Produkt ohne oder mit ungültigem Preis |
| Fehlende SKU | ❌ | Keine eindeutige Kennung |
| Fehlende Lidl-ID | ⚠️ | Innere Lidl-Produktkennung fehlt |
| Duplikate | ⚠️ | Mehrfach vorhandene SKU |
| Negative Preise | ❌ | Ungültige Preise |
| Verwaiste History | ⚠️ | History-Einträge ohne Produkt |

**Legend:**
- ❌ = **Kritisch** - Sync wird abgebrochen
- ⚠️ = **Warnung** - Wird geloggt, Sync läuft weiter

## 📊 Output

### Bei Erfolg:
```
VALIDATION SUMMARY:
✅ Validation PASSED - Data quality OK

SYNC PHASE: Transferring clean data to crawly_db
✓ Synced 96 products
✓ Synced 2 scraper runs

Final Statistics:
  • Products synced: 96
  • Products skipped: 0
  • Scraper runs synced: 2

✅ crawly_db is now ready for API queries!
   96 clean products available
```

### Bei Fehler:
```
VALIDATION SUMMARY:
❌ CRITICAL ISSUES (2):
  ❌ 5 products missing/invalid price
  ❌ 3 products missing SKU

❌ Validation FAILED - Sync aborted
   Please fix the critical issues in crawly_lidl_db before syncing
```

## 🔄 Workflow-Beispiel

```powershell
# 1. Scraper läuft und füllt crawly_lidl_db
python run_scraper.py --max-pages 10

# 2. Validieren & Synchronisieren
python sync_and_validate.py

# 3. API liest saubere Daten aus crawly_db
curl http://localhost:8001/products
```

## 📝 Konfiguration

Umgebungsvariablen (optional):

```powershell
# Lidl-Datenbank (wo Scraper schreibt)
$env:LIDL_DATABASE_URL="mysql+pymysql://crawly_user:***@localhost:3306/crawly_lidl_db"

# Master-Datenbank (wo API liest)
$env:MASTER_DATABASE_URL="mysql+pymysql://crawly_user:***@localhost:3306/crawly_db"

# Dann Script starten
python sync_and_validate.py
```

## 🎯 Was passiert beim Sync

1. **crawly_db wird geleert** - Alte Daten werden gelöscht
2. **Produkte werden transferiert**:
   - Nur Produkte mit valid SKU + Price
   - Duplikate werden gefiltert
   - NULL-Werte werden korrigiert
3. **Metadaten werden kopiert** - ScraperRun-Informationen
4. **Datenbank ist ready** - API kann abfragen

## 🔍 Fehler beheben

### Problem: "CRITICAL ISSUES - Sync aborted"

**Lösung:** crawly_lidl_db direkt reparieren:

```sql
-- Produkte ohne Preis löschen
DELETE FROM crawly_lidl_db.products WHERE price IS NULL OR price <= 0;

-- Produkte ohne SKU löschen
DELETE FROM crawly_lidl_db.products WHERE sku IS NULL OR sku = '';

-- Duplikate bereinigen (letzte Version behalten)
DELETE p1 FROM crawly_lidl_db.products p1
INNER JOIN crawly_lidl_db.products p2
WHERE p1.id > p2.id AND p1.sku = p2.sku;
```

Dann nochmal `sync_and_validate.py` starten.

## 📈 Nächste Schritte

- [ ] Amazon-Scraper hinzufügen → `crawly_amazon_db`
- [ ] eBay-Scraper hinzufügen → `crawly_ebay_db`
- [ ] Aggregations-Script erweitern für mehrere Quellen
- [ ] API-Endpoints für Quellen-Filter hinzufügen

---

**Hinweis:** Dieses Script ist Teil des Crawly-Datenmanagement-Systems. Es sollte nach jedem Scraper-Lauf ausgeführt werden, um Datenintegrität zu gewährleisten.
