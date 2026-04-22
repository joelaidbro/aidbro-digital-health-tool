from dotenv import dotenv_values
import os

env_path = os.path.join(os.path.dirname(__file__), ".env")

config = dotenv_values(env_path)

print("ENV CONTENT:", config)