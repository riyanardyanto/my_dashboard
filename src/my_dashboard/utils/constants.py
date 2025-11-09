from httpx_ntlm import HttpNtlmAuth

FILENAME = "DB.xlsx"
TARGET_FOLDER = "Target"
MAIN_URL = "http://ots.app.pmi/db.aspx?"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/111.0.0.0 Safari/537.36"
}
USERNAME = "f-pmiidkraplu18"
PASSWORD = "Sampoerna1"
NTLM_AUTH = HttpNtlmAuth(username=USERNAME, password=PASSWORD)


TABLE_HEAD = [
    "Machine",
    "Description",
    "Stops",
    "DT [min]",
]

GREEN = "🟢"
RED = "🔴"
