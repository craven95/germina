import json
import os
import uuid
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

import jsonschema
import pandas as pd
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from werkzeug.datastructures import MultiDict

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, resources={r"/submit": {"origins": "*"}})

QID = os.environ.get('Q_ID')
BASE_STORAGE = Path("/app/data") / QID
ALLOWED_EXTENSIONS = {
    'png',
    'jpg',
    'jpeg',
    'gif',
    'pdf',
    'docx',
    'xlsx',
    'txt',
    'csv',
    'json',
}

with open('schema.json') as f:
    SCHEMA = json.load(f)

with open('ui_schema.json') as f:
    UI_SCHEMA = json.load(f)


def get_file_fields(schema):
    """Identifie les champs de fichier dans le schéma"""
    return [
        key
        for key, prop in schema['properties'].items()
        if prop.get('format') == 'data-url'
    ]


def generate_anonymous_code():
    """Génère un code anonyme unique"""
    return str(uuid.uuid4())[:8]


def save_uploaded_files(field_name, files, code):
    """Sauvegarde les fichiers selon la structure spécifiée"""
    field_dir = BASE_STORAGE / field_name / code
    field_dir.mkdir(parents=True, exist_ok=True)

    saved_files = []
    for idx, file in enumerate(files):
        if file.filename == '':
            continue

        ext = Path(file.filename).suffix.lower()
        if ext[1:] not in ALLOWED_EXTENSIONS:
            continue

        filename = f"{field_name}_{code}_{idx + 1}{ext}"
        filepath = field_dir / filename
        file.save(filepath)
        saved_files.append(str(filepath.relative_to(BASE_STORAGE)))

    return saved_files


def parse_form_data(form_data: MultiDict, json_schema: dict) -> dict:
    """
    Parse les données d'un formulaire (MultiDict) selon un schéma JSON.
    Retourne un dict prêt à être inséré dans un Excel.
    """
    parsed = OrderedDict()

    for field, field_schema in json_schema.get("properties", {}).items():
        raw_value = form_data.get(field)
        field_type = field_schema.get("type")

        if raw_value is None:
            parsed[field] = None
            continue

        try:
            if field_type == "string":
                if field_schema.get("format") == "date":
                    parsed[field] = str(datetime.strptime(raw_value, "%Y-%m-%d").date())
                else:
                    parsed[field] = str(raw_value)

            elif field_type == "number":
                parsed[field] = float(raw_value.replace(",", "."))

            elif field_type == "integer":
                parsed[field] = int(raw_value)

            elif field_type == "boolean":
                parsed[field] = raw_value.lower() in ("true", "1", "yes", "on")

            elif field_type == "array":
                parsed[field] = form_data.getlist(field)

            else:
                parsed[field] = raw_value

        except Exception:
            parsed[field] = raw_value

    return parsed


@app.route('/')
def form():
    return render_template(
        'form.html',
        survey_schemas=json.dumps({"schema": SCHEMA, "ui_schema": UI_SCHEMA}),
    )


@app.route('/submit', methods=['POST'])
def submit():
    try:
        entry_id = generate_anonymous_code()
        data = request.form.copy()
        file_fields = get_file_fields(SCHEMA)
        for field in file_fields:
            field_dir = BASE_STORAGE / field
            field_dir.mkdir(parents=True, exist_ok=True)
            files = request.files.getlist(field)
            if files and files[0].filename != '':
                saved_paths = save_uploaded_files(field, files, entry_id)
                data[field] = json.dumps(saved_paths)
            else:
                data[field] = None

        jsonschema.validate(data, SCHEMA)

        parsed_data = parse_form_data(request.form, SCHEMA)
        df = pd.DataFrame([parsed_data])

        df['entry_id'] = entry_id
        df['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        excel_path = BASE_STORAGE / f"{QID}.xlsx"
        if excel_path.exists():
            existing_df = pd.read_excel(excel_path)
            df = pd.concat([existing_df, df], ignore_index=True)

        df.to_excel(excel_path, index=False)

        session['success_message'] = f"Entrée {entry_id} enregistrée !"
        return jsonify({"status": "ok", "entry_id": entry_id})

    except jsonschema.ValidationError as e:
        return (
            jsonify(status="error", errors={'.'.join(e.path) or "_global": e.message}),
            400,
        )

    except Exception as e:
        return (
            jsonify(status="error", errors={"_global": f"Erreur serveur: {str(e)}"}),
            500,
        )


if __name__ == '__main__':
    BASE_STORAGE.mkdir(parents=True, exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
