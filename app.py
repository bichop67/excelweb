from flask import Flask, request, send_file, jsonify, render_template
from flask_cors import CORS
import openai
import pandas as pd
import os
from dotenv import load_dotenv
import io

load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/generate', methods=['POST'])
def generate_excel():
    try:
        prompt = request.json.get('prompt')
        
        # Appel à GPT-4
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Tu es un expert en création de tableaux Excel. Génère uniquement les données au format JSON avec les colonnes et les données."},
                {"role": "user", "content": prompt}
            ]
        )
        
        # Conversion de la réponse JSON en DataFrame
        data = response.choices[0].message.content
        try:
            json_data = eval(data)
            df = pd.DataFrame(json_data)
        except:
            return jsonify({"error": "Erreur lors de la conversion des données"}), 500
        
        # Création du fichier Excel en mémoire
        output = io.BytesIO()
        df.to_excel(output, index=False, engine='openpyxl')
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='generated_excel.xlsx'
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
