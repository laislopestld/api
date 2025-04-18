from langchain_anthropic import ChatAnthropic
from browser_use import Agent
from dotenv import load_dotenv
import asyncio
import nest_asyncio
import json
import time
import random
import os
import requests

# Aplica o nest_asyncio
nest_asyncio.apply()

# Carrega variáveis de ambiente
load_dotenv()

# Verifica se a API key existe
if not os.getenv("ANTHROPIC_API_KEY"):
    raise ValueError("ANTHROPIC_API_KEY não encontrada no arquivo .env")

# Inicializa o modelo com Claude 3 Haiku (modelo mais econômico)
# Custa apenas $0.25 por milhão de tokens de entrada e $1.25 por milhão de tokens de saída
llm = ChatAnthropic(
    model_name="claude-3-haiku-20240307",  # Usando o modelo mais econômico
    temperature=0.0,
    timeout=300,  # Aumentado para tarefas complexas de scraping
)

async def scrape_product_info(product_name, stores=None):
    if stores is None:
        stores = ["Amazon", "Mercado Livre", "Magazine Luiza", "Bemol"]
    
    stores_str = ", ".join(stores)
    
    # Simplificando a instrução para reduzir tokens
    task = f"""
    Busque o produto '{product_name}' nas lojas {stores_str}.
    Para cada loja, extraia: título do produto, preço atual e URL da página.
    Retorne os dados em formato JSON com a loja como chave e título, preço e URL como valores.
    """
    
    agent = Agent(
        task=task,
        llm=llm,
    )
    
    try:
        result = await agent.run()
        # Tentar parsear como JSON, se possível
        try:
            parsed_result = json.loads(result)
            return parsed_result
        except:
            return result
    except Exception as e:
        print(f"Erro ao executar o agente para '{product_name}': {e}")
        return {"error": str(e)}

async def main():
    products = [
        "smartphone samsung galaxy s23",
        "notebook dell inspiron",
        "smart tv 50 polegadas",
        "Geladeira Consul Frost Free Duplex 340 litros Branca CRM39ABA",
        "Máquina De Lavar Consul 9kg Lavagem Econômica Branca CWB09BB",
        "Fritadeira Elétrica Air Fryer Elgin 5L Space 127V AFC50"
    ]
    
    results = {}
    
    # Arquivo para salvar resultados parciais em caso de falha
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
            # Adiciona um delay variável para evitar atingir rate limits
            wait_time = random.uniform(30, 60)  # 30-60 segundos com o modelo mais eficiente
            print(f"Aguardando {wait_time:.1f} segundos antes da próxima requisição...")
            time.sleep(wait_time)
            
            product_data = await scrape_product_info(product)
            # Adiciona timestamp
            product_data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
            results[product] = product_data
            
            # Salva resultados parciais após cada produto
            with open(partial_results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
                
            print(f"Concluído: {product} (Resultados parciais salvos)\n")
        
        except Exception as e:
            print(f"Erro crítico ao processar '{product}': {e}")
            print("Salvando resultados parciais e continuando com o próximo produto...")
            
            results[product] = {"error": str(e), "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
            
            # Salva resultados parciais em caso de erro
            with open(partial_results_file, "w", encoding="utf-8") as f:
                json.dump(results, f, ensure_ascii=False, indent=2)
            
            # Espera um pouco mais em caso de erro (especialmente para rate limits)
            if "rate limit" in str(e).lower():
                wait_time = 90  # 90 segundos em caso de erro de limite de taxa
                print(f"Erro de rate limit detectado. Aguardando {wait_time} segundos...")
                time.sleep(wait_time)
    
    # Salva resultados finais em um arquivo JSON
    with open("product_prices.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Relatório completo salvo em 'product_prices.json'")
    
    # Envia para a API (se configurada)
    try:
        api_url = "http://localhost:5000/prices"  # URL da sua API Flask
        response = requests.post(api_url, json=results)
        print(f"Dados enviados para API. Status: {response.status_code}")
    except Exception as e:
        print(f"Erro ao enviar para API: {e}")
    
    # Remove arquivo de resultados parciais
    if os.path.exists(partial_results_file):
        os.remove(partial_results_file)
        print("Arquivo de resultados parciais removido.")

if __name__ == "__main__":
    try:
        nest_asyncio.apply()
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperação interrompida pelo usuário. Os resultados parciais estão salvos.")
    except Exception as e:
        print(f"\nErro não tratado: {e}")
        print("Os resultados parciais estão salvos no arquivo 'product_prices_partial.json'")