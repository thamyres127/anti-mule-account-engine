import json
import time
from datetime import datetime, timedelta

# Simulador de Banco de Dados Relacional (Arquivos JSON em Memória)
DB_CONTAS = {
    "127001": {
        "titular": "Conta Laranja Suspeita",
        "data_criacao": (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d"), # Conta nova (5 dias)
        "saldo": 0.0,
        "limite_historico": 200.0 # Perfil de baixa movimentação
    },
    "127002": {
        "titular": "Cliente Antigo Confiável",
        "data_criacao": "2024-01-15", # Conta antiga
        "saldo": 50000.0,
        "limite_historico": 10000.0
    },
    "127003": {
        "titular": "Conta Destino Final",
        "data_criacao": "2025-06-20",
        "saldo": 10.0,
        "limite_historico": 500.0
    }
}

DB_TRANSACOES = []

def registrar_entrada_pix(conta_id, valor):
    """Simula a chegada de um PIX na conta do cliente"""
    if conta_id not in DB_CONTAS:
        return False
    
    DB_CONTAS[conta_id]["saldo"] += valor
    timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Padronizado: entrada usa conta_destino como a conta que está recebendo
    DB_TRANSACOES.append({
        "transacao_id": f"TX_IN_{int(time.time())}",
        "conta_origem": "BANCO_EXTERNO",
        "conta_destino": conta_id,
        "tipo": "ENTRADA",
        "valor": valor,
        "timestamp": timestamp_atual,
        "status": "CONCLUIDO"
    })
    print(f"[SISTEMA CORE] Entrada de R$ {valor:.2f} processada na conta {conta_id} às {timestamp_atual}.")
    return True

def avaliar_e_processar_saida(conta_origem, conta_destino, valor):
    """
    Motor Anti-Mule (Anti-Contas Laranja).
    Aplica as regras de negócio baseadas em tempo, perfil e idade da conta.
    """
    if conta_origem not in DB_CONTAS or conta_destino not in DB_CONTAS:
        print("[ERRO] Conta de origem ou destino inválida.")
        return "ERRO"
    
    conta = DB_CONTAS[conta_origem]
    timestamp_atual = datetime.now()
    
    # Validação de Saldo Básico
    if conta["saldo"] < valor:
        print("[BLOCK] Saldo insuficiente.")
        return "SALDO_INSUFICIENTE"
    
    # --- MOTOR DE REGRAS ANTI-MULE (SCORE DE RISCO) ---
    score_risco = 0
    motivos_bloqueio = []
    
    # Regra 1: Idade da Conta (Contas com menos de 15 dias são críticas)
    data_criacao = datetime.strptime(conta["data_criacao"], "%Y-%m-%d")
    idade_conta_dias = (timestamp_atual - data_criacao).days
    if idade_conta_dias < 15:
        score_risco += 40
        motivos_bloqueio.append(f"Conta Nova ({idade_conta_dias} dias de existência)")
        
    # Regra 2: Estouro do Perfil Histórico (Valor acima de 500% do limite histórico)
    if valor > (conta["limite_historico"] * 5):
        score_risco += 35
        motivos_bloqueio.append(f"Estouro de Perfil (Tentativa de R$ {valor:.2f} para limite histórico de R$ {conta['limite_historico']:.2f})")
        
    # Regra 3: Fator Tempo / Velocidade de Evasão (Dinheiro entrou e já está saindo correndo)
    # Busca a última transação de entrada onde esta conta foi o destino
    ultima_entrada = None
    for tx in reversed(DB_TRANSACOES):
        if tx["conta_destino"] == conta_origem and tx["tipo"] == "ENTRADA":
            ultima_entrada = tx
            break
            
    if ultima_entrada:
        ts_entrada = datetime.strptime(ultima_entrada["timestamp"], "%Y-%m-%d %H:%M:%S")
        diferenca_segundos = (timestamp_atual - ts_entrada).total_seconds()
        
        # Se tentar esvaziar a conta em menos de 30 segundos após receber o dinheiro
        if diferenca_segundos < 30:
            score_risco += 45
            motivos_bloqueio.append(f"Alta Velocidade de Evasão ({int(diferenca_segundos)} segundos após a entrada)")

    # --- TOMADA DE DECISÃO BANCÁRIA ---
    tx_id = f"TX_OUT_{int(time.time())}"
    status_final = "CONCLUIDO"
    
    # Se o score de risco passar de 70 pontos, o sistema aplica a Retenção Preventiva de 30 minutos
    if score_risco >= 70:
        status_final = "RETIDA_PARA_ANALISE"
        # Bloqueia temporariamente o valor do saldo do cliente no core
        conta["saldo"] -= valor 
        print(f"\n[🚨 ALERTA MOTOR ANTI-MULE] DEMÊNCIA DETECTADA NA CONTA {conta_origem}!")
        print(f"[SCORE DE RISCO]: {score_risco} PONTOS (CRÍTICO)")
        print("[MOTIVOS]:")
        for motivo in motivos_bloqueio:
            print(f"  -> {motivo}")
        print(f"[AÇÃO CORE BANKING]: Transação {tx_id} retida preventivamente por 30 minutos.")
    else:
        # Transação legítima segue o fluxo normal
        conta["saldo"] -= valor
        DB_CONTAS[conta_destino]["saldo"] += valor
        print(f"\n[SISTEMA CORE] Transação {tx_id} concluída com sucesso de {conta_origem} para {conta_destino}.")

    # Registra no histórico de auditoria usando as chaves padronizadas
    DB_TRANSACOES.append({
        "transacao_id": tx_id,
        "conta_origem": conta_origem,
        "conta_destino": conta_destino,
        "tipo": "SAIDA",
        "valor": valor,
        "timestamp": timestamp_atual.strftime("%Y-%m-%d %H:%M:%S"),
        "status": status_final,
        "score_risco": score_risco
    })
    
    return status_final

# --- SIMULAÇÃO PRÁTICA DO CENÁRIO DE FRAUDE ---
if __name__ == "__main__":
    print("=== INICIANDO SIMULADOR CORE BANKING: MOTOR ANTI-MULE ===")
    
    # Cenário 1: Tentativa de Fraude por Efeito Fluxo Rápido em Conta Laranja (Conta 127001)
    print("\n--- PASSO 1: Criminosos depositam dinheiro roubado na conta laranja ---")
    registrar_entrada_pix("127001", 15000.0) # Recebe R$ 15k de repente
    
    print("\n--- PASSO 2: 3 segundos depois, tentam pulverizar o dinheiro para outra conta ---")
    time.sleep(3) # Simula delay de 3 segundos
    avaliar_e_processar_saida("127001", "127003", 15000.0)
    
    # Cenário 2: Transação Normal de Cliente Antigo (Conta 127002)
    print("\n\n--- PASSO 3: Cliente antigo movimentando valor dentro do perfil ---")
    avaliar_e_processar_saida("127002", "127003", 500.0)
    
    print("\n=== STATUS FINAL DAS CONTAS EM MEMÓRIA (JSON) ===")
    print(json.dumps(DB_CONTAS, indent=4, ensure_ascii=False))
