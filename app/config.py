from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_hostname: str
    database_port: int
    database_username: str
    database_password: str
    database_name: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int

    class Config:
        env_file = "../.env"  # if you're using a .env file for configuration


settings = Settings()
print("Database hostname:", settings.database_hostname)
print("Database name:", settings.database_name)
