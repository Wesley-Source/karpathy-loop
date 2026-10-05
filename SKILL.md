---
name: karpathy-loop
description: Loop de otimização estilo Karpathy — melhora uma métrica mensurável de um alvo por tempo limitado, com juiz (checks/metric.sh) separado e imutável, mediana de 3 execuções, revert automático do que não melhora e relatório final baseline vs. melhor. Use quando o usuário pedir para "melhorar X por N minutos", "rodar o karpathy loop" ou otimizar uma métrica objetiva (latência, contagem de erros, warnings, precisão, tamanho de bundle).
---

# Karpathy Loop

Otimiza uma métrica mensurável por tempo limitado. A arquitetura tem **dois papéis separados**:

- **Agente principal = juiz PERSISTENTE**: orquestra o loop inteiro, executa a métrica, decide aceite/revert, guarda o estado acumulado (melhor_aceito, SPREAD_HIST, contadores) durante toda a sessão. **Nunca faz a mudança da rodada.**
- **Builder = subagente DESCARTÁVEL**: criado do zero a cada rodada via ferramenta `task`. Faz UMA mudança pequena e é descartado. Sem memória da conversa — pega contexto sozinho lendo `karpathy-results.md` e o código.

O juiz pontua com `checks/metric.sh`, separado e **IMUTÁVEL**; só mantém mudança que melhora de verdade. No fim, reporta o quanto melhorou.

**Regra de ouro: o otimizador (builder) nunca edita o juiz.** Toda mudança sob `checks/` é violação estrutural → aborto.

## Entrada

- `alvo` — o que otimizar (ex.: "tempo de build", "warnings do lint").
- `direção` — `maximize` ou `minimize`. **OBRIGATÓRIO**: pergunte ao usuário se faltar.
- `duração_do_loop` — minutos.
- `objetivo` (opcional) — melhora absoluta acumulada mínima; atingir = FIM de sucesso.

Se `checks/metric.sh` não existir, ajude o usuário a escrevê-lo (deve imprimir **exatamente 1 número** no stdout) e exija a aprovação dele antes de prosseguir. Se já existir, use-o (confirme com o usuário).

## Caps fixos

- Máx. **20 rodadas**.
- **3 execuções** da métrica por medição.
- **3 falhas de execução** → FIM.
- Overshoot máximo do loop: última rodada + 3×T + tempo de edição (aceitável, documentado).

## Execução pinada da métrica

TODA execução (validação, baseline, rodadas) é idêntica:

1. `cd` à raiz do repo (toplevel).
2. `bash checks/metric.sh` sob `timeout $T`.
3. Cronometre cada execução com `date +%s` antes/depois → `D_run`; registre em `karpathy-results.md`.
4. Saída válida somente se: exit 0 **E** stdout contém exatamente 1 linha casando `^[+-]?[0-9]+(\.[0-9]+)?([eE][+-]?[0-9]+)?$` (teste com `grep -c` da regex sobre o stdout — resultado 1; **não use `wc -l`**, ele falso-rejeita stdout sem newline final).
5. Qualquer desvio (exit ≠ 0, saída fora do padrão) = **falha de execução**.

## Pré-flight (ordem fixa)

1. `git rev-parse --show-toplevel` → `cd` lá. Não é repo → use o cwd como raiz.
2. Gravar exclusões em `.git/info/exclude` (**NUNCA** no `.gitignore` do usuário): `node_modules/`, `.env`, `__pycache__/`, `dist/`, `karpathy-results.md`, `*.pem`, `credentials*`. No caminho não-repo: `git init` primeiro, depois o exclude.
3. Não-repo ou repo sem commits → `git init` (se preciso) + commit inicial com tudo.
4. Repo com commits e sujo → liste paths com `git status --porcelain -z`:
   - Sujeira **só em `checks/`** → ABORTAR pedindo que o usuário committe ou stashe o próprio WIP de `checks/` antes (o WIP seria commitado no baseline e se perderia no checkout final).
   - Caso contrário → `git stash push -u -- <todos os paths exceto checks/>` (`STASHED=1`).
5. `ORIGINAL_BRANCH=$(git branch --show-current)`; vazio (detached HEAD) → `ORIGINAL_SHA=$(git rev-parse HEAD)`. Grave.
6. Branch dedicada `karpathy/<slug>` — slug do alvo: `[a-z0-9-]`, máx. 40 chars; nome existente → sufixo `-2`, `-3`...
7. Commit `karpathy baseline` com o estado atual **incluindo `checks/`** (`git add -f` se `checks/` estiver gitignored; `--allow-empty` se nada a cometer) → `BASELINE_SHA`.
8. Validação: 1ª execução sob `timeout 600` (CAP_INICIAL anti-hang). Estourou → abortar com "métrica muito lenta". `T = 2×D_run` → REVALIDAR sob `T`: exit 0 + 1 linha + regex.
9. Baseline = **mediana de 3 execuções** sob `T`. Qualquer falha → aborto (nunca compare contra lixo). `melhor_aceito = mediana do baseline`.
10. Criar `karpathy-results.md` (APPEND-only) com seção `=== run <timestamp> ===`: baseline, BASELINE_SHA, ORIGINAL_BRANCH/ORIGINAL_SHA, `START=$(date +%s)`, T, SPREAD_HIST (spread do baseline = max−min das 3 execuções).

## Rotina canônica de aborto

Invocada por TODO caminho de aborto e por todo "voltar" — nunca improvisar:

