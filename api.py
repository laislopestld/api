from flask import Flask, jsonify, request
from flask_cors import CORS  # Para permitir requisições de diferentes origens
import json
import os
from datetime import datetime

# Inicializa a aplicação Flask
app = Flask(__name__)
CORS(app)  # Habilita CORS para todas as rotas

# Caminho para o arquivo JSON dos preços
JSON_FILE_PATH = 'product_prices.json'

# Função auxiliar para ler o arquivo JSON
def read_prices_file():
    try:
        if os.path.exists(JSON_FILE_PATH):
            with open(JSON_FILE_PATH, 'r', encoding='utf-8') as file:
                return json.load(file)
        else:
            return {"error": "Arquivo de preços não encontrado"}
    except Exception as e:
        return {"error": f"Erro ao ler arquivo: {str(e)}"}

# Função auxiliar para salvar no arquivo JSON
def save_prices_file(data):
    try:
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as file:
            json.dump(data, file, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        return False

# Rota principal - informações sobre a API
@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "status": "online",
        "description": "API de preços de produtos em e-commerces",
        "endpoints": {
            "/prices": "Obter todos os preços",
            "/prices/produtos": "Listar nomes dos produtos",
            "/prices/{nome_produto}": "Obter preços de um produto específico"
        }
    })

# Rota para obter todos os preços
@app.route('/prices', methods=['GET'])
def get_all_prices():
    data = read_prices_file()
    return jsonify(data)

# Rota para listar os nomes dos produtos
@app.route('/prices/produtos', methods=['GET'])
def get_product_names():
    data = read_prices_file()
    if isinstance(data, dict) and "error" not in data:
        product_names = list(data.keys())
        return jsonify({"produtos": product_names})
    else:
        return jsonify(data)

# Rota para obter preços de um produto específico
@app.route('/prices/<product_name>', methods=['GET'])
def get_product_price(product_name):
    data = read_prices_file()
    if isinstance(data, dict) and "error" not in data:
        if product_name in data:
            return jsonify({product_name: data[product_name]})
        else:
            return jsonify({"error": "Produto não encontrado"}), 404
    else:
        return jsonify(data)

# Rota para atualizar preços (via POST)
@app.route('/prices', methods=['POST'])
def update_prices():
    try:
        new_data = request.json
        if not new_data:
            return jsonify({"error": "Dados JSON não fornecidos"}), 400
            
        # Adiciona timestamp
        for product in new_data:
            if "timestamp" not in new_data[product]:
                new_data[product]["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
        if save_prices_file(new_data):
            return jsonify({"message": "Dados atualizados com sucesso"}), 200
        else:
            return jsonify({"error": "Erro ao salvar dados"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Executa a aplicação se este arquivo for executado diretamente
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
