# --- ADMIN BEREICH ---
@app.route('/admin')
def admin():
    # Wir müssen die Zahlen übergeben, sonst bleibt das Dashboard leer!
    wiki_count = WikiEntry.query.count()
    soap_count = Soap.query.count()
    return render_template('admin.html', wiki_count=wiki_count, soap_count=soap_count)

@app.route('/admin/import', methods=['POST'])
def admin_import():
    # ... (Der Rest der Import-Funktion bleibt gleich, der war korrekt)
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