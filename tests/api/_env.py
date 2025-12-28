import os


def get_kis_base_url() -> str:
    mode = os.getenv("KIS_MODE", "REAL").upper()
    if mode == "VTS":
        return os.getenv("VTS_BASE_URL")
    return os.getenv("REAL_BASE_URL")


def get_kis_app_key() -> str:
    mode = os.getenv("KIS_MODE", "REAL").upper()
    if mode == "VTS":
        return os.getenv("VTS_APP_KEY")
    return os.getenv("REAL_APP_KEY")


def get_kis_app_secret() -> str:
    mode = os.getenv("KIS_MODE", "REAL").upper()
    if mode == "VTS":
        return os.getenv("VTS_APP_SECRET")
    return os.getenv("REAL_APP_SECRET")
