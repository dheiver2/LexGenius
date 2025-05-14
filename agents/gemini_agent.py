import os
import logging
import google.generativeai as genai
from config import Config
from functools import wraps
import time
from datetime import datetime
from bs4 import BeautifulSoup
import re

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
        """Generate a legal document using the Gemini model and return sections separately"""
        try:
            prompt = self._create_prompt(case_type, parties, facts, legal_grounds, requests)
            response = self.model.generate_content(prompt)
            if not response or not response.text:
                raise ValueError("Empty response from Gemini API")
            # Parse the response into sections
            sections = self._parse_sections(response.text)
            return sections
        except Exception as e:
            self.logger.error(f"Error generating document: {str(e)}")
            raise

    def _create_prompt(self, case_type, parties, facts, legal_grounds, requests):
        """Prompt aprimorado para gerar peças jurídicas completas e profissionais."""
        return f"""
Gere o texto de uma peça jurídica do tipo {case_type} com as seguintes informações, retornando cada seção SEPARADAMENTE, SEM HTML, SEM formatação, apenas o texto puro de cada parte, usando os marcadores abaixo:

[PARTIES]
{parties}
[FACTS]
{facts}
[LEGAL_GROUNDS]
{legal_grounds}
[REQUESTS]
{requests}
[VALUE_CAUSE]
(Preencha com o valor da causa, ex: 'Dá-se à causa o valor de R$ 15.000,00 (quinze mil reais).')
[CITY_DATE]
(Preencha com cidade e data, ex: 'São Paulo, 14 de maio de 2025.')
[LAWYER_NAME]
(Preencha com o nome do advogado)
[LAWYER_OAB]
(Preencha com o número da OAB)

Instruções:
- Use linguagem jurídica formal, clara, objetiva e técnica.
- Estruture cada seção conforme a tradição forense brasileira.
- No preâmbulo e qualificação, detalhe nomes, documentos, endereços e representações.
- Nos fatos, conte a história com contexto, datas, valores, consequências e impacto.
- Na fundamentação, cite doutrina, jurisprudência e artigos de lei reais e relevantes, com trechos e explicações.
- Nos pedidos, detalhe cada um, fundamente e numere, incluindo citação, condenação, custas, honorários, protesto por provas, etc.
- Inclua protesto por provas, valor da causa, local/data e assinatura.
- Parágrafos devem ser numerados e justificados.
- Não repita informações entre seções.
- Não gere tópicos vazios ou genéricos.
- Cada pedido deve ser completo, objetivo e em frase única.
- O texto deve ser compatível com o padrão de grandes escritórios de advocacia.
"""

    def _parse_sections(self, text):
        """Extrai as seções do texto do Gemini usando marcadores."""
        sections = {
            'parties': '',
            'facts': '',
            'legal_grounds': '',
            'requests': '',
            'value_cause': '',
            'city_date': '',
            'lawyer_name': '',
            'lawyer_oab': ''
        }
        current = None
        buffer = []
        marker_map = {
            '[PARTIES]': 'parties',
            '[FACTS]': 'facts',
            '[LEGAL_GROUNDS]': 'legal_grounds',
            '[REQUESTS]': 'requests',
            '[VALUE_CAUSE]': 'value_cause',
            '[CITY_DATE]': 'city_date',
            '[LAWYER_NAME]': 'lawyer_name',
            '[LAWYER_OAB]': 'lawyer_oab'
        }
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line in marker_map:
                if current and buffer:
                    sections[current] = '\n'.join(buffer).strip()
                current = marker_map[line]
                buffer = []
            else:
                if current:
                    buffer.append(line)
        if current and buffer:
            sections[current] = '\n'.join(buffer).strip()
        return sections

    def _format_document(self, document: str, case_type: str) -> str:
        """Formata o documento gerado com HTML estruturado e limpo, títulos corretos e pedidos em lista."""
        current_date = datetime.now().strftime("%d de %B de %Y")

        # Remove blocos de código markdown e títulos duplicados
        document = re.sub(r'```[a-zA-Z]*', '', document)
        document = re.sub(r'Petição Inicial', '', document, count=1)

        # Remove blocos de CSS e tags <style>
        document = re.sub(r'<style.*?>.*?</style>', '', document, flags=re.DOTALL)
        document = re.sub(r'body\s*{[^}]*}', '', document, flags=re.DOTALL)
        document = re.sub(r'\{[^}]*\}', '', document, flags=re.DOTALL)

        # Remove qualquer atributo style
        document = re.sub(r'style="[^"]*"', '', document)

        # Corrige títulos de seção (DOS FATOS, DA FUNDAMENTAÇÃO JURÍDICA, etc.)
        def section_title_replacer(match):
            artigo = match.group(1) or ''
            texto = match.group(2).strip().title()
            # Corrige palavras comuns do juridiquês para maiúsculas
            texto = re.sub(r'\b(Da|Do|Dos|Das|E|A|O|As|Os|De|Em|No|Na|Nos|Nas|Por|Para|Com|Ao|À|Pelo|Pela|Pelos|Pelas)\b', lambda m: m.group(0).upper(), texto)
            return f'<h2 class="section-title">D{artigo.upper()} {texto}</h2>'
        document = re.sub(
            r'(?<![\w>])D(A|O|OS|AS)?\s+([A-ZÇÃÕÉÊÍÓÚÂÔÛÀÈÌÒÙ\s]+)',
            section_title_replacer,
            document
        )

        # Converte incisos romanos para <div class="legal-item">I - ...</div>
        document = re.sub(r'(?m)^([IVX]+)\s*-\s*(.*)$', r'<div class="legal-item">\1 - \2</div>', document)

        # Converte alíneas para <div class="legal-subitem">a) ...</div>
        document = re.sub(r'(?m)^([a-j])\)\s*(.*)$', r'<div class="legal-subitem">\1) \2</div>', document)

        # Converte parágrafos numerados para <p class="document-paragraph"><span class="paragraph-number">§ n.</span> ...</p>
        document = re.sub(r'§\s*(\d+)\.\s*(.*)', r'<p class="document-paragraph"><span class="paragraph-number">§ \1.</span> \2</p>', document)

        # Garante que linhas soltas virem parágrafos
        lines = document.splitlines()
        new_lines = []
        for line in lines:
            if (not line.strip().startswith('<') and line.strip()):
                new_lines.append(f'<p class="document-paragraph">{line.strip()}</p>')
            else:
                new_lines.append(line)
        document = '\n'.join(new_lines)

        # Formata pedidos em lista numerada (ol/li)
        # Procura "requer a Vossa Excelência:" e transforma os itens seguintes em <li>
        def pedidos_replacer(match):
            pre = match.group(1)
            pedidos = match.group(2)
            # Divide por ponto e vírgula ou quebra de linha
            itens = re.split(r';|\n', pedidos)
            lis = ''.join(f'<li>{item.strip()}</li>' for item in itens if item.strip())
            return f'{pre}<ol>{lis}</ol>'
        document = re.sub(r'(requer a Vossa Excelência:)(.*?)(<p|§|$)', pedidos_replacer, document, flags=re.DOTALL|re.IGNORECASE)

        # Remove linhas em branco extras
        document = re.sub(r'\n{2,}', '\n', document)

        # Usa BeautifulSoup para garantir HTML válido e remover tags não permitidas
        soup = BeautifulSoup(document, "html.parser")
        allowed_tags = {'h1', 'h2', 'p', 'div', 'span', 'em', 'strong', 'ol', 'li'}
        allowed_classes = {
            "section-title", "document-paragraph", "highlight", "citation",
            "legal-reference", "legal-item", "legal-subitem", "paragraph-number",
            "article-number", "law-number", "code-reference", "court-reference"
        }
        for tag in soup.find_all(True):
            if tag.name not in allowed_tags:
                tag.unwrap()
            if "class" in tag.attrs:
                tag['class'] = [c for c in tag.get('class', []) if c in allowed_classes]
                if not tag['class']:
                    del tag['class']
            # Remove qualquer atributo style remanescente
            if 'style' in tag.attrs:
                del tag['style']

        # Limpeza agressiva de tópicos vazios ou irrelevantes
        for tag in soup.find_all(['p', 'div', 'h2', 'li']):
            text = tag.get_text(strip=True)
            # Remove se não houver texto relevante (apenas pontuação, marcadores, números, etc)
            if (
                not text or
                re.fullmatch(r'[-–—.·•§\\s]*', text) or
                re.fullmatch(r'[0-9IVXivx]+[.\\-–—]*', text) or
                re.fullmatch(r'(Art\\.?|§|I+\\s*-|[0-9]+\\.|\\[.*?\\]|\\.{2,}|-+|–+|—+|•+|·+|,|;|:|/|\\\\)+', text) or
                text.lower() in ['...', '[]', 'art.', '§', 'i -', 'ii -', 'iii -', 'iv -', 'v -', 'vi -', 'vii -', 'viii -', 'ix -', 'x -']
            ):
                tag.decompose()
            # Remove títulos de seção que não contenham palavras jurídicas relevantes
            elif tag.name in ['h2', 'div'] and not re.search(r'(fato|pedido|fundamenta|qualifica|parte|conclus|requer|direito|dos|da|do|das|dos)', text, re.IGNORECASE):
                tag.decompose()

        html_template = f"""
        <div class="legal-document">
            <div class="document-header">
                <h1 class="document-title">{case_type}</h1>
                <p class="document-date">Data: {current_date}</p>
            </div>
            <div class="document-content">
                {str(soup)}
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
        return html_template 