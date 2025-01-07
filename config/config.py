import os

from dotenv import load_dotenv


class Config:
    # Load environment variables from .env file
    load_dotenv()

    # API keys
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

    # Search engine identifier (e.g., Google CSE)
    SEARCH_ENGINE = os.getenv("SEARCH_ENGINE", "")

    @staticmethod
    def is_valid():
        """Validate required environment variables."""
        missing_vars = [
            var for var in ["OPENAI_API_KEY", "GOOGLE_API_KEY", "SEARCH_ENGINE"]
            if not getattr(Config, var)
        ]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
