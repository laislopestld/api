import anthropic
import json
import time
import random
import os
from dotenv import load_dotenv
import requests
from datetime import datetime

# Carrega variáveis de ambiente
load_dotenv()

# Verifica se a API key existe
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY não encontrada no arquivo .env")

# Inicializa o cliente Anthropic
client = anthropic.Anthropic(api_key=api_key)

def scrape_product_info(product_name, stores=None):
    if stores is None:
        stores = ["Amazon", "Mercado Livre", "Magazine Luiza"]
    
    stores_str = ", ".join(stores)
    
    # Cria a mensagem para o Claude buscar informações de preços
    prompt = f"""
    Encontre o produto '{product_name}' nas lojas online: {stores_str}.
    
    Para cada loja, forneça:
    1. O título exato do produto
    2. O preço atual
    3. A URL do produto
    
    IMPORTANTE: Retorne apenas no formato JSON a seguir, sem explicações adicionais:
    
    {{
      "Amazon": {{
        "title": "título do produto",
        "price": "R$ XX,XX",
        "url": "url do produto"
      }},
      "Mercado Livre": {{
        "title": "título do produto",
        "price": "R$ XX,XX",
        "url": "url do produto"
      }},
      ...
    }}
    
    Se não encontrar em alguma loja, retorne null para essa loja.
    """
    
    try:
        # Usando o modelo Claude 3 Haiku (mais econômico)
        message = client.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=1000,
            temperature=0,
            system="Você é um assistente especializado em extrair informações de produtos de e-commerce. Retorne apenas JSON válido, sem explicações.",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        # Extrair o JSON da resposta
        response_text = message.content[0].text
        
        # Encontrar o JSON na resposta (caso haja texto explicativo)
        import re
        json_match = re.search(r'({[\s\S]*})', response_text)
        if json_match:
            json_str = json_match.group(1)
            try:
                return json.loads(json_str)
            except:
                return {"error": "Erro ao parsear JSON", "raw_response": response_text}
        else:
            try:
                return json.loads(response_text)
            except:
                return {"error": "Não foi possível extrair JSON", "raw_response": response_text}
                
    except Exception as e:
        return {"error": str(e)}

def main():
    products = [
        "smartphone samsung galaxy s23",
        "notebook dell inspiron",
        "smart tv 50 polegadas"
    ]
    
    results = {}
    
    # Arquivo para salvar resultados parciais
    partial_results_file = "product_prices_partial.json"
    
    # Carrega resultados parciais, se existirem
    if os.path.exists(partial_results_file):
        try:
            with open(partial_results_file, "r", encoding="utf-8") as f:
                results = json.load(f)
                print(f"Resultados parciais carregados. Produtos já processados: {list(results.keys())}")
        except Exception as e:
            print(f"Erro ao carregar resultados parciais: {e}")
    
    for product in products:
        # Pula produtos já processados
        if product in results:
            print(f"Produto já processado: {product}")
            continue
            
        print(f"Buscando informações para: {product}")
        
        try:
            # Adiciona um delay para evitar rate limits
            wait_time = random.uniform(15, 30)  # Reduzido ainda mais com esta abordagem
            print(f"Aguardando {wait_time:.1f} segundos antes da próxima requisição...")
            time.sleep(wait_time)
            
            product_data = scrape_product_info(product)
            
            # Adiciona timestamp à resposta
            product_data["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            results[product] = product_data
            
            # Salva resultados parciais
            with open(partial_results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            print(f"Concluído: {product} (Resultados parciais salvos)\n")
        
        except Exception as e:
            print(f"Erro crítico ao processar '{product}': {e}")
            
            results[product] = {"error": str(e)}
            
            # Salva resultados parciais em caso de erro
            with open(partial_results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # Espera em caso de erro
            if "rate limit" in str(e).lower():
                wait_time = 60
                print(f"Erro de rate limit detectado. Aguardando {wait_time} segundos...")
                time.sleep(wait_time)
    
    # Opção 1: Salva resultados em um arquivo JSON para o n8n ler
    with open("product_prices.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Relatório completo salvo em 'product_prices.json'")
    
    # Opção 2: Envia diretamente para o n8n via webhook (descomente se quiser usar)
    """
    try:
        # Substitua a URL abaixo pela URL do seu webhook no n8n
        webhook_url = "https://seu-n8n.com/webhook/seu-endpoint"
        response = requests.post(webhook_url, json=results)
        print(f"Dados enviados para n8n. Status: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar para webhook: {e}")
    """

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário. Os resultados parciais estão salvos.")
    except Exception as e:
        print(f"\nErro não tratado: {e}")
        print("Os resultados parciais estão salvos no arquivo 'product_prices_partial.json'")