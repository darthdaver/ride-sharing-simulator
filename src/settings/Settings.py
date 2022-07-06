from pydantic import BaseSettings

class Settings(BaseSettings):
    H3_RESOLUTION: int
    class Config:
        env_file = '.env'