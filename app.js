// Gerenciador de simulação da interface do Anti-Mule-Account-Engine
document.addEventListener('DOMContentLoaded', () => {
    console.log('Sistema de simulação antifraude iniciado com suporte a Modo Demonstração.');

    // Mapeamento dos elementos da interface baseados na sua tela
    const btnInjetarPix = document.getElementById('btn-injetar-pix') || document.querySelector('.btn-primary') || document.querySelectorAll('button')[0];
    const btnForcarEvasao = document.getElementById('btn-forcar-evasao') || document.querySelector('.btn-danger') || document.querySelectorAll('button')[1];
    const btnSimularLegitima = document.getElementById('btn-simular-legitima') || document.querySelector('.btn-secondary') || document.querySelectorAll('button')[2];
    const painelResultado = document.getElementById('resultado-analise');

    // Elementos de saldo para atualizar na tela visualmente
    const saldos = document.querySelectorAll('h2, .saldo, [style*="color: rgb(0, 255, 0)"], [style*="color: #00ff00"]');

    // Função única para enviar a ação do front-end para o back-end (Python/SQL) ou rodar local
    async function processarSimulacao(endpoint, dados, botao) {
        const textoOriginal = botao.innerText;
        botao.innerText = 'Processando...';
        botao.disabled = true;

        if (painelResultado) {
            painelResultado.innerHTML = '<div style="padding: 15px; color: #fff;">Analisando transação no Core Banking...</div>';
        }

        try {
            // Tenta conectar com a API em Python
            const response = await fetch(`http://127.0.0{endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dados)
            });

            const resultado = await response.json();
            exibirResultado(resultado);

        } catch (error) {
            console.log('Servidor Python offline. Executando simulação local no Modo Demonstração...');
            
            // EXECUÇÃO LOCAL (Para o recrutador ver o funcionamento no GitHub Pages)
            setTimeout(() => {
                let resultadoSimulado = {};
                const txId = `TX_${endpoint.toUpperCase().replace('-', '_')}_${int(Date.now() / 1000)}`;

                if (endpoint === 'registrar-entrada') {
                    resultadoSimulado = {
                        transacao_id: txId,
                        status: 'CONCLUIDO',
                        score_risco: 5,
                        motivos: ['Depósito Externo Identificado']
                    };
                } else if (endpoint === 'processar-saida' && dados.conta_origem === '127001') {
                    resultadoSimulado = {
                        transacao_id: txId,
                        status: 'RETIDA_PARA_ANALISE',
                        score_risco: 85,
                        motivos: ['Conta Nova (5 dias)', 'Alta Velocidade de Evasão (3s)', 'Estouro de Perfil Histórico']
                    };
                } else {
                    resultadoSimulado = {
                        transacao_id: txId,
                        status: 'CONCLUIDO',
                        score_risco: 12,
                        motivos: ['Dentro do Perfil Histórico']
                    };
                }

                exibirResultado(resultadoSimulado);
            }, 800);
        }

        // Restaura o botão após o processamento
        setTimeout(() => {
            botao.innerText = textoOriginal;
            botao.disabled = false;
        }, 800);
    }

    function exibirResultado(resultado) {
        if (!painelResultado) return;
        
        const ehCritico = resultado.score_risco >= 70 || resultado.status === 'RETIDA_PARA_ANALISE';
        
        painelResultado.innerHTML = `
            <div style="padding: 15px; border-radius: 8px; background-color: ${ehCritico ? '#ffcccc' : '#ccffcc'}; color: #000; margin-top: 15px; font-family: sans-serif; border-left: 5px solid ${ehCritico ? '#ff0000' : '#00aa00'};">
                <strong style="font-size: 16px;">[SISTEMA CORE BANKING]</strong><br><br>
                <strong>Status da Transação:</strong> ${resultado.status}<br>
                <strong>Score de Risco Antifraude:</strong> ${resultado.score_risco}/100<br>
                <strong>ID de Auditoria:</strong> ${resultado.transacao_id}<br>
                ${resultado.motivos ? `<strong>Métricas analisadas:</strong> ${resultado.motivos.join(', ')}` : ''}
            </div>
        `;
    }

    // Configuração dos eventos de clique baseados nos 3 botões da sua imagem
    if (btnInjetarPix) {
        btnInjetarPix.addEventListener('click', (e) => {
            e.preventDefault();
            processarSimulacao('registrar-entrada', { conta_id: '127001', valor: 15000.0 }, btnInjetarPix);
        });
    }

    if (btnForcarEvasao) {
        btnForcarEvasao.addEventListener('click', (e) => {
            e.preventDefault();
            processarSimulacao('processar-saida', { conta_origem: '127001', conta_destino: '127003', valor: 15000.0 }, btnForcarEvasao);
        });
    }

    if (btnSimularLegitima) {
        btnSimularLegitima.addEventListener('click', (e) => {
            e.preventDefault();
            processarSimulacao('processar-saida', { conta_origem: '127002', conta_destino: '127003', valor: 500.0 }, btnSimularLegitima);
        });
    }
});
