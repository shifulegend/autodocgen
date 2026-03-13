import os
from autodocgen.config import Config
from autodocgen.generator import AIDocGenerator

def test_openrouter():
    print("Testing OpenRouter...")
    cfg = Config.load(overrides={"llm": {"provider": "openrouter", "model": "stepfun/step-3.5-flash:free"}})
    gen = AIDocGenerator(api_key=cfg.api_key, model=cfg.model, provider=cfg.provider, base_url=cfg.base_url)
    res = gen.generate_function_docs("add", ["a", "b"], "int", "Adds two numbers.")
    print(res)
    print("-" * 20)

def test_groq():
    print("Testing Groq...")
    cfg = Config.load(overrides={"llm": {"provider": "groq", "model": "llama-3.1-8b-instant"}})
    gen = AIDocGenerator(api_key=cfg.api_key, model=cfg.model, provider=cfg.provider, base_url=cfg.base_url)
    res = gen.generate_function_docs("sub", ["a", "b"], "int", "Subtracts two numbers.")
    print(res)
    print("-" * 20)

if __name__ == "__main__":
    try:
        test_openrouter()
    except Exception as e:
        print(f"OpenRouter failed: {e}")
    
    try:
        test_groq()
    except Exception as e:
        print(f"Groq failed: {e}")
