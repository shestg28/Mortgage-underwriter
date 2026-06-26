from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Local Postgres defaults (local installation)
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "shes"
    POSTGRES_DB: str = "loan_system"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    JWT_SECRET: str = "change-me"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15

    class Config:
        env_file = "../.env"


def get_database_url(settings: Settings | None = None) -> str:
    s = settings or Settings()
    # Build a DB URL that omits the password if not set (works with local trust setups)
    if s.POSTGRES_PASSWORD:
        return (
            f"postgresql://{s.POSTGRES_USER}:{s.POSTGRES_PASSWORD}@{s.POSTGRES_HOST}:{s.POSTGRES_PORT}/{s.POSTGRES_DB}"
        )
    return f"postgresql://{s.POSTGRES_USER}@{s.POSTGRES_HOST}:{s.POSTGRES_PORT}/{s.POSTGRES_DB}"


settings = Settings()
