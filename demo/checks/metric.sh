#!/usr/bin/env bash
# JUIZ IMUTÁVEL do demo — não edite durante um loop.
# Imprime EXATAMENTE 1 número no stdout: quantas funções de demo_target.py
# têm mais de 20 linhas (do "def" até o fim do corpo).
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="$SCRIPT_DIR/../demo_target.py"

awk '
/^[[:space:]]*(async[[:space:]]+)?def[[:space:]]+/ {
    # indentação do def
    match($0, /[^[:space:]]/)
    def_indent[def_n++] = RSTART - 1
    body[def_n-1] = 0
    next
}
{
    if (def_n == 0) next
    line = $0
    if (line ~ /^[[:space:]]*$/) {           # linha em branco pertence ao corpo aberto
        for (i = 0; i < def_n; i++) body[i]++
        next
    }
    match(line, /[^[:space:]]/)
    ind = RSTART - 1
    # fecha todas as funções cuja indentação >= ind
    while (def_n > 0 && def_indent[def_n-1] >= ind) {
        def_n--
        if (body[def_n] > 20) count++
    }
    for (i = 0; i < def_n; i++) body[i]++
}
END {
    while (def_n > 0) { def_n--; if (body[def_n] > 20) count++ }
    print count + 0
}
' "$TARGET"
