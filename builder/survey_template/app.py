import json
import os
import uuid
from collections import OrderedDict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import jsonschema
import pandas as pd
from flask import Flask, jsonify, render_template, request, session
from flask_cors import CORS
from werkzeug.datastructures import MultiDict

# Configuration
QID: str = os.environ.get('Q_ID', '')
if not QID:
    raise EnvironmentError("Environment variable Q_ID must be set")
BASE_STORAGE: Path = Path("/app/data") / QID
ALLOWED_EXTENSIONS: set[str] = {
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

SCHEMA: Dict[str, Any]
UI_SCHEMA: Dict[str, Any]
with open('schema.json', 'r') as f:
    SCHEMA = json.load(f)
with open('ui_schema.json', 'r') as f:
    UI_SCHEMA = json.load(f)

JSONType = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
ParsedData = Dict[str, JSONType]

app = Flask(__name__)
app.secret_key = os.urandom(24)
CORS(app, resources={r"/submit": {"origins": "*"}})


def parse_form_data(form_data: MultiDict[str, Any], json_schema: Dict[str, Any]) -> ParsedData:
    """
    Parse les données d'un formulaire (MultiDict) selon un schéma JSON.
    Retourne un dict prêt à être inséré dans un Excel.

    Args:
        form_data (MultiDict): Les données du formulaire à parser.
        json_schema (dict): Le schéma JSON décrivant la structure des données.
    Returns:
        dict: Un dictionnaire avec les données du formulaire converties selon le schéma.
    """
    parsed: OrderedDict[str, JSONType] = OrderedDict()

    for field, field_schema in json_schema.get("properties", {}).items():
        raw_value: Optional[str] = form_data.get(field)
        field_type: Optional[str] = field_schema.get("type")

        if raw_value is None:
            parsed[field] = None
            continue

        try:
            if field_type == "string":
                if field_schema.get("format") == "date":
                    parsed[field] = datetime.strptime(raw_value, "%Y-%m-%d").date().isoformat()
                else:
                    parsed[field] = raw_value

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

    return dict(parsed)


def generate_anonymous_code() -> str:
    """Génère un code anonyme unique pour chaque entrée du questionnaire"""
    return uuid.uuid4().hex[:8]


def get_file_fields(schema: Dict[str, Any]) -> List[str]:
    """Identifie les champs de fichier dans le schéma pour les traiter correctement.
    Args:
        schema (dict): Le schéma JSON du questionnaire.
    Returns:
        list: Liste des noms de champs qui sont des fichiers (data-url).
    """

    return [
        key
        for key, prop in schema.get('properties', {}).items()
        if prop.get('format') == 'data-url'
    ]


def save_uploaded_files(field_name: str, files: List[Any], entry_id: str) -> List[str]:
    """Sauvegarde les fichiers en local sur la machine du serveur.
    Crée un répertoire pour chaque champ de fichier et enregistre les fichiers avec un nom unique.

    Args:
        field_name (str): Le nom du champ de fichier.
        files (list): Liste des fichiers uploadés.
        entry_id (str): L'ID de l'entrée du questionnaire.
    Returns:
        list: Liste des chemins relatifs des fichiers sauvegardés pour ajouter dans l'Excel.
    """
    field_dir: Path = BASE_STORAGE / field_name / entry_id
    field_dir.mkdir(parents=True, exist_ok=True)

    saved_files: List[str] = []
    for idx, file in enumerate(files):
        if file.filename == '':
            continue

        ext = Path(file.filename).suffix.lower()
        if ext.lstrip('.') not in ALLOWED_EXTENSIONS:
            continue

        filename = f"{field_name}_{entry_id}_{idx + 1}{ext}"
        filepath = field_dir / filename
        file.save(filepath)
        saved_files.append(str(filepath.relative_to(BASE_STORAGE)))

    return saved_files


@app.route('/')  # type: ignore[misc]
def form() -> Any:
    return render_template(
        'form.html',
        survey_schemas=json.dumps({"schema": SCHEMA, "ui_schema": UI_SCHEMA}),
    )


@app.route('/submit', methods=['POST'])  # type: ignore[misc]
def submit() -> Any:
    try:
        entry_id: str = generate_anonymous_code()
        data: MultiDict[str, Any] = request.form.copy()
        file_fields: List[str] = get_file_fields(SCHEMA)

        for field in file_fields:
            files = request.files.getlist(field)
            if files and files[0].filename:
                saved_paths: List[str] = save_uploaded_files(field, files, entry_id)
                data[field] = json.dumps(saved_paths)
            else:
                data[field] = None

        jsonschema.validate(data, SCHEMA)

        parsed_data: ParsedData = parse_form_data(request.form, SCHEMA)
        df: pd.DataFrame = pd.DataFrame([parsed_data])

        df['entry_id'] = entry_id
        df['date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        excel_path: Path = BASE_STORAGE / f"{QID}.xlsx"
        if excel_path.exists():
            existing_df: pd.DataFrame = pd.read_excel(excel_path)
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
