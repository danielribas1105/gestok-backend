import unicodedata


def generate_name_code(description: str) -> str:
    text = description.strip()  # remove só espaços nas pontas (o padding do arquivo)
    text = text.upper()
    text = unicodedata.normalize("NFKD", text).encode("ASCII", "ignore").decode("ASCII")
    text = text.replace(" ", "_")
    return text
