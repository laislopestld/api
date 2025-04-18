from langchain_anthropic import ChatAnthropic
from browser_use import Agent
from dotenv import load_dotenv
import asyncio
import nest_asyncio

# Aplica o nest_asyncio
nest_asyncio.apply()

# Carrega variáveis de ambiente
load_dotenv()

# Inicializa o modelo
llm = ChatAnthropic(
    model_name="claude-3-5-sonnet-20240620",
    temperature=0.0,
    timeout=100,  # Increase for complex tasks
)

async def run_agent():
    # Cria o agente com o modelo
    agent = Agent(
        task="Compare the price of gpt-4o and DeepSeek-V3",
        llm=llm,
    )
    
    try:
        # Executa o agente
        result = await agent.run()
        print(result)
        return result
    except Exception as e:
        print(f"Erro ao executar o agente: {e}")
        return str(e)

# Executa o código principal
if __name__ == "__main__":
    asyncio.run(run_agent())