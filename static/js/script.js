document.addEventListener('DOMContentLoaded', function() {
    // Get all required elements
    const form = document.getElementById('legalForm');
    const documentTab = document.getElementById('document-tab');
    const loadingIndicator = document.getElementById('loadingIndicator');
    const documentContent = document.getElementById('documentContent');
    const analysisContent = document.getElementById('analysisContent');
    const basisContent = document.getElementById('basisContent');
    const reviewContent = document.getElementById('reviewContent');

    // Verify all required elements exist
    const requiredElements = {
        form,
        documentTab,
        loadingIndicator,
        documentContent,
        analysisContent,
        basisContent,
        reviewContent
    };

    const missingElements = Object.entries(requiredElements)
        .filter(([_, element]) => !element)
        .map(([name]) => name);

    if (missingElements.length > 0) {
        console.error('Elementos necessários não encontrados:', missingElements);
        return;
    }

    // Initialize Bootstrap tabs
    const tabElements = document.querySelectorAll('[data-bs-toggle="tab"]');
    tabElements.forEach(tab => {
        new bootstrap.Tab(tab);
    });

    // Copy to clipboard function
    function copyToClipboard() {
        const documentText = documentContent.innerText;
        navigator.clipboard.writeText(documentText).then(() => {
            const copyButton = document.querySelector('button[onclick="copyToClipboard()"]');
            if (copyButton) {
                const originalText = copyButton.innerHTML;
                copyButton.innerHTML = '<i class="bi bi-check"></i> Copiado!';
                setTimeout(() => {
                    copyButton.innerHTML = originalText;
                }, 2000);
            }
        }).catch(err => {
            console.error('Erro ao copiar texto:', err);
            alert('Erro ao copiar o texto. Por favor, tente novamente.');
        });
    }

    // Make copyToClipboard available globally
    window.copyToClipboard = copyToClipboard;

    // Function to switch tabs
    function switchTab(tabId) {
        const tab = document.querySelector(`#${tabId}`);
        if (tab) {
            const tabInstance = bootstrap.Tab.getOrCreateInstance(tab);
            tabInstance.show();
        }
    }

    // Function to show error message
    function showError(message) {
        const errorHtml = `
            <div class="alert alert-danger alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
            </div>
        `;
        document.getElementById('errorContainer').innerHTML = errorHtml;
    }

    // Form submission handler
    form.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        // Show loading indicator
        loadingIndicator.style.display = 'block';
        
        // Clear previous content
        documentContent.innerHTML = '';
        analysisContent.innerHTML = '';
        basisContent.innerHTML = '';
        reviewContent.innerHTML = '';

        try {
            const formData = new FormData(form);
            const response = await fetch('/generate', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            if (result.status === 'error') {
                throw new Error(result.error);
            }

            // Update document tab
            documentContent.innerHTML = formatDocument(result.document);

            // Update analysis tab
            analysisContent.innerHTML = formatAnalysis(result.analysis);

            // Update basis tab
            basisContent.innerHTML = formatBasis(result.basis);

            // Update review tab
            reviewContent.innerHTML = formatReview(result.review);

            // Switch to document tab
            switchTab('document');

        } catch (error) {
            console.error('Error:', error);
            showError(error.message || 'Ocorreu um erro ao processar sua solicitação.');
        } finally {
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
        }
    });

    // Helper functions to format content
    function formatDocument(document) {
        return `<pre class="document-text">${document}</pre>`;
    }

    function formatAnalysis(analysis) {
        try {
            const data = typeof analysis === 'string' ? JSON.parse(analysis) : analysis;
            return `
                <div class="analysis-section">
                    <h4>Pontos Fortes</h4>
                    <ul>${data.pontos_fortes.map(ponto => `<li>${ponto}</li>`).join('')}</ul>
                    
                    <h4>Pontos Fracos</h4>
                    <ul>${data.pontos_fracos.map(ponto => `<li>${ponto}</li>`).join('')}</ul>
                    
                    <h4>Riscos</h4>
                    <ul>${data.riscos.map(risco => `<li>${risco}</li>`).join('')}</ul>
                    
                    <h4>Oportunidades</h4>
                    <ul>${data.oportunidades.map(oportunidade => `<li>${oportunidade}</li>`).join('')}</ul>
                    
                    <h4>Sugestões de Melhoria</h4>
                    <ul>${data.sugestoes_melhoria.map(sugestao => `<li>${sugestao}</li>`).join('')}</ul>
                </div>
            `;
        } catch (error) {
            console.error('Erro ao formatar análise:', error);
            return '<p class="text-danger">Erro ao processar análise do caso.</p>';
        }
    }

    function formatBasis(basis) {
        return `<pre class="basis-text">${basis}</pre>`;
    }

    function formatReview(review) {
        try {
            const data = typeof review === 'string' ? JSON.parse(review) : review;
            return `
                <div class="review-section">
                    <h4>Estrutura</h4>
                    <p>${data.estrutura || 'Não disponível'}</p>
                    
                    <h4>Clareza</h4>
                    <p>${data.clareza || 'Não disponível'}</p>
                    
                    <h4>Coerência</h4>
                    <p>${data.coerencia || 'Não disponível'}</p>
                    
                    <h4>Sugestões de Melhoria</h4>
                    <ul>${(data.sugestoes_melhoria || []).map(sugestao => `<li>${sugestao}</li>`).join('')}</ul>
                </div>
            `;
        } catch (error) {
            console.error('Erro ao formatar revisão:', error);
            return '<p class="text-danger">Erro ao processar revisão do documento.</p>';
        }
    }
}); 