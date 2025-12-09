import os
from flask import Flask, render_template, request, redirect, url_for, flash
from extensions import db
from models import Soap, Ingredient

app = Flask(__name__)
app.secret_key = 'geheimschluessel_fuer_sessions' # Wichtig für Nachrichten

# --- KONFIGURATION ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'soap.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- KONSTANTEN (Vereinfachte SAP Werte für den Rechner v1.0) ---
OILS = {
    'Olivenöl': 0.134,
    'Kokosöl': 0.190,
    'Palmöl': 0.141,
    'Rapsöl': 0.124,
    'Sonnenblumenöl': 0.134,
    'Mandelöl': 0.136,
    'Rizinusöl': 0.128,
    'Sheabutter': 0.128
}

# --- ROUTEN ---

@app.route('/')
def home():
    soap_count = 0
    ingredient_count = 0
    try:
        soap_count = Soap.query.count()
        ingredient_count = Ingredient.query.count()
    except:
        pass
    return render_template('index.html', soap_count=soap_count, ingredient_count=ingredient_count)

# --- RECHNER ---
@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    result = None
    if request.method == 'POST':
        # Daten aus dem Formular holen
        oil_name = request.form.get('oil')
        amount = float(request.form.get('amount'))
        superfat = float(request.form.get('superfat'))
        
        # Berechnung (Sehr vereinfacht für v1.0 - nur ein Öl)
        sap_value = OILS.get(oil_name, 0.134)
        naoh_needed = amount * sap_value
        
        # Überfettung berechnen (Abzug vom NaOH)
        discount = naoh_needed * (superfat / 100)
        final_naoh = naoh_needed - discount
        water_amount = amount * 0.33 # Standard 33% Wasseranteil zur Ölmenge
        
        result = {
            'oil': oil_name,
            'amount': amount,
            'naoh': round(final_naoh, 2),
            'water': round(water_amount, 2),
            'superfat': superfat
        }
        
    return render_template('calculator.html', oils=OILS, result=result)

# --- REZEPTBUCH / LISTE ---
@app.route('/recipes', methods=['GET', 'POST'])
def recipes():
    if request.method == 'POST':
        # Neue Seife speichern
        name = request.form.get('name')
        batch = request.form.get('batch')
        notes = request.form.get('notes')
        new_soap = Soap(name=name, batch_number=batch, notes=notes)
        db.session.add(new_soap)
        db.session.commit()
        return redirect(url_for('recipes'))
        
    all_soaps = Soap.query.order_by(Soap.date_created.desc()).all()
    return render_template('recipes.html', soaps=all_soaps)

# --- LAGERHALTUNG ---
@app.route('/inventory', methods=['GET', 'POST'])
def inventory():
    if request.method == 'POST':
        name = request.form.get('name')
        amount = request.form.get('amount')
        
        new_item = Ingredient(name=name, amount=amount)
        db.session.add(new_item)
        db.session.commit()
        return redirect(url_for('inventory'))

    items = Ingredient.query.all()
    return render_template('inventory.html', items=items)

# --- HILFSFUNKTIONEN ---
@app.route('/delete_soap/<int:id>')
def delete_soap(id):
    soap = Soap.query.get_or_404(id)
    db.session.delete(soap)
    db.session.commit()
    return redirect(url_for('recipes'))

@app.route('/delete_ingredient/<int:id>')
def delete_ingredient(id):
    item = Ingredient.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('inventory'))

# DB Init beim Start
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)