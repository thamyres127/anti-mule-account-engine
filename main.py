import sqlite3
import time
from datetime import datetime, timedelta

def iniciar_banco():
    """Cria o banco de dados SQL e insere os dados iniciais se não existirem"""
    conn = sqlite3.connect('core_banking.db')
    cursor = conn.cursor()

    # 1. Cria a tabela de Contas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contas (
            id TEXT PRIMARY KEY,
            titular TEXT,
            data_criacao TEXT,
            saldo REAL,
            limite_historico REAL
        )
    ''')

    # 2. Cria a tabela de Transações
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacoes (
            transacao_id TEXT PRIMARY KEY,
            conta_origem TEXT,
            conta_destino TEXT,
            tipo TEXT,
            valor REAL,
            timestamp TEXT,
            status TEXT,
            score_risco INTEGER DEFAULT 0
        )
    ''')

    # 3. Insere os dados iniciais se a tabela estiver vazia
    cursor.execute("SELECT COUNT(*) FROM contas")
    if cursor.fetchone()[0] == 0:
        data_laranja = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
        contas_iniciais = [
            ("127001", "Conta Laranja Suspeita", data_laranja, 0.0, 200.0),
            ("127002", "Cliente Antigo Confiável", "2024-01-15", 50000.0, 10000.0),
            ("127003", "Conta Destino Final", "2025-06-20", 10.0, 500.0)
        ]
        cursor.executemany("INSERT INTO contas VALUES (?, ?, ?, ?, ?)", contas_iniciais)
        conn.commit()
        print("[SQL] Banco de dados inicializado com sucesso!")
        
    conn.close()

def buscar_conta(conta_id):
    """Busca os dados de uma conta no SQL e retorna como um dicionário"""
    conn = sqlite3.connect('core_banking.db')
    cursor = conn.cursor()
    cursor.execute("SELECT titular, data_criacao, saldo, limite_historico FROM contas WHERE id = ?", (conta_id,))
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "titular": row[0],
            "data_criacao": row[1],
            "saldo": row[2],
            "limite_historico": row[3]
        }
    return None

