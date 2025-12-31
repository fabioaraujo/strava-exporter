# Strava Import

Projeto para importação e análise de dados do Strava.

## 🚀 Tecnologias

- Python 3.12+
- UV (gerenciador de pacotes e ambientes)

## 📦 Instalação

### Pré-requisitos

Certifique-se de ter o [UV](https://github.com/astral-sh/uv) instalado:

```bash
# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Configuração do Projeto

1. Clone o repositório:
```bash
git clone <seu-repositório>
cd strava-import
```

2. Crie o ambiente virtual e instale as dependências:
```bash
uv sync
```

3. Ative o ambiente virtual:
```bash
# Windows PowerShell
.venv\Scripts\Activate.ps1

# Windows CMD
.venv\Scripts\activate.bat
```

## 🏃 Uso

Execute o script principal:

```bash
uv run strava-import
```

Ou com o ambiente ativado:

```bash
strava-import
```

## 🛠️ Desenvolvimento

Instale as dependências de desenvolvimento:

```bash
uv sync --extra dev
```

Execute os testes:

```bash
uv run pytest
```

Formate o código:

```bash
uv run black .
uv run ruff check .
```

## 📝 Estrutura do Projeto

```
strava-import/
├── src/
│   └── strava_import/
│       ├── __init__.py     # Inicialização do pacote
│       └── main.py         # Script principal
├── .gitignore              # Arquivos ignorados pelo Git
├── .python-version         # Versão do Python
├── pyproject.toml          # Configurações do projeto
└── README.md               # Este arquivo
```

## 📄 Licença

Este projeto é de código aberto.
