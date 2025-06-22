""" """

from flask import request, jsonify
from werkzeug.utils import secure_filename
import os
import tempfile
from app.routes.logistica import logistica_bp
from app.services.logistica import Logistica


@logistica_bp.route('/upload_csv', methods=['POST'])
def upload_csv():
    """
    Recibe un archivo CSV y lo procesa utilizando la función csv_to_user_dict de la clase Logistica

    El archivo CSV debe enviarse como un FormData con el campo 'file'
    Opcionalmente se puede especificar el campo que se usará como clave para cada usuario con el parámetro 'user_key_field'

    Returns:
        dict: Diccionario con los datos de usuarios procesados del CSV
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No se envió ningún archivo'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'error': 'No se seleccionó ningún archivo'}), 400
        if not file.filename.endswith('.csv'):
            return jsonify({'error': 'El archivo debe ser un CSV'}), 400

        user_key_field = request.form.get('user_key_field', 'email')

        temp_dir = tempfile.gettempdir()
        filename = secure_filename(file.filename)
        filepath = os.path.join(temp_dir, filename)
        file.save(filepath)

        logistica = Logistica()
        user_dict = logistica.csv_to_user_dict(filepath, user_key_field)

        os.remove(filepath)

        logistica.create_optimized_routes(user_dict)

        return jsonify({
            'success': True,
            'message': f'Archivo CSV procesado correctamente: {len(user_dict)} usuarios',
            'users': user_dict,
            "data": user_dict
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500
