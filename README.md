# Karpathy Loop

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Skill de agente (Hermes Agent / OpenCode / Claude Code) que implementa um **loop de otimização estilo Karpathy**: melhora uma métrica mensurável de um alvo por tempo limitado, com **juiz imutável**, **builder descartável** por rodada, **mediana de 3 execuções** e **revert automático** do que não melhora de verdade.

## O problema que resolve

Quando você pede a um agente de código que "melhore X", ele tem um conflito de interesses estrutural: **quem edita o código é quem mede o próprio resultado**. Sob pressão para mostrar progresso, agentes "melhoram" a métrica fraudando — editam o script de teste para fazer o número cair, apagam warnings desligando o lint, ajustam a métrica em vez do alvo.

O Karpathy Loop separa os dois papéis à força:

- **Juiz (imutável):** `checks/metric.sh` — um script que imprime **exatamente 1 número** no stdout. O agente principal o executa, decide aceite/revert e guarda o estado. É o *único* who mede — e **não pode ser editado**: qualquer mudança sob `checks/` durante o loop é violação estrutural → aborto imediato.
- **Builder (descartável):** um subagente criado do zero a cada rodada, sem memória da conversa. Faz **exatamente uma** mudança pequena (máx. 1 arquivo ou ~30 linhas), **nunca toca em `checks/`**, nunca roda a métrica nem commita — só edita. Depois é jogado fora. Sem memória herdada, não há viés acumulado nem racionalização de rodadas anteriores.

Com quem edita separado de quem mede, e com o juiz fora do alcance do otimizador, a única forma de o número melhorar é o alvo melhorar de verdade.

## Anatomia do loop

```
                    ┌──────────────────────────────────────────────┐
                    │              AGENTE PRINCIPAL (JUIZ)          │
                    │        persistente — orquestra e decide       │
                    └──────────────────────────────────────────────┘
                        │                             ▲
                        │ cria subagente novo         │ edita e volta
                        │ por rodada (task)           │
                        ▼                             │
                    ┌───────────────┐                 │
   a cada rodada    │    BUILDER    │─────────────────┘
                    │  descartável  │   UMA mudança pequena,
                    └───────────────┘   JAMAIS sob checks/

  ┌─────────────────────────────────────────────────────────────┐
  │  Loop (máx. 20 rodadas, tempo limitado):                    │
  │                                                             │
  │   ┌─────────────────────────────────────────────────┐       │
  │   │ 1. builder faz UMA mudança (não toca em checks/) │       │
  │   │ 2. juiz audita o diff (escopo + checks/ intato)  │       │
  │   │ 3. juiz mede: bash checks/metric.sh  × 3         │       │
  │   │ 4. mediana das 3; melhora > ε (ruído)?           │       │
  │   │       sim → commit  (melhor_aceito = mediana)    │       │
  │   │       não → revert fiel do que o builder fez     │       │
  │   │ 5. log append-only em karpathy-results.md        │       │
  │   └─────────────────────────────────────────────────┘       │
  │                                                             │
  │  FIM → checkout da branch original + relatório              │
  │        baseline vs. melhor (delta absoluto e %)             │
  └─────────────────────────────────────────────────────────────┘
```

Garantias da arquitetura:

- **Juiz imutável:** `git diff --quiet $BASELINE_SHA -- checks/` a cada rodada; sujo → aborto.
- **Mediana de 3 execuções** com piso de ruído (ε = máx de 2% do melhor, spread da rodada, spread histórico) — ruído não vira "melhora".
- **Revert automático** de toda rodada que não melhora; só commits de melhora real ficam na branch `karpathy/<slug>`.
- **Tudo em branch dedicada** — seu checkout original é restaurado no fim, com relatório baseline vs. melhor.
- **Máx. 20 rodadas**, terminação por: objetivo atingido, 5 rodadas em platô, 3 falhas de execução ou tempo esgotado.

## Instalação

### Hermes Agent

Copie a skill para o diretório de skills do perfil:

