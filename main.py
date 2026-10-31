import sqlite3
import time
from datetime import datetime, timedelta
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # Permite conexões do front-end sem problemas de segurança

def iniciar_banco():
    """Cria o banco de dados SQL e insere os dados iniciais se não existirem"""
    conn = sqlite3.connect('core_banking.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS contas (
            id TEXT PRIMARY KEY,
            titular TEXT,
            data_criacao TEXT,
            saldo REAL,
            limite_historico REAL
        )
    ''')

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

    cursor.execute("SELECT COUNT(*) FROM contas")
    if cursor.fetchone() == 0:
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

@app.route('/api/registrar-entrada', methods=['POST'])
def api_registrar_entrada():
    """Rota da API para simular a chegada de um PIX"""
    dados = request.get_json()
    conta_id = dados.get('conta_id')
    valor = dados.get('valor', 0.0)
    
    conta = buscar_conta(conta_id)
    if not conta:
        return jsonify({"status": "ERRO", "mensagem": "Conta inválida"}), 400
    
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
    
    return jsonify({
        "transacao_id": tx_id,
        "status": "CONCLUIDO",
        "score_risco": 0
    })

@app.route('/api/processar-saida', methods=['POST'])
def api_processar_saida():
    """Rota da API para o Motor Antifraude analisar a transferência de saída"""
    dados = request.get_json()
    conta_origem = dados.get('conta_origem')
    conta_destino = dados.get('conta_destino')
    valor = dados.get('valor', 0.0)
    
    conta_orig = buscar_conta(conta_origem)
    conta_dest = buscar_conta(conta_destino)
    
    if not conta_orig or not conta_dest:
        return jsonify({"status": "ERRO", "mensagem": "Contas inválidas"}), 400
    
    timestamp_atual = datetime.now()
    
    if conta_orig["saldo"] < valor:
        return jsonify({"status": "SALDO_INSUFICIENTE", "score_risco": 0, "transacao_id": "N/A"}), 200
    
    # --- MOTOR DE REGRAS ANTI-MULE (SCORE DE RISCO) ---
    score_risco = 0
    motivos_bloqueio = []
    
    data_criacao = datetime.strptime(conta_orig["data_criacao"], "%Y-%m-%d")
    idade_conta_dias = (timestamp_atual - data_criacao).days
    if idade_conta_dias < 15:
        score_risco += 40
        motivos_bloqueio.append(f"Conta Nova ({idade_conta_dias} dias)")
        
    if valor > (conta_orig["limite_historico"] * 5):
        score_risco += 35
        motivos_bloqueio.append("Estouro de Perfil Histórico")
        
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
            motivos_bloqueio.append(f"Velocidade de Evasão Rápida ({int(diferenca_segundos)}s)")

    # --- TOMADA DE DECISÃO ---
    tx_id = f"TX_OUT_{int(time.time())}"
    status_final = "CONCLUIDO"
    
    if score_risco >= 70:
        status_final = "RETIDA_PARA_ANALISE"
        atualizar_saldo(conta_origem, conta_orig["saldo"] - valor) 
    else:
        atualizar_saldo(conta_origem, conta_orig["saldo"] - valor)
        atualizar_saldo(conta_destino, conta_dest["saldo"] + valor)

    conn = sqlite3.connect('core_banking.db')
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transacoes (transacao_id, conta_origem, conta_destino, tipo, valor, timestamp, status, score_risco)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (tx_id, conta_origem, conta_destino, "SAIDA", valor, timestamp_atual.strftime("%Y-%m-%d %H:%M:%S"), status_final, score_risco))
    conn.commit()
    conn.close()
    
    return jsonify({
        "transacao_id": tx_id,
        "status": status_final,
        "score_risco": score_risco,
        "motivos": motivos_bloqueio
    })

if __name__ == "__main__":
    iniciar_banco()
    app.run(port=5000, debug=True)
