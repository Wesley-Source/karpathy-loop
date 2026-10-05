"""Alvo propositalmente SUBÓTIMO do demo do karpathy loop.

O juiz (checks/metric.sh) imprime quantas funções deste arquivo têm
mais de 20 linhas. Há 4 funções longas de propósito — a skill deve
reduzi-las (extrair helpers, reescrever em comprehensions etc.) sem
jamais tocar em checks/.
"""


def processa_vendas_brutas(vendas):
    """Linha por linha, sem comprehension — propositalmente > 20 linhas."""
    total = 0
    relatorio = []
    for venda in vendas:
        if venda["valor"] <= 0:
            continue
        valor = venda["valor"]
        if venda["categoria"] == "eletronico":
            imposto = valor * 0.18
        elif venda["categoria"] == "alimento":
            imposto = valor * 0.07
        elif venda["categoria"] == "servico":
            imposto = valor * 0.12
        else:
            imposto = valor * 0.10
        desconto = 0.0
        if valor > 1000:
            desconto = valor * 0.05
        elif valor > 500:
            desconto = valor * 0.03
        elif valor > 100:
            desconto = valor * 0.01
        liquido = valor - desconto + imposto
        total += liquido
        relatorio.append(
            {
                "id": venda["id"],
                "bruto": valor,
                "desconto": desconto,
                "imposto": imposto,
                "liquido": liquido,
                "categoria": venda["categoria"],
            }
        )
    return total, relatorio


def normaliza_nomes_clientes(clientes):
    """Limpeza de nomes com if/else redundantes — propositalmente > 20 linhas."""
    resultado = []
    for cliente in clientes:
        nome = cliente["nome"]
        nome = nome.strip()
        while "  " in nome:
            nome = nome.replace("  ", " ")
        partes = nome.split(" ")
        novas_partes = []
        for parte in partes:
            if parte == "":
                continue
            if parte in ("de", "da", "do", "das", "dos", "e"):
                novas_partes.append(parte.lower())
            else:
                novas_partes.append(parte.capitalize())
        nome = " ".join(novas_partes)
        if cliente.get("sufixo"):
            nome = nome + " " + cliente["sufixo"].upper()
        resultado.append({"id": cliente["id"], "nome": nome})
    return resultado


def calcula_frete_por_regiao(pedidos):
    """Cadeia gigante de elif por região — propositalmente > 20 linhas."""
    fretes = []
    for pedido in pedidos:
        peso = pedido["peso_kg"]
        regiao = pedido["regiao"]
        if regiao == "norte":
            if peso < 5:
                frete = 25.0
            elif peso < 10:
                frete = 40.0
            elif peso < 20:
                frete = 60.0
            else:
                frete = 60.0 + (peso - 20) * 3.0
        elif regiao == "nordeste":
            if peso < 5:
                frete = 22.0
            elif peso < 10:
                frete = 36.0
            elif peso < 20:
                frete = 55.0
            else:
                frete = 55.0 + (peso - 20) * 2.8
        elif regiao == "sudeste":
            if peso < 5:
                frete = 12.0
            elif peso < 10:
                frete = 18.0
            elif peso < 20:
                frete = 28.0
            else:
                frete = 28.0 + (peso - 20) * 1.5
        elif regiao == "sul":
            if peso < 5:
                frete = 15.0
            elif peso < 10:
                frete = 22.0
            elif peso < 20:
                frete = 33.0
            else:
                frete = 33.0 + (peso - 20) * 1.8
        else:
            if peso < 5:
                frete = 20.0
            elif peso < 10:
                frete = 30.0
            elif peso < 20:
                frete = 45.0
            else:
                frete = 45.0 + (peso - 20) * 2.2
        fretes.append({"id": pedido["id"], "frete": round(frete, 2)})
    return fretes


def gera_log_textual(eventos):
    """Concatenação de string em loop + ifs aninhados — propositalmente > 20 linhas."""
    log = ""
    for evento in eventos:
        if evento["tipo"] == "erro":
            log = log + "[ERRO] "
            log = log + evento["timestamp"] + " "
            log = log + evento["mensagem"] + "\n"
        elif evento["tipo"] == "aviso":
            if evento.get("codigo"):
                log = log + "[AVISO " + str(evento["codigo"]) + "] "
            else:
                log = log + "[AVISO] "
            log = log + evento["timestamp"] + " "
            log = log + evento["mensagem"] + "\n"
        elif evento["tipo"] == "info":
            log = log + "[INFO] "
            log = log + evento["timestamp"] + " "
            log = log + evento["mensagem"] + "\n"
        else:
            log = log + "[???] "
            log = log + evento["timestamp"] + " "
            log = log + "evento desconhecido: " + str(evento) + "\n"
    return log
