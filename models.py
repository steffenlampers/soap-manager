from datetime import datetime
from extensions import db

# Tabelle für fertige Seifen (Rezepte)
class Soap(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    batch_number = db.Column(db.String(50))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text) # Notizen zum Rezept

# Tabelle für das Lager (Rohstoffe)
class Ingredient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, default=0.0) # Menge in Gramm
    unit = db.Column(db.String(10), default='g') # Einheit (g, ml)

    def __repr__(self):
        return f'<Ingredient {self.name}>'