# Demo do karpathy loop

Exemplo mínimo e rodável. `checks/metric.sh` é o **juiz imutável**: conta quantas funções de `demo_target.py` têm **mais de 20 linhas** e imprime **exatamente 1 número** no stdout (nada mais). `demo_target.py` tem 4 funções propositalmente subótimas (código verboso, if/elif em cadeia, concatenação de string em loop) — material para o loop otimizar.

## 1. Testar o juiz

```bash
cd demo
bash checks/metric.sh
# saída esperada: um único número (ex.: 4)
```

A saída deve casar a regex `^[+-]?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?$` em **1 linha** — é o formato que a skill exige de qualquer juiz.

## 2. Rodar o loop sobre o demo

Peça ao seu agente (com a skill instalada):

> "Rode o karpathy loop para reduzir o número de funções com mais de 20 linhas em `demo_target.py` por 10 minutos, minimize"

O que deve acontecer:

1. **Pré-flight** — branch `karpathy/...` criada, commit `karpathy baseline`, baseline = mediana de 3 execuções do juiz (ex.: 4).
2. **Cada rodada** — um builder descartável faz UMA refatoração pequena (extrair helper, comprehension, dicionário de taxas…), **sem tocar em `checks/`**; o juiz mede de novo; melhora real (> ε de ruído) vira commit, senão **revert**.
3. **FIM** — volta à branch original e reporta baseline vs. melhor (ex.: `4 → 0, −100%`).

**Regra do jogo:** se o builder tentar "melhorar" editando `checks/metric.sh` (fraude), o juiz detecta a violação estrutural e aborta o loop. É exatamente esse o problema que a skill existe para impedir.
