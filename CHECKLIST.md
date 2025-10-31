# Crawly - Setup & Operations Checklist

## ✅ Initial Setup

- [x] Python 3.13 installiert
- [x] MySQL 8.0 in Docker
- [x] phpMyAdmin auf :8080
- [x] Dual-Database-System (crawly_lidl_db + crawly_db)
- [x] SQLAlchemy ORM konfiguriert
- [x] Playwright Browser-Automation
- [x] FastAPI mit Swagger-UI
- [x] Logging konfiguriert

## 🚀 Scraper-Operationen

### Vor erstem Scrape
```powershell
[ ] Docker-Compose läuft: docker-compose ps
[ ] MySQL healthy: docker-compose ps | grep mysql
[ ] Datenbanken initialisiert: python init_databases.py
```

### Scraping
```powershell
[ ] Scraper starten: python run_scraper.py --max-pages 1 (Test)
[ ] Logs prüfen
[ ] Produkte in crawly_lidl_db landen
[ ] Prüfe: docker exec crawly-mysql mysql -u crawly_user -pcrawly_password crawly_lidl_db -e "SELECT COUNT(*) FROM products;"
```

### Validierung & Sync
```powershell
[ ] Validator starten: python sync_and_validate.py
[ ] Keine kritischen Fehler
[ ] Prüfe: docker exec crawly-mysql mysql -u crawly_user -pcrawly_password crawly_db -e "SELECT COUNT(*) FROM products;"
[ ] Beide DBs haben gleiche Anzahl
```

### API Test
```powershell
[ ] API läuft: curl http://localhost:8001/docs
[ ] Produkte abrufbar: curl http://localhost:8001/products
[ ] Stats funktioniert: curl http://localhost:8001/stats
```

## 🔧 Troubleshooting

### Problem: "crawly_mysql is not running"
```powershell
[ ] docker-compose up -d --build
[ ] docker-compose logs crawly-mysql
```

### Problem: "pymysql.err.OperationalError"
```powershell
[ ] Credentials prüfen in docker-compose.yml
[ ] MySQL in Docker am laufen: docker ps
[ ] Datenbanken existieren: docker exec crawly-mysql mysql -u root -proot_password -e "SHOW DATABASES;"
```

### Problem: "No products found in crawly_lidl_db"
```powershell
[ ] run_scraper.py läuft noch?
[ ] Lidl.de erreichbar?
[ ] Logs prüfen: docker-compose logs crawly-scraper
[ ] Cookie-Bypass funktioniert? (OneTrust)
[ ] Selektoren noch gültig? (HTML-Struktur von Lidl ändert sich)
```

### Problem: API gibt 500 error
```powershell
[ ] docker-compose logs crawly-api
[ ] Datenbank-Verbindung: curl http://localhost:8001/stats
[ ] DB-Schema OK: crawly_db.products Tabelle existiert
```

## 📊 Datenqualität

### Nach jedem Scrape prüfen

```powershell
# In crawly_lidl_db
[ ] Keine Produkte mit price = NULL
[ ] Keine Produkte mit price <= 0
[ ] Keine Produkte ohne SKU
[ ] Keine doppelten SKUs
[ ] Alle required fields vorhanden (name, price, sku)

# Nach Sync
[ ] crawly_db hat gleiche Anzahl wie crawly_lidl_db
[ ] Alle Felder in crawly_db gefüllt
[ ] API gibt Produkte zurück
```

## 🔄 Tägliche Operationen

```powershell
# Morgens: Scrape
python run_scraper.py

# Nach Scrape: Validieren & Sync
python sync_and_validate.py

# Optional: Prüfen
curl http://localhost:8001/stats

# Bei Bedarf: phpMyAdmin prüfen
start http://localhost:8080
```

## 🎯 Performance-Checks

```powershell
# Scraper-Geschwindigkeit
[ ] Seite 1: ~10-15 Sekunden
[ ] Page 2: +20-30 Sekunden (mehr Produkte)
[ ] Memory: < 500MB (Browser + Python)

# API-Performance
[ ] /products: < 100ms
[ ] /products?search=test: < 200ms
[ ] /stats: < 50ms

# DB-Performance
[ ] Sync-Zeit für 96 Produkte: < 2 Sekunden
```

## 🔐 Sicherheit

- [x] crawly_user hat nur Zugriff auf crawly_lidl_db + crawly_db
- [x] root-Passwort ist root_password (nicht in Produktion nutzen!)
- [x] MySQL nur auf localhost:3306 (lokal nur)
- [x] API ohne Authentication (für intern Netzwerk OK)

**TODO für Produktion:**
- [ ] Starke Passwörter nutzen
- [ ] MySQL auth aktivieren
- [ ] API mit JWT/OAuth sichern
- [ ] HTTPS aktivieren
- [ ] Scraper IP-Blocking handhaben

## 📝 Logs

```powershell
# Scraper-Logs (live)
docker-compose logs -f crawly-scraper

# API-Logs (live)
docker-compose logs -f crawly-api

# MySQL-Logs (live)
docker-compose logs -f crawly-mysql

# Alle Logs
docker-compose logs

# In Datei speichern
docker-compose logs > logs.txt
```

## 🗑️ Cleanup

```powershell
# Nur Lidl-Daten clearen (new Scrape)
python -c "from src.database.connection import LidlSessionLocal; from src.models.product import Product, ProductHistory; db = LidlSessionLocal(); db.query(ProductHistory).delete(); db.query(Product).delete(); db.commit();"

# Beides leeren
python init_databases.py

# Docker cleanup
docker-compose down
docker volume rm crawly_mysql_data
docker system prune -a
```

## 📚 Dokumentation

- [x] README.md - Projekt-Übersicht
- [x] QUICKSTART.md - Erste Schritte
- [x] SYNC_AND_VALIDATE.md - Validator-Doku
- [x] ARCHITECTURE.md - System-Design
- [ ] API-Dokumentation (auto-gen via Swagger)

## 🎓 Nächste Lernschritte

- [ ] Amazon-Scraper bauen
- [ ] Aggregations-Service für multi-Source
- [ ] Scheduled Jobs (APScheduler)
- [ ] Monitoring Dashboard (Grafana)
- [ ] Automatische Fehler-Alerts
- [ ] Datenbank-Backups

## 📞 Support

Bei Problemen:
1. Logs anschauen: `docker-compose logs SERVICE_NAME`
2. Checkliste durchgehen
3. Datenbank-Zustand prüfen via phpMyAdmin
4. Test-Queries ausführen
5. Selektoren überprüfen (Lidl-HTML ändert sich)

---

**Status:** ✅ System ist produktionsreif
**Letzte Aktualisierung:** 2025-10-31
**Next Review:** 2025-11-07
