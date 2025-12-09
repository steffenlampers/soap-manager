import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash
from extensions import db
from models import Soap, Ingredient, WikiEntry

app = Flask(__name__)
app.secret_key = 'super_secret_key_soap_manager'

basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'soap.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

# --- HELPER: WISSENSCHAFTLICHE BERECHNUNG ---
def calculate_science(entries, amounts):
    """Berechnet Fettsäureprofil basierend auf den JSON-Daten der Einträge"""
    total_amount = sum(amounts.values())
    if total_amount == 0: return None

    total_fatty = {'lauric':0,'myristic':0,'palmitic':0,'stearic':0,'ricinoleic':0,'oleic':0,'linoleic':0,'linolenic':0}
    total_iodine = 0

    for entry in entries:
        data = entry.get_data()
        pct = amounts[entry.id] / total_amount
        
        iodine = data.get('iodine', 0)
        total_iodine += iodine * pct
        
        acids = data.get('fatty_acids', {})
        for k, v in acids.items():
            if k in total_fatty: total_fatty[k] += v * pct

    return {
        'iodine': round(total_iodine, 1),
        'hardness': round(sum([total_fatty[x] for x in ['lauric','myristic','palmitic','stearic']]), 1),
        'cleansing': round(sum([total_fatty[x] for x in ['lauric','myristic']]), 1),
        'conditioning': round(sum([total_fatty[x] for x in ['oleic','linoleic','linolenic','ricinoleic']]), 1),
        'bubbly': round(sum([total_fatty[x] for x in ['lauric','myristic','ricinoleic']]), 1),
        'creamy': round(sum([total_fatty[x] for x in ['palmitic','stearic','ricinoleic']]), 1),
        'fatty_acids': {k: round(v,1) for k,v in total_fatty.items() if v > 0}
    }

# --- ROUTES ---

@app.route('/')
def home():
    stats = {}
    try:
        stats['wiki'] = WikiEntry.query.count()
        stats['soaps'] = Soap.query.count()
    except: pass
    return render_template('index.html', stats=stats)

# --- WIKI ---
@app.route('/wiki')
def wiki():
    cats = [c[0] for c in db.session.query(WikiEntry.category).distinct().all() if c[0]]
    cats.sort()
    return render_template('wiki_index.html', categories=cats)

@app.route('/wiki/category/<path:cat>')
def wiki_category(cat):
    entries = WikiEntry.query.filter_by(category=cat).order_by(WikiEntry.name).all()
    return render_template('wiki_list.html', category=cat, entries=entries)

@app.route('/wiki/entry/<int:id>')
def wiki_detail(id):
    entry = WikiEntry.query.get_or_404(id)
    return render_template('wiki_detail.html', entry=entry, data=entry.get_data())

# --- RECHNER ---
@app.route('/calculator', methods=['GET', 'POST'])
def calculator():
    all_entries = WikiEntry.query.order_by(WikiEntry.category, WikiEntry.name).all()
    # Filter: Nur Einträge anzeigen, die SAP Werte haben (Öle)
    oil_options = [e for e in all_entries if 'sap_naoh' in e.get_data()]
    
    result = None
    if request.method == 'POST':
        try:
            entry_id = int(request.form.get('oil_id'))
            amount = float(request.form.get('amount'))
            superfat = float(request.form.get('superfat'))
            
            sel = WikiEntry.query.get(entry_id)
            data = sel.get_data()
            
            sap = data.get('sap_naoh', 0.134)
            naoh = (amount * sap) * (1 - (superfat/100))
            
            science = calculate_science([sel], {sel.id: amount})
            
            result = {
                'oil': sel.name, 'amount': amount, 'naoh': round(naoh, 2),
                'water': round(amount*0.33, 2), 'superfat': superfat,
                'science': science
            }
        except Exception as e: flash(f"Fehler: {e}")
            
    return render_template('calculator.html', oils=oil_options, result=result)

# --- ADMIN BEREICH (Korrigiert) ---
@app.route('/admin')
def admin():
    wiki_count = WikiEntry.query.count()
    soap_count = Soap.query.count()
    return render_template('admin.html', wiki_count=wiki_count, soap_count=soap_count)

@app.route('/admin/import', methods=['POST'])
def admin_import():
    file = request.files.get('file')
    if file:
        try:
            items = json.load(file)
            c_new = 0
            c_upd = 0
            for item in items:
                entry = WikiEntry.query.filter_by(name=item.get('name') or item.get('title')).first()
                if not entry:
                    entry = WikiEntry(name=item.get('name') or item.get('title'))
                    db.session.add(entry)
                    c_new += 1
                else:
                    c_upd += 1
                
                entry.category = item.get('category', 'Allgemein')
                entry.inci = item.get('inci', '')
                entry.content = item.get('content') or item.get('description', '')
                
                tech_data = {}
                tech_keys = ['sap_naoh', 'sap_koh', 'iodine', 'ins', 'fatty_acids', 
                             'hardness', 'cleansing', 'conditioning', 'bubbly', 'creamy',
                             'neutralization_factor', 'usage_rate', 'ph_value']
                
                for key in tech_keys:
                    if key in item:
                        tech_data[key] = item[key]
                
                entry.data_json = json.dumps(tech_data)
            
            db.session.commit()
            flash(f'Import erfolgreich: {c_new} neu, {c_upd} aktualisiert.', 'success')
        except Exception as e: flash(f'Import Fehler: {e}', 'danger')
    return redirect(url_for('admin'))

@app.route('/admin/reset_db')
def admin_reset_db():
    db.session.query(WikiEntry).delete()
    db.session.commit()
    return redirect(url_for('admin'))

# --- STANDARD ROUTEN ---
@app.route('/recipes')
def recipes(): return render_template('recipes.html', soaps=Soap.query.all())
@app.route('/inventory')
def inventory(): return render_template('inventory.html', items=Ingredient.query.all())

# --- INITIALISIERUNG ---
with app.app_context(): db.create_all()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)