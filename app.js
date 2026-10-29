// Gerenciador de simulação da interface do Anti-Mule-Account-Engine
document.addEventListener('DOMContentLoaded', () => {
    console.log('Sistema de simulação antifraude iniciado.');

    // Mapeamento dos elementos da interface
    const btnSimular = document.getElementById('btn-simular') || document.querySelector('button');
    const selectStatus = document.getElementById('status-conta');
    const painelResultado = document.getElementById('resultado-analise');

    if (btnSimular) {
        btnSimular.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Força a validação visual do clique
            btnSimular.innerText = 'Processando...';
            btnSimular.disabled = true;

            setTimeout(() => {
                // Simulação da lógica de detecção contida no main.py
                const scoreRisco = Math.floor(Math.random() * 100);
                let decisao = 'APROVADO';
                let flagErro = 'NENHUMA';

                if (scoreRisco > 70) {
                    decisao = 'BLOQUEADO (Conta Laranja Suspeita)';
                    flagErro = 'FLUXO_RAPIDO_DETECTADO';
                }

                // Injeta o resultado diretamente no elemento de output da tela
                if (painelResultado) {
                    painelResultado.innerHTML = `
                        <div style="padding: 15px; border-radius: 5px; background-color: ${scoreRisco > 70 ? '#ffcccc' : '#ccffcc'}; color: #000;">
                            <strong>Resultado da Análise:</strong> ${decisao}<br>
                            <strong>Score de Risco:</strong> ${scoreRisco}/100<br>
                            <strong>Vulnerabilidade/Gargalo:</strong> ${flagErro}
                        </div>
                    `;
                }

                // Restaura o botão
                btnSimular.innerText = 'Simular Transação';
                btnSimular.disabled = false;
            }, 800);
        });
    }
});
