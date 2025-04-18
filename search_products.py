from langchain_anthropic import ChatAnthropic
from browser_use import Agent
from dotenv import load_dotenv
import asyncio
import nest_asyncio
import json

# Aplica o nest_asyncio
nest_asyncio.apply()

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa o modelo
llm = ChatAnthropic(
    model_name="claude-3-5-sonnet-20240620",
    temperature=0.0,
    timeout=300,  # Aumentado para tarefas complexas de scraping
)

async def scrape_product_info(product_name, stores=None):
    if stores is None:
        stores = ["Amazon", "Mercado Livre", "Magazine Luiza"]
    
    stores_str = ", ".join(stores)
    
    task = f"""
    Search for '{product_name}' on {stores_str}.
    For each store, extract:
    1. Product title
    2. Current price
    3. URL of the product page
    
    Return the data in a structured JSON format with store name as the key and an object with title, price, and url as values.
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
        "smart tv 50 polegadas"
    ]
    
    results = {}
    
    for product in products:
        print(f"Buscando informações para: {product}")
        product_data = await scrape_product_info(product)
        results[product] = product_data
        print(f"Concluído: {product}\n")
    
    # Salvar resultados em um arquivo JSON que o n8n pode consumir
    with open("product_prices.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print("Relatório completo salvo em 'product_prices.json'")

if __name__ == "__main__":
    nest_asyncio.apply()
    asyncio.run(main())