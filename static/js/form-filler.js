// Default case example
const defaultCase = {
    tipo_acao: 'Ação de Indenização por Danos Materiais e Morais',
    autor: 'Maria Silva',
    reu: 'Empresa XYZ Ltda.',
    fatos: 'A autora adquiriu um produto eletrônico que apresentou defeito após 3 meses de uso. A empresa se recusou a realizar a troca ou conserto, alegando que o prazo de garantia havia expirado.',
    fundamentacao: 'Código de Defesa do Consumidor, art. 6º, inciso III - direito à informação adequada e clara sobre os produtos e serviços.',
    pedidos: '1. Condenação da ré ao pagamento de R$ 10.000,00 a título de danos materiais; 2. Condenação da ré ao pagamento de R$ 5.000,00 a título de danos morais; 3. Honorários advocatícios de 20% sobre o valor da causa.'
};

// Add event listener when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const fillExampleButton = document.getElementById('fillExample');
    if (fillExampleButton) {
        fillExampleButton.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Preenchendo formulário com exemplo...');
            Object.entries(defaultCase).forEach(([key, value]) => {
                const input = document.getElementById(key);
                if (input) {
                    input.value = value;
                    input.dispatchEvent(new Event('input', { bubbles: true }));
                    input.classList.remove('is-invalid');
                } else {
                    console.warn(`Campo não encontrado: ${key}`);
                }
            });
        });
    } else {
        console.error('Botão de exemplo não encontrado');
    }
}); 