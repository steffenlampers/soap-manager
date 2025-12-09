from datetime import datetime
from extensions import db

# --- REZEPTE & LAGER (Bestand) ---
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

# --- WISSENSDATENBANK (Neu & Erweitert) ---
class OilProfile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False) # unique=True verhindert doppelte Namen auf DB-Ebene
    inci = db.Column(db.String(150)) # Internationale Bezeichnung
    description = db.Column(db.Text)
    
    # Chemische Werte
    sap_naoh = db.Column(db.Float, nullable=False)
    iodine = db.Column(db.Integer, default=0)
    ins = db.Column(db.Integer, default=0)

    # Eigenschaften (0-100)
    hardness = db.Column(db.Integer, default=0)
    cleansing = db.Column(db.Integer, default=0)
    conditioning = db.Column(db.Integer, default=0)
    bubbly = db.Column(db.Integer, default=0)
    creamy = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f'<OilProfile {self.name}>'