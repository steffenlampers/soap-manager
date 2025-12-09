import json
from datetime import datetime
from extensions import db

# --- REZEPTE & LAGER (Bleiben, da dies Bewegungsdaten sind) ---
class Soap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    batch_number = db.Column(db.String(50))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text)

class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, default=0.0)
    unit = db.Column(db.String(10), default='g')

# --- DIE UNIVERSELLE WISSENSDATENBANK ---
class WikiEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    # Standard-Felder, die JEDER Eintrag hat
    name = db.Column(db.String(100), unique=True, nullable=False) # Titel / Name
    category = db.Column(db.String(50), default='Allgemein')       # Kategorie (Basisöle, Zusätze, Theorie...)
    inci = db.Column(db.String(150))                               # INCI (optional)
    content = db.Column(db.Text)                                   # Der Beschreibungstext (HTML erlaubt)
    
    # DAS MAGIC FIELD: Hier speichern wir alle technischen Daten flexibel
    # Für Öle: {"sap_naoh": 0.134, "fatty_acids": {...}}
    # Für Säure: {"neutralization_factor": 0.571}
    # Für Theorie: {}
    data_json = db.Column(db.Text, default='{}')

    def get_data(self):
        """Hilfsfunktion, um das JSON Feld als echtes Python-Objekt zu bekommen"""
        try:
            return json.loads(self.data_json)
        except:
            return {}

    def __repr__(self):
        return f'<WikiEntry {self.name}>'