# Strava Import

Projeto para importação e análise de dados do Strava com exportação para Markdown em formato tabular.

## ✨ Funcionalidades

- 🔐 Autenticação OAuth2 com a API do Strava
- 📥 Download de todas as suas atividades
- 📊 Exportação para Markdown em formato de tabela
- 📈 Estatísticas gerais (distância total, tempo, médias)
- 🏃 Agrupamento por tipo de atividade (corrida, ciclismo, etc)
- ⚡ Cálculo automático de pace, duração formatada e muito mais

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

## 🚀 Início Rápido

### 1. Criar aplicativo no Strava

Acesse https://www.strava.com/settings/api e crie um novo aplicativo.

### 2. Configurar credenciais

```bash
cp .env.example .env
# Edite .env com seu CLIENT_ID e CLIENT_SECRET
```

### 3. Executar

```bash
uv run strava-import
```

O script irá guiá-lo pelo processo de autorização OAuth2.

## 📖 Documentação Completa

Veja [USAGE.md](USAGE.md) para instruções detalhadas de configuração e uso.

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

```bash      # Inicialização do pacote
│       ├── main.py               # Script principal
│       ├── strava_api.py         # Cliente da API do Strava
│       └── markdown_exporter.py  # Exportador para Markdown
├── .env.example                  # Exemplo de variáveis de ambiente
├── .gitignore                    # Arquivos ignorados pelo Git
├── .python-version               # Versão do Python
├── pyproject.toml                # Configurações do projeto
├── README.md                     # Este arquivo
└── USAGE.md                      # Guia detalhado de uso
```

## 📊 Exemplo de Saída

O script gera tabelas Markdown como:

| Data | Nome | Tipo | Distância | Duração | Pace | Elevação | Kudos |
|------|------|------|-----------|---------|------|----------|-------|
| 30/12/2025 08:30 | Morning Run | Run | 10.50 km | 00:52:30 | 5:00 /km | 120 m | 15 |
| 29/12/2025 18:00 | Evening Ride | Ride | 35.20 km | 01:25:15 | N/A | 450 m | 8 |
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
