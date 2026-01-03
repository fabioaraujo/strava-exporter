# Gerenciamento de Rate Limit

## 📊 Limites da API do Strava

A API do Strava tem os seguintes limites:
- **200 requisições por 15 minutos**
- **1000 requisições por dia**

## 🛡️ Proteções Implementadas

### 1. **Retry Automático com Backoff**
Quando o erro 429 (Rate Limit) ocorre:
- O sistema aguarda automaticamente o tempo especificado pelo Strava
- Tenta novamente até 5 vezes
- Mostra progresso no console

### 2. **Salvamento Incremental**
O cache é salvo:
- A cada **10 atividades** processadas (atividades novas)
- A cada **50 atividades** processadas (processamento em lote)
- Sempre que ocorre um erro
- Quando você pressiona **Ctrl+C**

### 3. **Continuação Automática**
- Se o processo for interrompido, execute novamente
- O sistema detecta quais atividades já foram processadas
- Continua apenas com as pendentes

## 🚀 Como Usar

### Primeira Execução (Todas as Atividades)

```bash
uv run strava-exporter
```

Quando perguntado sobre buscar detalhes completos:
- Digite **"n"** se quiser apenas as novas
- Digite **"s"** para processar todas (pode levar horas)

### Se For Interrompido

1. **Pressione Ctrl+C** para pausar com segurança
2. Aguarde a mensagem: `✅ Progresso salvo!`
3. Execute novamente: `uv run strava-exporter`
4. O sistema continua de onde parou

### Processamento de Novas Atividades

Nas próximas execuções:
- O sistema busca apenas atividades novas
- Os detalhes são obtidos automaticamente
- Cache salvo a cada 10 atividades

## 💡 Dicas

### Para 1713 Atividades

**Tempo estimado:**
- ~8-10 minutos por lote de 200 atividades
- Total: **1-2 horas** (com rate limits)

**Recomendações:**
1. Execute em horário que pode deixar rodando
2. Mantenha o terminal aberto
3. Não precisa supervisionar - é automático

### Se Atingir Rate Limit

O sistema irá:
1. Mostrar: `⏸️  Rate limit atingido! Aguardando 900s...`
2. Aguardar automaticamente (geralmente 15 minutos)
3. Tentar novamente automaticamente
4. Salvar progresso periodicamente

### Em Caso de Erro

Se algo der errado:
1. Pressione **Ctrl+C**
2. Verifique o arquivo `strava_cache.json`
3. Execute novamente - continua de onde parou

## 📁 Arquivos Importantes

- **`strava_cache.json`** - Cache com todas as atividades
- **`strava_cache.json.bkp`** - Backup automático (se existir)

## ⚡ Performance

### Primeira Execução (1713 atividades)
- **Sem detalhes:** ~2 minutos (apenas lista)
- **Com detalhes:** 1-2 horas (com rate limits)

### Execuções Subsequentes
- **Atividades novas:** ~1 segundo por atividade
- **Cache salvo automaticamente**

## 🐛 Troubleshooting

### "Rate limit atingido após 5 tentativas"
- Aguarde 15 minutos
- Execute novamente

### "KeyboardInterrupt"
- Normal quando você pressiona Ctrl+C
- Cache foi salvo automaticamente

### Cache corrompido
- Renomeie `strava_cache.json` para `.old`
- Execute novamente para reconstruir

## 🎯 Exemplo de Execução

```
🚴 Strava Exporter - Exportador de Atividades
==================================================

⏳ Obtendo informações do atleta...
✅ Conectado como: Fabio Araujo

⏳ Verificando cache local...
💾 1713 atividades no cache
   Última atualização: 2026-01-03T14:25:27.287376

✅ 850 atividades já processadas anteriormente
⏳ Buscando detalhes de 863 atividades restantes...
   (Isso levará vários minutos...)
   💡 Pressione Ctrl+C para pausar e salvar progresso

   Processadas 50/863 atividades...
   💾 Cache salvo (900/1713)
   Processadas 100/863 atividades...
   💾 Cache salvo (950/1713)
   ...
   ⏸️  Rate limit atingido! Aguardando 900s antes de tentar novamente...
   (Tentativa 1/5)
   ...
✅ Detalhes obtidos para todas as 1713 atividades
```
