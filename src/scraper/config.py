# ...
from pydantic_settings import BaseSettings
from typing import List, Optional # Adicione Optional se não estiver

class ScraperConfig(BaseSettings):
    # ... (outras configurações)
    user_agent: str = "Mozilla/5.0 (compatible; OutageBot/1.0)"
    monitored_services: str = "google,facebook,twitter,instagram,whatsapp"
    
    # --- Configurações do Crawl4AI ---
    CRAWL4AI_API_KEY: Optional[str] = None
    CRAWL4AI_ENDPOINT: str = "https://api.crawl4ai.com/v1" 
    
    @property
# ...
