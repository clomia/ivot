import os
from dotenv import load_dotenv

load_dotenv()

print(os.environ.get("APP_KEY"))
print(os.environ.get("APP_SECRET"))
print(os.environ.get("CANO"))
print(os.environ.get("ACNT_PRDT_CD"))
