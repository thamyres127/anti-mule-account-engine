# Anti-Mule Account Engine 🛡️💰

Um simulador de **Core Banking** de alta performance com um motor antifraude integrado focado na detecção de "contas laranjas" (*mule accounts*) em transações PIX. Desenvolvido para mitigar fraudes bancárias de evasão rápida através de análise de risco comportamental em tempo real.

---

## 🛠️ Tecnologias Utilizadas
* **Back-end:** Python 3 (Flask para gerenciamento de microserviços e rotas de API)
* **Banco de Dados:** SQLite (Banco de dados relacional para persistência de contas e auditoria de logs)
* **Front-end:** HTML5, CSS3, JavaScript Avançado (Modo Demonstração nativo e responsivo para execução em ambientes web/GitHub Pages)
* **Segurança:** Regras de negócio e motores de score baseados em conformidade bancária e PLD (Prevenção à Lavagem de Dinheiro).

---

## 🧠 Regras do Motor Antifraude (Score de Risco)
O sistema analisa três vetores críticos de dados antes de aprovar uma transferência de saída:
1. **Idade da Conta:** Contas abertas há menos de 15 dias recebem **+40 pontos** de risco de forma preventiva.
2. **Estouro de Perfil:** Movimentações acima de 500% do limite histórico do cliente disparam **+35 pontos** de risco.
3. **Velocidade de Evasão Rápida:** Tentativas de pulverizar ou esvaziar o saldo em menos de 30 segundos após a chegada de um PIX disparam **+45 pontos** de risco.

> 🚨 **Tomada de Decisão:** Caso o Score de Risco atinja ou ultrapasse **70 pontos**, o sistema aciona automaticamente a **Retenção Preventiva de 30 minutos**, bloqueando o valor e salvando a transação com o status `RETIDA_PARA_ANALISE` no banco SQL para auditoria.

---

## 🚀 Como Executar o Projeto

### 1. Clonar o Repositório
```bash
git clone https://github.com
cd anti-mule-account-engine
```

### 2. Iniciar o Back-end (API + Banco de Dados SQL)
Certifique-se de ter o Python e o Flask instalados:
```bash
python main.py
```
*O arquivo `core_banking.db` será criado e populado automaticamente na primeira execução.*

### 3. Execução Online
Abra o arquivo `index.html` em qualquer navegador. O front-end possui um **Modo Demonstração automático** integrado para simular e testar os cenários de fraude diretamente na nuvem (GitHub Pages) mesmo com a API local desconectada.
