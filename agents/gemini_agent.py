import os
import logging
import google.generativeai as genai
from config import Config
from functools import wraps
import time
from datetime import datetime

# Configuração do logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def retry_on_failure(max_retries=3, delay=1):
    """Decorator to retry a function on failure"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {str(e)}")
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(delay)
            return None
        return wrapper
    return decorator

class GeminiAgent:
    def __init__(self):
        """Initialize the Gemini agent with API key"""
        if not Config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=Config.GEMINI_API_KEY)
        self.model = genai.GenerativeModel(Config.GEMINI_MODEL)
        self.logger = logging.getLogger(__name__)

    @retry_on_failure(max_retries=3)
    def generate_document(self, case_type, parties, facts, legal_grounds, requests):
        """Generate a legal document using the Gemini model"""
        try:
            prompt = self._create_prompt(case_type, parties, facts, legal_grounds, requests)
            response = self.model.generate_content(prompt)
            
            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")
            
            document = self._format_document(response.text, case_type)
            return document
            
        except Exception as e:
            self.logger.error(f"Error generating document: {str(e)}")
            raise

    def _create_prompt(self, case_type, parties, facts, legal_grounds, requests):
        """Create a prompt for the Gemini model"""
        return f"""
        Gere uma peça jurídica do tipo {case_type} com as seguintes informações:

        PARTES ENVOLVIDAS:
        {parties}

        FATOS:
        {facts}

        FUNDAMENTAÇÃO JURÍDICA:
        {legal_grounds}

        PEDIDOS:
        {requests}

        Instruções:
        1. Use linguagem jurídica formal e técnica
        2. Estruture o documento em seções claras:
           - Cabeçalho com tipo de peça
           - Qualificação das partes
           - Dos fatos
           - Da fundamentação jurídica
           - Dos pedidos
        3. Inclua citações relevantes de leis e jurisprudência
        4. Mantenha a objetividade e clareza
        5. Formate o documento em HTML com tags apropriadas:
           - Use <h2 class="section-title"> para títulos de seções
           - Use <p class="document-paragraph"> para parágrafos
           - Use <strong class="highlight"> para termos importantes
           - Use <em class="citation"> para citações
           - Use <div class="legal-reference"> para referências legais
        6. Mantenha o documento dentro do tamanho A4 (aproximadamente 2000 palavras)
        7. Use parágrafos curtos e objetivos
        8. Inclua numeração de parágrafos quando apropriado
        9. NÃO inclua estilos CSS inline no documento
        10. Use APENAS as classes CSS definidas, sem adicionar estilos inline
        11. Formate incisos e alíneas corretamente:
            - Use <div class="legal-item">I -</div> para incisos
            - Use <div class="legal-subitem">a)</div> para alíneas
            - Mantenha a hierarquia visual adequada
        12. Estruture os pedidos em tópicos numerados
        13. Use referências cruzadas quando necessário
        14. Inclua numeração de artigos e parágrafos
        15. Mantenha a formatação consistente em todo o documento
        """

    def _format_document(self, document: str, case_type: str) -> str:
        """Formata o documento gerado com HTML estruturado."""
        current_date = datetime.now().strftime("%d de %B de %Y")
        
        # Remove estilos inline e formata o conteúdo
        document = document.replace('.section-title {', '')
        document = document.replace('font-size: 1.2em;', '')
        document = document.replace('font-weight: bold;', '')
        document = document.replace('.document-paragraph {', '')
        document = document.replace('text-align: justify;', '')
        document = document.replace('.highlight {', '')
        document = document.replace('font-weight: bold;', '')
        document = document.replace('.citation {', '')
        document = document.replace('.legal-reference {', '')
        document = document.replace('margin-top: 5px;', '')
        document = document.replace('font-size: 0.9em;', '')
        document = document.replace('color: #555;', '')
        document = document.replace('}', '')
        
        # Estrutura HTML base com classes para estilização
        html_template = f"""
        <div class="legal-document">
            <div class="document-header">
                <h1 class="document-title">{case_type}</h1>
                <p class="document-date">Data: {current_date}</p>
            </div>
            
            <div class="document-content">
                {document}
            </div>
            
            <div class="document-signature">
                <div class="signature-line"></div>
                <p class="signature-name">Advogado(a)</p>
                <p class="signature-oab">OAB/XX XXX.XXX</p>
            </div>
            
            <div class="document-footer">
                <p class="footer-text">Documento gerado por LexGenius</p>
                <p class="footer-date">Data de geração: {current_date}</p>
            </div>
        </div>
        """
        
        # Aplica formatação adicional ao conteúdo
        formatted_doc = html_template.replace(
            document,
            document.replace('\n\n', '</p><p class="document-paragraph">')
                    .replace('\n', '<br>')
                    .replace('§', '<span class="paragraph-number">§</span>')
                    .replace('Art.', '<span class="article-number">Art.</span>')
                    .replace('LEI Nº', '<span class="law-number">LEI Nº</span>')
                    .replace('CPC', '<span class="code-reference">CPC</span>')
                    .replace('CC', '<span class="code-reference">CC</span>')
                    .replace('STJ', '<span class="court-reference">STJ</span>')
                    .replace('STF', '<span class="court-reference">STF</span>')
                    # Formatação de incisos
                    .replace('I -', '<div class="legal-item">I -</div>')
                    .replace('II -', '<div class="legal-item">II -</div>')
                    .replace('III -', '<div class="legal-item">III -</div>')
                    .replace('IV -', '<div class="legal-item">IV -</div>')
                    .replace('V -', '<div class="legal-item">V -</div>')
                    .replace('VI -', '<div class="legal-item">VI -</div>')
                    .replace('VII -', '<div class="legal-item">VII -</div>')
                    .replace('VIII -', '<div class="legal-item">VIII -</div>')
                    .replace('IX -', '<div class="legal-item">IX -</div>')
                    .replace('X -', '<div class="legal-item">X -</div>')
                    # Formatação de alíneas
                    .replace('a)', '<div class="legal-subitem">a)</div>')
                    .replace('b)', '<div class="legal-subitem">b)</div>')
                    .replace('c)', '<div class="legal-subitem">c)</div>')
                    .replace('d)', '<div class="legal-subitem">d)</div>')
                    .replace('e)', '<div class="legal-subitem">e)</div>')
                    .replace('f)', '<div class="legal-subitem">f)</div>')
                    .replace('g)', '<div class="legal-subitem">g)</div>')
                    .replace('h)', '<div class="legal-subitem">h)</div>')
                    .replace('i)', '<div class="legal-subitem">i)</div>')
                    .replace('j)', '<div class="legal-subitem">j)</div>')
        )
        
        return formatted_doc 