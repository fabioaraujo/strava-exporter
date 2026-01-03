# Cálculo Local de Relative Effort

## 🎯 O que é Relative Effort?

O **Relative Effort** (também chamado de Suffer Score) é uma métrica proprietária do Strava que mede o esforço relativo de uma atividade baseado em:

- Frequência cardíaca ao longo do tempo
- Zonas de FC personalizadas do usuário
- Duração da atividade
- Tipo de atividade

## ⚠️ Limitação da API

A API do Strava **NÃO retorna** o Relative Effort para:
- Usuários que não são assinantes Strava
- Mesmo no endpoint detalhado de atividades

Resultado: `suffer_score: null` em todas as atividades.

## ✨ Solução: Cálculo Local

Implementamos um **cálculo estimado** baseado no algoritmo TRIMP (Training Impulse), adaptado para ser similar ao Relative Effort do Strava.

### Fórmula Implementada

```
Relative Effort = duração × intensidade × exp(intensidade) × fator_atividade × 2.5
```

Onde:
- **Duração**: Tempo em movimento (minutos)
- **Intensidade**: FC média / FC máxima estimada
- **Exponencial**: Aumenta não-linearmente com intensidade
- **Fator de atividade**: Multiplica por tipo de esporte

### Fatores por Tipo de Atividade

| Tipo | Fator | Motivo |
|------|-------|--------|
| Run | 1.2 | Corrida é mais intensa |
| Ride | 1.0 | Base (referência) |
| Walk | 0.8 | Caminhada menos intensa |
| Workout | 1.1 | Treino funcional intenso |
| Yoga | 0.6 | Yoga menos intensa |

### FC Máxima Estimada

O sistema usa 3 níveis de detecção (em ordem de prioridade):

1. **Configuração Manual** (mais preciso)
   - Configure `USER_MAX_HR=190` no arquivo `.env`
   - Recomendado se você conhece sua FC máxima atual

2. **Detecção Automática - Dados Recentes** (recomendado)
   - Analisa atividades dos **últimos 2 anos**
   - Usa a maior FC registrada nesse período
   - Evita usar dados muito antigos (FC diminui ~1 bpm/ano)
   - Exemplo: `💓 FC Máxima detectada: 175 bpm (última vez em 2025)`

3. **Detecção Automática - Histórico Completo** (fallback)
   - Se não houver dados recentes, analisa todo histórico
   - Mostra aviso se o dado for antigo
   - Exemplo: `💓 FC Máxima detectada: 180 bpm (registrada em 2018)`
   - `⚠️  Dado antigo - considere configurar USER_MAX_HR`

4. **Padrão** (último recurso)
   - **185 bpm** (fórmula: 220 - 35 anos)
   - Apenas se não houver nenhum dado de FC

### Por que Priorizar Dados Recentes?

A FC máxima **diminui com a idade**:
- Aproximadamente **1 bpm por ano**
- Uma FC de 185 bpm em 2018 pode ser 177 bpm em 2026
- Usar dados antigos **superestima a intensidade** dos treinos atuais

## 📊 Comparação com Strava Real

### Exemplo 1: Caminhada Leve
```
- Duração: 15 minutos
- FC Média: 113 bpm
- FC Máxima: 123 bpm
- Tipo: Walk

Cálculo:
- Intensidade = 113 / 185 = 0.61
- Exponencial = 1 + (0.61^1.5) = 1.48
- Effort = 15 × 0.61 × 1.48 × 0.8 × 2.5 = 27

Resultado: ~27 (leve)
```

### Exemplo 2: Corrida Intensa
```
- Duração: 30 minutos
- FC Média: 155 bpm
- FC Máxima: 175 bpm
- Tipo: Run

Cálculo:
- Intensidade = 155 / 185 = 0.84
- Exponencial = 1 + (0.84^1.5) = 1.77
- Effort = 30 × 0.84 × 1.77 × 1.2 × 2.5 = 133

Resultado: ~133 (moderado-alto)
```

### Faixas Típicas (Similar ao Strava)

| Faixa | Esforço | Descrição |
|-------|---------|-----------|
| 0-20 | Muito Leve | Recuperação ativa |
| 21-50 | Leve | Exercício leve |
| 51-100 | Moderado | Treino aeróbico |
| 101-200 | Alto | Treino intenso |
| 201-300 | Muito Alto | Treino muito intenso |
| 300+ | Extremo | Competições/esforço máximo |

## 🎯 Precisão

**Limitações:**
- ❌ Não é o cálculo exato do Strava (proprietário)
- ❌ Não usa zonas de FC personalizadas do usuário
- ❌ Não considera variações de FC ao longo da atividade

**Vantagens:**
- ✅ Estimativa razoável baseada em ciência esportiva
- ✅ Funciona para TODOS os usuários (não precisa Strava PRO)
- ✅ Baseado em algoritmo TRIMP reconhecido
- ✅ Ajustado por tipo de atividade
- ✅ Consistente entre atividades

## 🔧 Como Funciona

1. **API retorna `suffer_score: null`**
2. Sistema verifica se há FC média disponível
3. Se sim, calcula localmente usando a fórmula
4. Exibe o valor calculado na coluna Relative Effort

## 💡 Melhorias Futuras

Podemos implementar:
- [ ] Zonas de FC personalizadas (usuário configurar sua FC máx)
- [ ] Análise de elevação (subidas aumentam esforço)
- [ ] Considerar temperatura (calor aumenta FC)
- [ ] Histórico de fitness (condicionamento atual)
- [ ] Variabilidade de FC ao longo da atividade (se disponível)

## 📖 Referências

- [TRIMP (Training Impulse)](https://en.wikipedia.org/wiki/Training_load)
- [Heart Rate Based Training](https://www.polar.com/blog/calculating-training-load/)
- Algoritmo baseado em estudos científicos de fisiologia do exercício
