import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from extensions import db
from models import Soap, Ingredient, OilProfile

app = Flask(__name__)
app.secret_key = 'super_secret_key_soap_manager'

# --- CONFIG ---
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'soap.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- ROUTES: PUBLIC ---

@app.route('/')
def home():
    stats = {'soaps': 0, 'inventory': 0, 'knowledge': 0}
    try:
        stats['soaps'] = Soap.query.count()
        stats['inventory'] = Ingredient.query.count()
        stats['knowledge'] = OilProfile.query.count()
    except:
        pass
    return render_template('index.html', stats=stats)

@app.route('/wiki')
def wiki():
    oils = OilProfile.query.order_by(OilProfile.name).all()
    return render_template('wiki.html', oils=oils)

@app.route('/wiki/<int:id>')
def wiki_detail(id):
    oil = OilProfile.query.get_or_404(id)
    return render_template('wiki_detail.html', oil=oil)

# --- ROUTES: ADMIN ---

@app.route('/admin')
def admin():
    oil_count = OilProfile.query.count()
    soap_count = Soap.query.count()
    return render_template('admin.html', oil_count=oil_count, soap_count=soap_count)

@app.route('/admin/import', methods=['POST'])
def admin_import():
    file = request.files.get('file')
    if file:
        try:
            data = json.load(file)
            count_new = 0
            count_updated = 0
            
            for item in data:
                # --- DUPLIKAT-CHECK ---
                # Wir suchen nach dem Namen in der Datenbank
                oil = OilProfile.query.filter_by(name=item['name']).first()
                
                if not oil:
                    # Nicht gefunden -> Wir erstellen einen neuen Eintrag
                    oil = OilProfile(name=item['name'])
                    db.session.add(oil)
                    count_new += 1
                else:
                    # Gefunden -> Wir aktualisieren den bestehenden Eintrag
                    count_updated += 1
                
                # Hier schreiben wir die Daten (passiert bei NEU und UPDATE)
                oil.inci = item.get('inci', '')
                oil.description = item.get('description', '')
                oil.sap_naoh = float(item.get('sap_naoh', 0))
                oil.iodine = int(item.get('iodine', 0))
                oil.ins = int(item.get('ins', 0))
                oil.hardness = int(item.get('hardness', 0))
                oil.cleansing = int(item.get('cleansing', 0))
                oil.conditioning = int(item.get('conditioning', 0))
                oil.bubbly = int(item.get('bubbly', 0))
                oil.creamy = int(item.get('creamy', 0))
            
            db.session.commit()
            flash(f'Import erfolgreich! {count_new} neu angelegt, {count_updated} aktualisiert.', 'success')
        except Exception as e:
            flash(f'Fehler beim Import: {e}', 'danger')
    return redirect(url_for('admin'))

@app.route('/admin/export')
def admin_export():
    oils = OilProfile.query.all()
    data = []
    for oil in oils:
        data.append({
            'name': oil.name, 'inci': oil.inci, 'description': oil.description,
            'sap_naoh': oil.sap_naoh, 'iodine': oil.iodine, 'ins': oil.ins,
            'hardness': oil.hardness, 'cleansing': oil.cleansing,
            'conditioning': oil.conditioning, 'bubbly': oil.bubbly, 'creamy': oil.creamy
        })
    return jsonify(data)

@app.route('/admin/reset_db')
def admin_reset_db():
    # Löscht nur die Öle, nicht die Rezepte!
    db.session.query(OilProfile).delete()
    db.session.commit()
    seed_database()
    flash('Wissensdatenbank wurde geleert und zurückgesetzt!', 'warning')
    return redirect(url_for('admin'))

# --- EDITOREN (Manuell) ---
@app.route('/admin/oil/new', methods=['GET', 'POST'])
def admin_oil_new():
    if request.method == 'POST': return save_oil_profile(None, request.form)
    return render_template('wiki_form.html', oil=None)

@app.route('/admin/oil/edit/<int:id>', methods=['GET', 'POST'])
def admin_oil_edit(id):
    oil = OilProfile.query.get_or_404(id)
    if request.method == 'POST': return save_oil_profile(oil, request.form)
    return render_template('wiki_form.html', oil=oil)

def save_oil_profile(oil, form):
    try:
        if not oil:
            oil = OilProfile()
            db.session.add(oil)
        oil.name = form.get('name')
        oil.inci = form.get('inci')
        oil.description = form.get('description')
        oil.sap_naoh = float(form.get('sap_naoh'))
        oil.iodine = int(form.get('iodine'))
        oil.ins = int(form.get('ins'))
        oil.hardness = int(form.get('hardness'))
        oil.cleansing = int(form.get('cleansing'))
        oil.conditioning = int(form.get('conditioning'))
        oil.bubbly = int(form.get('bubbly'))
        oil.creamy = int(form.get('creamy'))
        db.session.commit()
        flash('Gespeichert.', 'success')
        return redirect(url_for('wiki'))
    except Exception as e:
        flash(f'Fehler: {e}', 'danger')
        return redirect(url_for('admin'))

# --- RECHNER & APPS ---
@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    available_oils = OilProfile.query.order_by(OilProfile.name).all()
    result = None
    if request.method == 'POST':
        try:
            oil_id = int(request.form.get('oil_id'))
            amount = float(request.form.get('amount'))
            superfat = float(request.form.get('superfat'))
            sel = OilProfile.query.get(oil_id)
            
            # Berechnungslogik
            naoh_pure = amount * sel.sap_naoh
            discount = naoh_pure * (superfat/100)
            final_naoh = naoh_pure - discount
            
            result = {
                'oil': sel.name, 'amount': amount, 'naoh': round(final_naoh, 2),
                'water': round(amount*0.33, 2), 'superfat': superfat,
                'properties': {'Härte': sel.hardness, 'Pflege': sel.conditioning, 'Reinigung': sel.cleansing}
            }
        except: flash("Fehler bei der Berechnung")
    return render_template('calculator.html', oils=available_oils, result=result)

@app.route('/recipes')
def recipes(): return render_template('recipes.html', soaps=Soap.query.all())
@app.route('/inventory')
def inventory(): return render_template('inventory.html', items=Ingredient.query.all())

def seed_database():
    # Legt nur an, wenn wirklich gar nichts da ist
    if OilProfile.query.first() is None:
        db.session.add(OilProfile(name="Olivenöl", inci="Olea Europaea", sap_naoh=0.134, hardness=17, conditioning=83, description="Basis-Startwert."))
        db.session.commit()

with app.app_context():
    db.create_all()
    seed_database()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)