def atualizar_saldo(conta_id, novo_saldo):
    """Atualiza o saldo de uma conta direto no SQL"""
    conn = sqlite3.connect('core_banking.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE contas SET saldo = ? WHERE id = ?", (novo_saldo, conta_id))
    conn.commit()
    conn.close()

def registrar_entrada_pix(conta_id, valor):
    """Simula a chegada de um PIX na conta do cliente salvando no SQL"""
    conta = buscar_conta(conta_id)
    if not conta:
        return False
    
    novo_saldo = conta["saldo"] + valor
    atualizar_saldo(conta_id, novo_saldo)
    
    timestamp_atual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tx_id = f"TX_IN_{int(time.time())}"
    
    conn = sqlite3.connect('core_banking.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transacoes (transacao_id, conta_origem, conta_destino, tipo, valor, timestamp, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, "BANCO_EXTERNO", conta_id, "ENTRADA", valor, timestamp_atual, "CONCLUIDO"))
    conn.commit()
    conn.close()
    
    print(f"[SISTEMA CORE] Entrada de R$ {valor:.2f} processada na conta {conta_id} às {timestamp_atual}.")
    return True

def avaliar_e_processar_saida(conta_origem, conta_destino, valor):
    """Motor Anti-Mule operando direto com consultas e comandos SQL"""
    conta_orig = buscar_conta(conta_origem)
    conta_dest = buscar_conta(conta_destino)
    
    if not conta_orig or not conta_dest:
        print("[ERRO] Conta de origem ou destino inválida.")
        return "ERRO"
    
    timestamp_atual = datetime.now()
    
    if conta_orig["saldo"] < valor:
        print("[BLOCK] Saldo insuficiente.")
        return "SALDO_INSUFICIENTE"
    
    # --- MOTOR DE REGRAS ANTI-MULE (SCORE DE RISCO) ---
    score_risco = 0
    motivos_bloqueio = []
    
    # Regra 1: Idade da Conta
    data_criacao = datetime.strptime(conta_orig["data_criacao"], "%Y-%m-%d")
    idade_conta_dias = (timestamp_atual - data_criacao).days
    if idade_conta_dias < 15:
        score_risco += 40
        motivos_bloqueio.append(f"Conta Nova ({idade_conta_dias} dias de existência)")
        
    # Regra 2: Estouro do Perfil Histórico
    if valor > (conta_orig["limite_historico"] * 5):
        score_risco += 35
        motivos_bloqueio.append(f"Estouro de Perfil (Tentativa de R$ {valor:.2f} para limite histórico de R$ {conta_orig['limite_historico']:.2f})")
        
    # Regra 3: Fator Tempo / Velocidade de Evasão (Buscando última entrada no SQL)
    conn = sqlite3.connect('core_banking.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT timestamp FROM transacoes 
        WHERE conta_destino = ? AND tipo = 'ENTRADA' 
        ORDER BY timestamp DESC LIMIT 1
    """, (conta_origem,))
    row_tx = cursor.fetchone()
    conn.close()
            
    if row_tx:
        ts_entrada = datetime.strptime(row_tx[0], "%Y-%m-%d %H:%M:%S")
        diferenca_segundos = (timestamp_atual - ts_entrada).total_seconds()
        
        if diferenca_segundos < 30:
            score_risco += 45
            motivos_bloqueio.append(f"Alta Velocidade de Evasão ({int(diferenca_segundos)} segundos após a entrada)")

    # --- TOMADA DE DECISÃO BANCÁRIA ---
    tx_id = f"TX_OUT_{int(time.time())}"
    status_final = "CONCLUIDO"
    
    if score_risco >= 70:
        status_final = "RETIDA_PARA_ANALISE"
        atualizar_saldo(conta_origem, conta_orig["saldo"] - valor) 
        print(f"\n[🚨 ALERTA MOTOR ANTI-MULE] SUSPEITA DETECTADA NA CONTA {conta_origem}!")
        print(f"[SCORE DE RISCO]: {score_risco} PONTOS (CRÍTICO)")
        print("[MOTIVOS]:")
        for motivo in motivos_bloqueio:
            print(f"  -> {motivo}")
        print(f"[AÇÃO CORE BANKING]: Transação {tx_id} retida preventivamente por 30 minutos.")
    else:
        atualizar_saldo(conta_origem, conta_orig["saldo"] - valor)
        atualizar_saldo(conta_destino, conta_dest["saldo"] + valor)
        print(f"\n[SISTEMA CORE] Transação {tx_id} concluída com sucesso de {conta_origem} para {conta_destino}.")

    # Salva o log de auditoria da transação no banco SQL
    conn = sqlite3.connect('core_banking.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transacoes (transacao_id, conta_origem, conta_destino, tipo, valor, timestamp, status, score_risco)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, conta_origem, conta_destino, "SAIDA", valor, timestamp_atual.strftime("%Y-%m-%d %H:%M:%S"), status_final, score_risco))
    conn.commit()
    conn.close()
    
    return status_final

def mostrar_status_banco_sql():
    """Exibe no console o estado atual das contas armazenadas no arquivo SQL"""
    conn = sqlite3.connect('core_banking.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, titular, data_criacao, saldo, limite_historico FROM contas")
    rows = cursor.fetchall()
    conn.close()
    
    print("\n=== STATUS ATUAL DAS CONTAS NO BANCO DE DADOS (SQL) ===")
    for row in rows:
        print(f"Conta: {row[0]} | Titular: {row[1]:<25} | Saldo: R$ {row[3]:,.2f}")

# --- EXECUÇÃO DO FLUXO DO CORE BANKING ---
if __name__ == "__main__":
    print("=== INICIANDO SIMULADOR CORE BANKING: MOTOR ANTI-MULE COM SQLITE ===")
    iniciar_banco()
    
    # Cenário 1: Fluxo Rápido em Conta Laranja (Conta 127001)
    print("\n--- PASSO 1: Depósito de dinheiro roubado na conta laranja via PIX ---")
    registrar_entrada_pix("127001", 15000.0)
    
    print("\n--- PASSO 2: 3 segundos depois, tentativa de pulverização do valor ---")
    time.sleep(3)
    avaliar_e_processar_saida("127001", "127003", 15000.0)
    
    # Cenário 2: Transação Normal de Cliente Antigo (Conta 127002)
    print("\n--- PASSO 3: Cliente antigo movimentando valor dentro do perfil ---")
    avaliar_e_processar_saida("127002", "127003", 500.0)
    
    # Exibe o resultado final lido direto do banco de dados relacional
    mostrar_status_banco_sql()
