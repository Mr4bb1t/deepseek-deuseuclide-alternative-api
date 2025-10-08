from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
import json
import os

app = Flask(__name__)
CORS(app)

# Caminho para o arquivo de configuração
CONFIG_FILE = 'config.json'



script_dir = os.path.dirname(os.path.abspath(__file__))
CONTEXTO_FILE = os.path.join(script_dir, "contexto.txt")

def carregar_api_key():
    """Carrega a API Key do arquivo de configuração"""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('api_key', '').strip()
        return ''
    except Exception as e:
        print(f"Erro ao carregar API Key: {e}")
        return ''

def salvar_api_key(api_key):
    """Salva a API Key no arquivo de configuração"""
    try:
        config = {'api_key': api_key}
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=4)
        return True
    except Exception as e:
        print(f"Erro ao salvar API Key: {e}")
        return False

def carregar_contexto(caminho_arquivo):
    """Carrega o contexto do arquivo"""
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as file:
            return file.read().strip()
    except FileNotFoundError:
        return "Você é um assistente útil."

def criar_cliente():
    """Cria e retorna um cliente OpenAI com a API Key atual"""
    api_key = carregar_api_key()
    if not api_key:
        return None
    try:
        return OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
    except Exception as e:
        print(f"Erro ao criar cliente: {e}")
        return None

# Carrega o contexto uma vez ao iniciar o servidor
contexto = carregar_contexto(CONTEXTO_FILE)

@app.route("/check_api_key", methods=["GET"])
def check_api_key():
    """Verifica se existe uma API Key configurada"""
    api_key = carregar_api_key()
    return jsonify({
        "configured": bool(api_key),
        "message": "API Key configurada" if api_key else "API Key não configurada"
    })

@app.route("/save_api_key", methods=["POST"])
def save_api_key():
    """Salva a API Key fornecida pelo usuário"""
    data = request.json
    api_key = data.get("api_key", "").strip()
    
    if not api_key:
        return jsonify({"error": "API Key não fornecida"}), 400
    
    # Valida formato básico da API Key (começa com sk-)
    if not api_key.startswith("sk-"):
        return jsonify({"error": "Formato de API Key inválido"}), 400
    
    # Testa a API Key antes de salvar
    try:
        test_client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
        test_response = test_client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": "test"}],
            max_tokens=10
        )
        # Se chegou aqui, a API Key é válida
    except Exception as e:
        return jsonify({"error": f"API Key inválida: {str(e)}"}), 400
    
    # Salva a API Key
    if salvar_api_key(api_key):
        return jsonify({
            "success": True,
            "message": "API Key salva com sucesso"
        })
    else:
        return jsonify({"error": "Erro ao salvar API Key"}), 500

@app.route("/chat", methods=["POST"])
def chat():
    """Endpoint principal para chat"""
    # Verifica se existe API Key configurada
    client = criar_cliente()
    if not client:
        return jsonify({
            "error": "API Key não configurada. Por favor, configure primeiro."
        }), 401
    
    data = request.json
    user_text = data.get("message", "")
    
    if not user_text:
        return jsonify({"error": "Mensagem vazia"}), 400

    # Prepara as mensagens com o contexto carregado
    messages = [
        {"role": "system", "content": contexto},
        {"role": "user", "content": user_text}
    ]

    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=2000
        )
        reply = response.choices[0].message.content
        return jsonify({"reply": reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/reset_context", methods=["POST"])
def reset_context():
    """Reinicia o contexto carregando novamente do arquivo"""
    global contexto
    contexto = carregar_contexto(CONTEXTO_FILE)
    return jsonify({
        "status": "success",
        "message": "Contexto reiniciado"
    })

@app.route("/delete_api_key", methods=["POST"])
def delete_api_key():
    """Remove a API Key configurada"""
    try:
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        return jsonify({
            "success": True,
            "message": "API Key removida com sucesso"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("=" * 50)
    print("🚀 Servidor Flask iniciado!")
    print("=" * 50)
    
    # Verifica se existe API Key configurada
    api_key = carregar_api_key()
    if api_key:
        print("✓ API Key encontrada!")
        print(f"✓ API Key: {api_key[:10]}...{api_key[-4:]}")
    else:
        print("⚠ Nenhuma API Key configurada")
        print("📝 Acesse a tela de configuração para adicionar sua API Key")
    
    print("=" * 50)
    print(f"🌐 Servidor rodando em: http://127.0.0.1:5000")
    print("=" * 50)
    
    app.run(port=5000, debug=True)