1. Diff do estado sujo → append em `karpathy-results.md`.
2. Resíduo sujo → `git stash push -u` (`RESIDUO=1`).
3. `git checkout -f $ORIGINAL_BRANCH` (ou `git checkout -f $ORIGINAL_SHA`).
4. Relatório de abort: TODAS as mutações feitas + como desfazer cada uma.

## Builder da rodada (subagente descartável)

A mudança de cada rodada é feita por um **subagente NOVO** (ferramenta `task`, agente `general`) — **nunca pelo agente principal**. Rodada nova = builder novo, criado do zero:

- **Contexto próprio**: o prompt é mínimo; o builder lê `karpathy-results.md` e explora o código SOZINHO. O juiz NÃO cola contexto herdado nele — é isso que impede viés de rodadas anteriores e racionalização acumulada.
- **Sem poderes de juiz**: builder NÃO roda `metric.sh`, NÃO mede, NÃO commita, NÃO stasha — só edita.
- **Escopo**: EXATAMENTE UMA mudança (máx. 1 arquivo OU ~30 linhas), JAMAIS paths sob `checks/`.

Prompt padrão do builder (substitua os `<campos>`):

> Você é o builder da rodada N do karpathy loop. Objetivo: melhorar `<alvo>` (direção: `<maximize|minimize>`). Leia `karpathy-results.md` na raiz do repo para contexto (baseline, aceites e reverts anteriores) e explore o código por conta própria — não há contexto herdado. Faça EXATAMENTE UMA mudança pequena: máx. 1 arquivo OU ~30 linhas. JAMAIS toque em paths sob `checks/`. Não execute `metric.sh`, não commite, não stashe — apenas edite. Ao terminar, liste os arquivos alterados e o que fez.

## Rodada (repita)

1. `elapsed = $(date +%s) - START`; se `elapsed ≥ duração_do_loop × 60` → FIM.
2. **Integridade do juiz (dupla)**: `git diff --quiet $BASELINE_SHA -- checks/` E `git status --porcelain -- checks/` limpos. Sujo → ABORTO (juiz violado).
3. **Disparar o builder**: crie um subagente NOVO (prompt da seção acima) e aguarde a edição. Depois **audite** o retorno: `git status --porcelain` + `git diff --stat` + HEAD inalterado (`git rev-parse HEAD`). Mais de 1 arquivo, >~30 linhas, QUALQUER path sob `checks/` ou commit feito pelo builder = **violação** → revert total do que ele fez (passo 6) + `FALHAS++` + log. Quem mede e decide é você (juiz) — nunca o builder.
4. **Medir**: 3 execuções pinadas sob T (D_run de cada uma logado). Mediana (nº par de válidos → média dos 2 centrais).
5. **LOG em duas fases** (append): INTENÇÃO (commit/revert) ANTES de executar; RESULTADO DEPOIS — só afirme "revert executado" se todos os comandos terminaram exit 0.
6. **Revert fiel** (se não aceito OU falha de execução): rastreado → `git restore --source=HEAD --staged --worktree -- <path>`; arquivo novo → `rm <path>`. Após TODO revert: `git status --porcelain` limpo (exceto `karpathy-results.md`); sujo → ABORTO.
7. **Aceite**: aceitar SOMENTE se melhora na direção > ε:
   - maximize: `(mediana − melhor_aceito) > ε`; minimize: `(melhor_aceito − mediana) > ε`.
   - `ε = max(0.02 × |melhor_aceito|, spread desta rodada, SPREAD_HIST)`.
   - Após cada rodada: `SPREAD_HIST = max(SPREAD_HIST, spread da rodada)` — o piso histórico impede que ruído vire "melhora".
   - Aceito → `git add` EXATAMENTE os paths tocados (inclui arquivo novo; **nunca** `karpathy-results.md`, **nunca** `checks/`) + `git commit`; `melhor_aceito = mediana`.
   - Senão → revert fiel (passo 6).
8. **Contadores**: não-aceite → `PLATÔ++` (5 → FIM); falha de execução → `PLATÔ++` e `FALHAS++` (3 → FIM); aceite → `PLATÔ=0`. Objetivo: após aceite, `|melhor_aceito − baseline| ≥ objetivo` → FIM "objetivo atingido". Precedência do motivo: FALHAS > PLATÔ > tempo > objetivo.
9. **Re-derivar T** a cada 3 rodadas: `T = 2 × pior D_run das últimas 6`; monotônico-não-decrescente; teto `4 × T0`. Logue a mudança.

## FIM

1. Voltar: `git checkout $ORIGINAL_BRANCH` (`-f` só com resíduo conhecido) ou `git checkout $ORIGINAL_SHA`.
2. `STASHED=1` → `git stash pop --index`; conflito → `mv <path> <path>.karpathy-backup` → pop → informe o backup.
3. `RESIDUO=1` → informe o stash de resíduo deixado.
4. **Relatório final**:
   - Caminho do `karpathy-results.md`.
   - Baseline vs. melhor: **delta absoluto sempre**; `%` só se baseline ≠ 0.
   - Rodadas executadas + motivo do FIM.
   - Hashes dos commits mantidos (branch `karpathy/<slug>`).
   - Opções para o usuário: manter a branch (merge manual) ou apagar tudo: `git branch -D karpathy/<slug>` + `git reset --hard $BASELINE_SHA` — **somente com aprovação explícita**.
