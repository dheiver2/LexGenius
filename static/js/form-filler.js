// Default case example
const defaultCase = {
    case_type: 'Ação de Indenização por Danos Materiais e Morais',
    parties: 'Autor: Maria Silva, brasileira, casada, portadora do RG nº 12.345.678-9 e CPF nº 123.456.789-00, residente e domiciliada na Rua das Flores, nº 123, Bairro Centro, Cidade de São Paulo/SP, CEP 01234-567.\n\nRéu: Empresa XYZ Ltda., pessoa jurídica de direito privado, inscrita no CNPJ sob o nº 12.345.678/0001-90, com sede na Avenida Principal, nº 456, Bairro Industrial, Cidade de São Paulo/SP, CEP 04567-890.',
    facts: 'A autora adquiriu um produto eletrônico que apresentou defeito após 3 meses de uso. A empresa se recusou a realizar a troca ou conserto, alegando que o prazo de garantia havia expirado.',
    legal_grounds: 'Código de Defesa do Consumidor, art. 6º, inciso III - direito à informação adequada e clara sobre os produtos e serviços.',
    requests: '1. Condenação da ré ao pagamento de R$ 10.000,00 a título de danos materiais;\n2. Condenação da ré ao pagamento de R$ 5.000,00 a título de danos morais;\n3. Honorários advocatícios de 20% sobre o valor da causa.'
};

// Add event listener when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    const fillExampleButton = document.getElementById('fillExample');
    if (fillExampleButton) {
        fillExampleButton.addEventListener('click', function(e) {
            e.preventDefault();
            console.log('Preenchendo formulário com exemplo...');
            
            // Preencher o select de tipo de peça
            const caseTypeSelect = document.getElementById('case_type');
            if (caseTypeSelect) {
                const options = Array.from(caseTypeSelect.options);
                const matchingOption = options.find(option => 
                    option.text.includes('Indenização por Danos Materiais e Morais')
                );
                if (matchingOption) {
                    caseTypeSelect.value = matchingOption.value;
                    caseTypeSelect.dispatchEvent(new Event('change', { bubbles: true }));
                }
            }
            
            // Preencher os campos de texto
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