from openai import AsyncOpenAI
from langchain_openai import ChatOpenAI
from pydantic_settings import BaseSettings


class LLMSettings(BaseSettings):
    lemma_base_url: str = "http://lemma:8081/v1"
    lemma_api_key: str = "sk-noop"
    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    embedding_model: str = "text-embedding-3-small"
    chat_model: str = "gpt-4o-mini"

    model_config = {"env_prefix": "", "case_sensitive": False}


def create_llm_client(settings: LLMSettings | None = None) -> AsyncOpenAI:
    s = settings or LLMSettings()
    return AsyncOpenAI(base_url=s.lemma_base_url, api_key=s.lemma_api_key)


def create_embed_client(settings: LLMSettings | None = None) -> AsyncOpenAI:
    s = settings or LLMSettings()
    api_key = s.openai_api_key or s.lemma_api_key
    return AsyncOpenAI(base_url=s.openai_base_url, api_key=api_key)


def create_langchain_llm(settings: LLMSettings | None = None) -> ChatOpenAI:
    s = settings or LLMSettings()
    return ChatOpenAI(
        model=s.chat_model,
        base_url=s.lemma_base_url,
        api_key=s.lemma_api_key,
        temperature=0.3,
    )
