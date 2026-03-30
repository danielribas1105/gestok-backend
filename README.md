# Backend - FastAPI + PostgreSQL

## 🚀 Pré-requisitos
- [Python 3.11+](https://www.python.org/downloads/)
- [PostgreSQL](https://www.postgresql.org/download/)
- [pip](https://pip.pypa.io/en/stable/)

---

## 📦 Instalação

Clone o repositório e entre na pasta do projeto:

```bash
git clone https://github.com/seu-repo/gestobra.git
cd gestobra/code

## Crie o ambiente virtual:

python -m venv venv

## Ative o ambiente virtual de acordo com o terminal que você usa:

### Prompt de Comando (cmd):

venv\Scripts\activate

### PowerShell:

.\venv\Scripts\Activate.ps1

### Git Bash:

source venv/Scripts/activate

## Instale as dependências:

pip install -r requirements.txt

## Gerar uma SECRET_KEY:

python -c "import secrets; print(secrets.token_hex(32))"

## ▶️ Rodando o servidor

uvicorn app.main:app --reload

## 🌳 Arquitetura da aplicação

tree /f | more

tree /f /a | more

## 🏦 Criando tabelas e rodando a primeira migração

alembic init alembic

alembic revision --autogenerate -m "initial database structure"

alembic upgrade head
