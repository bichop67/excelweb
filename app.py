from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import openai
import pandas as pd
import os
from dotenv import load_dotenv
import io
import json
import logging

# Configuration du logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')
if not openai.api_key:
    logger.error("Clé API OpenAI non trouvée!")

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

        # Appel à GPT-4
        try:
            response = openai.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": """Tu es un expert en création de tableaux Excel. 
                     Génère uniquement un tableau de données au format JSON.
                     Format attendu: [{"colonne1": "valeur1", "colonne2": "valeur2"}, {...}]"""},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7
            )
            logger.info("Réponse GPT-4 reçue")
        except Exception as e:
            logger.error(f"Erreur OpenAI: {str(e)}")
            return jsonify({"error": f"Erreur lors de l'appel à OpenAI: {str(e)}"}), 500

        # Conversion de la réponse JSON en DataFrame
        try:
            data = response.choices[0].message.content
            logger.info(f"Données brutes: {data}")
            
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
