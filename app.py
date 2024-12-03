from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import requests
import pandas as pd
import os
import io
import json
import logging
import time
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Configuration API
API_KEY = "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"
API_URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

def make_api_request(prompt, max_retries=3):
    """Fonction pour faire une requête à l'API avec retry"""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Accept": "application/json"
    }
    
    data = {
        "model": "gpt-4",
        "messages": [
            {"role": "system", "content": """Tu es un expert en création de tableaux Excel. 
             Génère uniquement un tableau de données au format JSON.
             Format attendu: [{"colonne1": "valeur1", "colonne2": "valeur2"}, {...}]"""},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Tentative {attempt + 1} de connexion à l'API")
            response = requests.post(
                API_URL, 
                headers=headers, 
                json=data,
                timeout=60,
                verify=True
            )
            
            logger.debug(f"Status code: {response.status_code}")
            logger.debug(f"Response headers: {response.headers}")
            logger.debug(f"Response body: {response.text[:500]}")  # Log les premiers 500 caractères de la réponse
            
            if response.status_code == 429:  # Rate limit
                wait_time = int(response.headers.get('Retry-After', 60))
                logger.warning(f"Rate limit atteint, attente de {wait_time} secondes...")
                time.sleep(wait_time)
                continue
            elif response.status_code == 401:
                logger.error(f"Erreur d'authentification: {response.text}")
                raise Exception("Erreur d'authentification avec l'API")
                
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de requête: {str(e)}")
            if attempt == max_retries - 1:
                raise Exception(f"Erreur API après {max_retries} tentatives: {str(e)}")
            
            wait_time = min(2 ** attempt * 5, 60)  # Backoff exponentiel
            logger.warning(f"Tentative {attempt + 1}/{max_retries} échouée, nouvelle tentative dans {wait_time} secondes...")
            time.sleep(wait_time)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_excel():
    try:
        prompt = request.json.get('prompt')
        logger.info(f"Prompt reçu : {prompt}")
        
        if not prompt:
            return jsonify({"error": "Prompt manquant"}), 400

        # Appel à l'API
        try:
            response_data = make_api_request(prompt)
            logger.info("Réponse API reçue")
            data = response_data['choices'][0]['message']['content']
        except Exception as e:
            logger.error(f"Erreur API: {str(e)}")
            error_msg = str(e)
            if "rate limit" in error_msg.lower():
                return jsonify({"error": "Le service est temporairement surchargé. Veuillez réessayer dans quelques minutes."}), 429
            if "Erreur d'authentification" in error_msg:
                return jsonify({"error": "Erreur d'authentification avec l'API. Veuillez vérifier la configuration."}), 401
            return jsonify({"error": f"Erreur lors de l'appel à l'API: {error_msg}"}), 500

        # Conversion de la réponse JSON en DataFrame
        try:
            # Nettoyage et parsing des données
            data = data.strip()
            if data.startswith("```") and data.endswith("```"):
                data = data[3:-3]
            if data.startswith("json"):
                data = data[4:]
                
            json_data = json.loads(data)
            logger.info(f"Données JSON parsées: {json_data}")
            
            df = pd.DataFrame(json_data)
            logger.info(f"DataFrame créé avec les colonnes: {df.columns.tolist()}")
        except Exception as e:
            logger.error(f"Erreur parsing JSON: {str(e)}")
            return jsonify({"error": f"Erreur lors de la conversion des données: {str(e)}"}), 500

        # Création du fichier Excel en mémoire
        try:
            output = io.BytesIO()
            df.to_excel(output, index=False, engine='openpyxl')
            output.seek(0)
            logger.info("Fichier Excel généré avec succès")
            
            return send_file(
                output,
                mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                as_attachment=True,
                download_name='generated_excel.xlsx'
            )
        except Exception as e:
            logger.error(f"Erreur génération Excel: {str(e)}")
            return jsonify({"error": f"Erreur lors de la création du fichier Excel: {str(e)}"}), 500
            
    except Exception as e:
        logger.error(f"Erreur générale: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
