import os
from dotenv import load_dotenv
from importlib.metadata import version

load_dotenv()

core_version = version("langchain-core")
lg_version = version("langgraph")
from langchain_openai import ChatOpenAI


print(f"langchain-core version: {core_version}")
print(f"langgraph version: {lg_version}")


def main():

    # Test local Ollama (OpenAI-compatible endpoint)
    llm = ChatOpenAI(
        model=os.getenv("MODEL"),
        base_url=os.getenv("BASE_URL"),
        api_key=os.getenv("API_KEY"),
        temperature=0,
    )
    response = llm.invoke("Say 'setup complete!' in one word")
    print(f"Response from Ollama: {response}")

    print("Setup complete!")


if __name__ == "__main__":
    main()