```bash
git clone https://github.com/Wesley-Source/karpathy-loop
mkdir -p ~/.hermes/skills/karpathy-loop
cp karpathy-loop/SKILL.md ~/.hermes/skills/karpathy-loop/SKILL.md
```

> Ajuste o caminho se você usa um perfil nomeado (ex.: `~/.hermes/profiles/<nome>/skills/`).
> A skill fica disponível automaticamente na próxima sessão — liste com `skills_list` ou invoque diretamente com `skill_view(name='karpathy-loop')`.

### OpenCode

Registre a skill no array `skills` da configuração (`opencode.json` ou `~/.config/opencode/config.json`):

```bash
git clone https://github.com/Wesley-Source/karpathy-loop ~/.config/opencode/skills/karpathy-loop
```

```jsonc
// opencode.json
{
  "skills": [
    { "name": "karpathy-loop", "path": "~/.config/opencode/skills/karpathy-loop/SKILL.md" }
  ]
}
```

### Claude Code

Copie para o diretório de skills do projeto (ou `~/.claude/skills` para todos os projetos):

```bash
git clone https://github.com/Wesley-Source/karpathy-loop
mkdir -p .claude/skills/karpathy-loop
cp karpathy-loop/SKILL.md .claude/skills/karpathy-loop/SKILL.md
```

### Windows

- **Hermes Agent (PowerShell):**

```powershell
git clone https://github.com/Wesley-Source/karpathy-loop "$env:USERPROFILE\.hermes\skills\karpathy-loop"
# se já clonou em outro lugar:
# Copy-Item karpathy-loop\SKILL.md "$env:USERPROFILE\.hermes\skills\karpathy-loop\SKILL.md"
```

- **OpenCode (PowerShell):** clone para `%USERPROFILE%\.config\opencode\skills\karpathy-loop` e adicione a entrada no array `skills` do `opencode.json` como acima (use o caminho Windows completo no `path`).
- **Claude Code (PowerShell):**

```powershell
git clone https://github.com/Wesley-Source/karpathy-loop
New-Item -ItemType Directory -Force "$PWD\.claude\skills\karpathy-loop" | Out-Null
Copy-Item karpathy-loop\SKILL.md ".claude\skills\karpathy-loop\SKILL.md"
```

Requisito: **Git for Windows** e um **bash** no PATH (Git Bash já vem com o Git for Windows) — os juízes são `metric.sh` executados com `bash`.

## Uso

Peça em linguagem natural, sempre com alvo, direção e duração:

> "Rode o karpathy loop para melhorar o tempo de build em 20 minutos, minimize"

```
Você: melhorar o tempo de build em 20 minutos, minimize
Skill: 1) grava exclusões e cria a branch karpathy/build-time
       2) commita o estado atual → karpathy baseline (BASELINE_SHA)
       3) valida checks/metric.sh e mede o baseline (mediana de 3)
       4) loop: builder descartável edita → juiz mede → aceita ou reverte
       5) FIM: volta para sua branch e reporta baseline vs. melhor
```

Exemplo de relatório final:

```
karpathy-results.md — run 20260105T1200
Baseline: 247.3s (mediana de 3, spread 1.1)
Melhor:   203.8s
Delta:    −43.5s (−17.6%) em 12 rodadas (9 aceites, 3 reverts)
FIM: tempo esgotado
Branch: karpathy/build-time — commits: a1b2c3d, e4f5a6b, ...
```

Se `checks/metric.sh` ainda não existe no seu repo, a skill ajuda você a escrevê-lo (deve imprimir exatamente 1 número) e pede sua aprovação antes de começar.

## Demo

`demo/` contém um exemplo mínimo e rodável: `checks/metric.sh` conta funções com mais de 20 linhas em `demo_target.py` (código propositalmente subótimo) e imprime **exatamente 1 número**. Veja [demo/README.md](demo/README.md).

```bash
cd demo && bash checks/metric.sh   # → ex.: 4
```

## Licença

[MIT](LICENSE) © Wesley Carlos Nascimento
