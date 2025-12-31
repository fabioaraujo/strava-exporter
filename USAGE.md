# Guia de Uso - Strava Exporter

Este guia explica como configurar e usar o Strava Exporter para baixar suas atividades.

## 📋 Pré-requisitos

1. Conta no Strava
2. Python 3.12+
3. UV instalado

## 🔧 Configuração

### 1. Criar Aplicativo no Strava

1. Acesse: https://www.strava.com/settings/api
2. Clique em "Create App" ou "My API Application"
3. Preencha os campos:
   - **Application Name:** Seu nome de app (ex: "Meu Exportador")
   - **Category:** Escolha uma categoria
   - **Club:** Deixe em branco
   - **Website:** http://localhost
   - **Authorization Callback Domain:** localhost
4. Clique em "Create"
5. Anote o **Client ID** e **Client Secret**

### 2. Configurar Variáveis de Ambiente

1. Copie o arquivo de exemplo:
   ```bash
   cp .env.example .env
   ```

2. Edite o arquivo `.env` e adicione suas credenciais:
   ```
   STRAVA_CLIENT_ID=12345
   STRAVA_CLIENT_SECRET=abc123def456...
   ```

### 3. Executar o Script

```bash
uv run strava-exporter
```

### 4. Processo de Autorização (primeira vez)

O script irá:
1. Gerar uma URL de autorização
2. Você abrirá no navegador
3. Autorizará o aplicativo
4. Será redirecionado para uma URL com um código
5. Copiará o código e colará no terminal
6. O token será salvo automaticamente

**Exemplo de URL de redirecionamento:**
```
http://localhost/?state=&code=abc123def456&scope=read,activity:read_all
```

Copie apenas a parte: `abc123def456`

## 📊 Arquivos Gerados

Após a execução, serão criados arquivos no diretório `atividades/`:

- **README.md** - Índice geral com resumo de todos os anos
- **strava_2025.md** - Atividades de 2025
- **strava_2024.md** - Atividades de 2024
- E assim por diante para cada ano

## 📝 Formato da Tabela

As tabelas Markdown incluem:
- Data e hora
- Nome da atividade
- Tipo (corrida, ciclismo, natação, etc)
- Distância (km)
- Duração (HH:MM:SS)
- Pace (min/km)
- Elevação (m)
- Kudos recebidos

## ⚙️ Personalização

### Limitar número de atividades

Edite o arquivo [src/strava_exporter/main.py](src/strava_exporter/main.py#L77):

```python
activities = client.get_all_activities(max_activities=50)  # Buscar apenas 50
```

### Buscar TODAS as atividades

```python
activities = client.get_all_activities()  # Sem limite
```

## 🔄 Atualizar Token

Os tokens do Strava expiram após algumas horas. Se receber erro de autenticação:

1. Delete a linha `STRAVA_ACCESS_TOKEN` do arquivo `.env`
2. Execute novamente: `uv run strava-exporter`
3. O processo de autorização será reiniciado

## 🆘 Problemas Comuns

### "Credenciais não encontradas"
- Verifique se o arquivo `.env` existe na raiz do projeto
- Confirme que CLIENT_ID e CLIENT_SECRET estão corretos

### "Invalid authorization code"
- O código expira rapidamente, tente novamente mais rápido
- Certifique-se de copiar o código completo da URL

### "Rate limit exceeded"
- A API do Strava tem limites de requisições
- Aguarde alguns minutos e tente novamente

## 📚 Documentação da API

- [Strava API Documentation](https://developers.strava.com/docs/reference/)
- [Strava Authentication](https://developers.strava.com/docs/authentication/)
