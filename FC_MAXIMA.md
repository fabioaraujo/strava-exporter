# Gerenciamento de FC Máxima

## 🎯 Como Funciona

A FC Máxima é usada para calcular o **Relative Effort** (esforço relativo) de cada atividade.

## 📊 Prioridades de Detecção

O sistema usa a seguinte ordem de prioridade:

### 1. **Configuração Manual** (Maior prioridade) ✅
```env
USER_MAX_HR=180
```
- No arquivo `.env`
- **Nunca é recalculada automaticamente**
- Use se você conhece sua FC máxima de um teste laboratorial
- Recomendado para máxima precisão

### 2. **FC do Cache** (Atualização Inteligente)
- Salva automaticamente no `strava_cache.json`
- **Regra de atualização:**
  - ✅ Usa se tem **menos de 6 meses**
  - ⚠️ Recalcula se tem **mais de 6 meses**
  
**Exemplo:**
```
💓 Usando FC Máxima do cache: 175 bpm
   Última detecção: há 45 dias
```

**Se desatualizada:**
```
⚠️  FC Máxima do cache tem 210 dias (7 meses)
   Recalculando com base nos dados recentes...
💓 FC Máxima detectada: 173 bpm (última vez em 2025)
   Baseado nas atividades dos últimos 6 meses
```

### 3. **Detecção Automática**
- Analisa atividades dos **últimos 6 meses**
- Ignora valores suspeitos (>200 bpm)
- Usa percentil 95 se houver outliers
- Salva no cache para próximas execuções

## ⏱️ Regras de Atualização

| Idade da FC | Ação | Motivo |
|-------------|------|--------|
| < 6 meses | ✅ Usa do cache | Ainda atual |
| 6-12 meses | ⚠️ Recalcula | Pode ter mudado |
| > 12 meses | 🔄 Recalcula | Provavelmente mudou |
| Sem data | 🔄 Recalcula | Cache antigo |

### Por que 6 meses?

**Para a janela de detecção:**
- Captura atividades intensas recentes
- Evita usar dados muito antigos
- FC máxima pode variar com condicionamento físico

**Para a atualização do cache:**
- A FC máxima diminui aproximadamente **1 bpm por ano** em média
- Em 6 meses: ~0.5 bpm (variação insignificante)
- Em 1 ano: ~1 bpm (começa a ser significativo)

**Conclusão:** 6 meses é um bom equilíbrio entre:
- Não recalcular desnecessariamente
- Manter dados atualizados e relevantes

## 🔄 Quando é Recalculada?

A FC é recalculada automaticamente:

1. **Ao buscar novas atividades:**
   - Salva no cache com data atual
   - Atualiza se novas atividades tiverem FC maior

2. **Se FC do cache está antiga:**
   - Mais de 6 meses desde última detecção
   - Recalcula usando dados recentes

3. **Se não houver FC no cache:**
   - Primeira execução
   - Cache corrompido ou deletado

## 📝 Estrutura do Cache

```json
{
  "last_update": "2026-01-03T15:08:50",
  "total_activities": 1713,
  "detected_max_hr": 175,
  "detected_max_hr_date": "2025-12-15T18:30:00Z",
  "activities": [...]
}
```

## 💡 Recomendações

### Para Máxima Precisão:
1. Faça um teste de FC máxima (teste de esforço)
2. Configure no `.env`: `USER_MAX_HR=180`
3. Nunca será alterado automaticamente

### Para Comodidade:
1. Deixe o sistema detectar automaticamente
2. Atualiza a cada 6 meses
3. Sempre usa os últimos 2 anos de dados

### Se Sua FC Mudou:
1. **Opção 1:** Configure manualmente no `.env`
2. **Opção 2:** Delete o cache e recalcule:
   ```bash
   rm strava_cache.json
   uv run strava-exporter
   ```
3. **Opção 3:** Aguarde 6 meses (atualização automática)

## 🔍 Como Verificar

### No Terminal:
```
💓 Usando FC Máxima do cache: 175 bpm
   Última detecção: há 45 dias
```

### No Arquivo Markdown:
```markdown
**FC Máxima utilizada nos cálculos:** 175 bpm
```

### No Cache (strava_cache.json):
```json
"detected_max_hr": 175,
"detected_max_hr_date": "2025-12-15T18:30:00Z"
```

## 🎯 Exemplo de Atualização Automática

**Dia 1 (Janeiro 2025):**
```
💓 FC Máxima detectada: 178 bpm (última vez em 2024)
   Salva no cache
```

**Dia 60 (Março 2025):**
```
💓 Usando FC Máxima do cache: 178 bpm
   Última detecção: há 60 dias
   Não recalcula (< 6 meses)
```

**Dia 200 (Julho 2025):**
```
⚠️  FC Máxima do cache tem 200 dias (6.6 meses)
   Recalculando com base nos dados recentes...
💓 FC Máxima detectada: 176 bpm (última vez em 2025)
   Nova FC: 176 bpm (diminuiu 2 bpm - esperado!)
```

## 📊 Impacto da Atualização

Com FC desatualizada (6+ meses):
- Relative Effort pode estar **levemente impreciso**
- Exemplo: 178 bpm (antiga) vs 176 bpm (atual)
- Diferença no cálculo: ~1-2% no Relative Effort

Por isso 6 meses é um bom intervalo! ✅
