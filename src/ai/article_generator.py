"""AI-powered article generation for outage summaries."""

from typing import List, Optional, Dict
import logging
from src.models import ChangeEvent
from src.ai.config import AIConfig
from src.utils.logger import get_logger


class AIArticleGenerator:
    """Generates article-style summaries using AI services."""

    def __init__(self, config: Optional[AIConfig] = None):
        self.config = config or AIConfig()
        self.logger = get_logger("ai_generator")
        self.cache: Dict[str, str] = {}
        self._client = None

        if not self.config.api_key:
            self.logger.warning("AI API key not configured - article generation disabled")

    def _get_client(self):
        """Get or create AI client."""
        if self._client is not None:
            return self._client

        if not self.config.api_key:
            return None

        try:
            if self.config.provider == "openai":
                from openai import AsyncOpenAI
                self._client = AsyncOpenAI(api_key=self.config.api_key)
            
            elif self.config.provider == "anthropic":
                from anthropic import AsyncAnthropic
                self._client = AsyncAnthropic(api_key=self.config.api_key)
            
            elif self.config.provider == "gemini":
                # NOVA MIGRACAO: Usa o SDK recomendado 'google-genai'
                from google import genai
                self._client = genai.Client(api_key=self.config.api_key)
            
            else:
                self.logger.error(f"Unknown AI provider: {self.config.provider}")
                return None
                
        except ImportError as e:
            self.logger.error(f"AI library for {self.config.provider} not installed: {e}")
            return None

        return self._client

    async def generate_article(self, changes: List[ChangeEvent]) -> Optional[str]:
        """Generate an article summary for detected changes."""
        if not changes:
            return None

        client = self._get_client()
        if client is None:
            self.logger.debug("AI client not available, skipping article generation")
            return None

        # Check cache
        cache_key = ""
        if self.config.enable_cache:
            cache_key = self._create_cache_key(changes)
            if cache_key in self.cache:
                self.logger.debug("Returning cached article")
                return self.cache[cache_key]

        # Prepare context
        context = self._prepare_context(changes)

        try:
            article = await self._call_ai_service(context)

            if article:
                # Add disclaimer
                article_with_disclaimer = (
                    f"{article}\n\n"
                    f"---\n"
                    f"*Resumo gerado via IA ({self.config.provider}) com dados do DownDetector.*"
                )

                # Cache result
                if self.config.enable_cache and cache_key:
                    self.cache[cache_key] = article_with_disclaimer

                self.logger.info(f"AI article generated successfully using {self.config.provider}")
                return article_with_disclaimer

        except Exception as e:
            self.logger.error(f"Failed to generate AI article: {e}")

        return None

    async def _call_ai_service(self, context: str) -> Optional[str]:
        """Call AI service to generate article."""
        prompt = f"""
        Atue como um jornalista de tecnologia especializado em infraestrutura.
        Com base nos dados de instabilidade abaixo, escreva um artigo curto, informativo e objetivo.
        
        Requisitos:
        - 200-300 palavras.
        - Use português do Brasil (pt-BR).
        - Explique o impacto potencial para os usuários.
        - Mencione regiões afetadas se houver dados.
        - Mantenha um tom profissional.

        Dados da Instabilidade:
        {context}

        Artigo:"""

        try:
            if self.config.provider == "openai":
                return await self._call_openai(prompt)
            elif self.config.provider == "anthropic":
                return await self._call_anthropic(prompt)
            elif self.config.provider == "gemini":
                return await self._call_gemini(prompt)
            else:
                return None
        except Exception as e:
            self.logger.error(f"AI API call failed ({self.config.provider}): {e}")
            return None

    async def _call_openai(self, prompt: str) -> Optional[str]:
        """Call OpenAI API."""
        response = await self._client.chat.completions.create(
            model=self.config.model,
            messages=[
                {"role": "system", "content": "You are a technical journalist."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature,
        )
        return response.choices[0].message.content.strip()

    async def _call_anthropic(self, prompt: str) -> Optional[str]:
        """Call Anthropic API."""
        response = await self._client.messages.create(
            model=self.config.model,
            max_tokens=self.config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()

    async def _call_gemini(self, prompt: str) -> Optional[str]:
        """Call Google Gemini API using the recommended google-genai SDK."""
        # Usa client.models.generate_content_async para manter a operação assíncrona
        response = await self._client.models.generate_content_async(
            model=self.config.model,
            contents=prompt,
            config={
                "temperature": self.config.temperature,
                "max_output_tokens": self.config.max_tokens,
            }
        )
        return response.text

    def _prepare_context(self, changes: List[ChangeEvent]) -> str:
        """Prepare context string for AI."""
        context_parts = []
        for change in changes:
            change_info = [
                f"Serviço: {change.service_name}",
                f"Tipo de Mudança: {change.change_type.value}",
                f"Status Atual: {change.new_status.value}",
                f"Relatórios de Falha: {change.new_report_count:,}",
                f"Severidade: {change.new_severity.value}",
                f"Horário: {change.timestamp.strftime('%H:%M UTC')}",
            ]
            context_parts.append("\n".join(change_info))
        return "\n\n---\n\n".join(context_parts)

    def _create_cache_key(self, changes: List[ChangeEvent]) -> str:
        """Create a cache key for changes."""
        key_parts = [f"{c.service_name}:{c.change_type.value}" for c in changes]
        return "|".join(sorted(key_parts))

    def clear_cache(self) -> None:
        """Clear the article cache."""
        self.cache.clear()
        self.logger.debug("AI article cache cleared")
