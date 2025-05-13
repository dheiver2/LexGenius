from flask import Flask, request, render_template, send_file, flash, redirect, url_for, session, jsonify
from dotenv import load_dotenv
import os
import google.generativeai as genai
import pdfkit
import tempfile
import logging
from datetime import datetime, timedelta
from functools import wraps
import secrets
from pytz import timezone
import re
import json

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))  # Usa SECRET_KEY do .env ou gera uma nova
load_dotenv()

# Configurações de segurança
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)  # Sessão expira em 1 hora
app.config['SESSION_COOKIE_SECURE'] = True  # Cookie só é enviado via HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Previne acesso via JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Proteção contra CSRF

# Credenciais padrão
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "admin123"

# Configurações de validação
MIN_TEXT_LENGTH = 50
MAX_TEXT_LENGTH = 5000
ALLOWED_CASE_TYPES = [
    "Petição Inicial",
    "Contestação",
    "Recurso",
    "Agravo",
    "Embargos"
]

# Gemini API setup
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY não encontrada no arquivo .env")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash')

# Configuração do pdfkit
pdfkit_config = pdfkit.configuration(wkhtmltopdf='C:\\Program Files\\wkhtmltopdf\\bin\\wkhtmltopdf.exe')

# Função para obter data/hora atual com timezone
def get_current_time():
    return datetime.now(timezone('America/Sao_Paulo'))

# Decorator para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Por favor, faça login para acessar esta página.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Decorator para limitar tentativas de login
def login_attempts(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'login_attempts' not in session:
            session['login_attempts'] = 0
            session['last_attempt'] = get_current_time().isoformat()
        
        last_attempt = datetime.fromisoformat(session['last_attempt'])
        current_time = get_current_time()
        
        # Reset tentativas após 15 minutos
        if (current_time - last_attempt) > timedelta(minutes=15):
            session['login_attempts'] = 0
        
        if session['login_attempts'] >= 3:
            flash('Muitas tentativas de login. Tente novamente em 15 minutos.', 'error')
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
@login_attempts
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        session['last_attempt'] = get_current_time().isoformat()
        session['login_attempts'] = session.get('login_attempts', 0) + 1
        
        if username == DEFAULT_USERNAME and password == DEFAULT_PASSWORD:
            session['logged_in'] = True
            session['login_attempts'] = 0  # Reset tentativas após login bem-sucedido
            session.permanent = True  # Mantém a sessão por 1 hora
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
            logging.warning(f'Tentativa de login falhou para usuário: {username}')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()  # Limpa todos os dados da sessão
    flash('Você foi desconectado.', 'success')
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

def validate_text(text, field_name):
    """Valida o texto de entrada"""
    if not text or not isinstance(text, str):
        return False, f"O campo {field_name} não pode estar vazio"
    
    text = text.strip()
    if len(text) < MIN_TEXT_LENGTH:
        return False, f"O campo {field_name} deve ter pelo menos {MIN_TEXT_LENGTH} caracteres"
    if len(text) > MAX_TEXT_LENGTH:
        return False, f"O campo {field_name} não pode ter mais que {MAX_TEXT_LENGTH} caracteres"
    
    # Verifica caracteres especiais ou scripts maliciosos
    if re.search(r'<script|javascript:|on\w+\s*=', text, re.IGNORECASE):
        return False, f"O campo {field_name} contém caracteres não permitidos"
    
    return True, text

def validate_case_type(case_type):
    """Valida o tipo de peça"""
    if case_type not in ALLOWED_CASE_TYPES:
        return False, "Tipo de peça inválido"
    return True, case_type

def sanitize_html(html_content):
    """Sanitiza o conteúdo HTML"""
    # Remove scripts e eventos
    html_content = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
    html_content = re.sub(r'on\w+\s*=\s*"[^"]*"', '', html_content)
    
    # Mantém apenas tags HTML seguras
    allowed_tags = ['div', 'h1', 'h2', 'p', 'br', 'strong', 'em', 'ul', 'li', 'ol']
    pattern = f'<(?!/?(?:{"|".join(allowed_tags)})\\b)[^>]*>'
    html_content = re.sub(pattern, '', html_content)
    
    return html_content

@app.route('/validate', methods=['POST'])
@login_required
def validate_form():
    """Endpoint para validação do formulário via AJAX"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'valid': False, 'message': 'Dados inválidos'})

        # Valida tipo de peça
        is_valid, message = validate_case_type(data.get('case_type', ''))
        if not is_valid:
            return jsonify({'valid': False, 'message': message})

        # Valida outros campos
        fields = ['parties', 'facts', 'legal_grounds', 'requests']
        for field in fields:
            is_valid, message = validate_text(data.get(field, ''), field)
            if not is_valid:
                return jsonify({'valid': False, 'message': message})

        return jsonify({'valid': True})
    except Exception as e:
        logging.error(f"Erro na validação: {str(e)}")
        return jsonify({'valid': False, 'message': 'Erro na validação dos dados'})

@app.route('/generate', methods=['POST'])
@login_required
def generate_document():
    try:
        # Logging detalhado do request
        logging.info(f"Headers: {dict(request.headers)}")
        logging.info(f"Form data: {request.form}")
        logging.info(f"Files: {request.files}")

        # Verifica se é uma requisição POST
        if request.method != 'POST':
            raise ValueError("Método não permitido")

        # Verifica se o Content-Type está correto
        content_type = request.headers.get('Content-Type', '')
        if not content_type or 'multipart/form-data' not in content_type and 'application/x-www-form-urlencoded' not in content_type:
            raise ValueError(f"Content-Type inválido: {content_type}")

        # Validação dos campos obrigatórios
        required_fields = ['case_type', 'parties', 'facts', 'legal_grounds', 'requests']
        missing_fields = [field for field in required_fields if field not in request.form]
        
        if missing_fields:
            error_msg = f"Campos obrigatórios ausentes: {', '.join(missing_fields)}"
            logging.error(error_msg)
            flash(error_msg, 'error')
            return redirect(url_for('index'))

        # Validação do tipo de peça
        case_type = request.form.get('case_type', '').strip()
        if not case_type:
            flash('O tipo de peça é obrigatório', 'error')
            return redirect(url_for('index'))

        is_valid, message = validate_case_type(case_type)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('index'))

        # Validação e sanitização dos campos de texto
        fields_to_validate = {
            'parties': 'Partes Envolvidas',
            'facts': 'Fatos',
            'legal_grounds': 'Fundamentação Jurídica',
            'requests': 'Pedidos'
        }

        validated_data = {}
        for field, display_name in fields_to_validate.items():
            value = request.form.get(field, '').strip()
            if not value:
                flash(f'O campo {display_name} é obrigatório', 'error')
                return redirect(url_for('index'))

            is_valid, result = validate_text(value, display_name)
            if not is_valid:
                flash(result, 'error')
                return redirect(url_for('index'))
            validated_data[field] = result

        validated_data['case_type'] = case_type

        logging.info(f"Iniciando geração de documento do tipo: {case_type}")
        logging.info(f"Dados validados: {validated_data}")

        # Define prompt for Gemini API
        prompt = f"""
        Crie uma peça jurídica em português (tipo: {validated_data['case_type']}) com base nas seguintes informações.
        Formate o documento seguindo a estrutura abaixo, usando as tags HTML apropriadas.
        Mantenha a formatação consistente e profissional:

        <div class="header">
            <h1>{validated_data['case_type']}</h1>
        </div>

        <h2>I - DAS PARTES</h2>
        <p>{validated_data['parties']}</p>

        <h2>II - DOS FATOS</h2>
        <p>{validated_data['facts']}</p>

        <h2>III - DA FUNDAMENTAÇÃO JURÍDICA</h2>
        <p>{validated_data['legal_grounds']}</p>

        <h2>IV - DOS PEDIDOS</h2>
        <p>{validated_data['requests']}</p>

        <div class="signature">
            <div class="signature-line"></div>
            <p>Advogado(a)</p>
            <p>OAB/XX XXX.XXX</p>
        </div>

        <div class="footer">
            Documento gerado em {get_current_time().strftime('%d/%m/%Y %H:%M:%S')}
        </div>

        A peça deve seguir o formato formal de documentos jurídicos brasileiros, com linguagem técnica e formal.
        Mantenha a formatação consistente, com parágrafos bem estruturados e espaçamento adequado.
        Não inclua nenhum CSS ou estilo inline no documento.
        """

        try:
            # Generate document
            response = model.generate_content(prompt)
            if not response or not response.text:
                raise ValueError("Resposta vazia da API Gemini")
            
            result = response.text
            logging.info("Documento gerado com sucesso pela API Gemini")

        except Exception as e:
            logging.error(f"Erro na geração do documento pela API Gemini: {str(e)}")
            flash('Erro ao gerar documento: falha na comunicação com a API', 'error')
            return redirect(url_for('index'))

        # Sanitiza o HTML gerado
        result = sanitize_html(result)
        logging.info("HTML sanitizado com sucesso")

        # Convert to PDF
        try:
        html = f"""
            <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&display=swap');
                    
                    body {{
                        font-family: 'Playfair Display', serif;
                        line-height: 2;
                        text-align: justify;
                        margin: 40px;
                        color: #2C3E50;
                    }}
                    
                    h1 {{
                        font-size: 2rem;
                        text-align: center;
                        margin-bottom: 2rem;
                        font-weight: 700;
                        text-transform: uppercase;
                        letter-spacing: 1px;
                        color: #2C3E50;
                    }}
                    
                    h2 {{
                        font-size: 1.4rem;
                        margin-top: 2.5rem;
                        margin-bottom: 1.5rem;
                        font-weight: 700;
                        color: #34495E;
                        border-bottom: 2px solid #3498DB;
                        padding-bottom: 0.5rem;
                    }}
                    
                    p {{
                        margin-bottom: 1.5rem;
                        text-indent: 2rem;
                    }}
                    
                    .header {{
                        text-align: center;
                        margin-bottom: 3rem;
                        padding-bottom: 2rem;
                        border-bottom: 2px solid #3498DB;
                    }}
                    
                    .footer {{
                        text-align: center;
                        margin-top: 4rem;
                        padding-top: 2rem;
                        border-top: 1px solid #E2E8F0;
                        font-size: 0.9rem;
                        color: #34495E;
                    }}
                    
                    .signature {{
                        margin-top: 4rem;
                        text-align: center;
                    }}
                    
                    .signature-line {{
                        width: 300px;
                        margin: 0 auto;
                        border-top: 2px solid #2C3E50;
                        margin-bottom: 0.5rem;
                    }}
            </style>
        </head>
        <body>
                {result}
        </body>
        </html>
        """
        
        # Create temporary PDF file
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
                pdfkit.from_string(html, tmp.name, configuration=pdfkit_config)
            pdf_path = tmp.name

            logging.info(f"PDF gerado com sucesso: {pdf_path}")
            flash('Documento gerado com sucesso!', 'success')
            
            # Armazena o caminho do PDF na sessão
            session['pdf_path'] = pdf_path
            
            return render_template('index.html', document=result, pdf_path=pdf_path)

        except Exception as e:
            logging.error(f"Erro ao gerar PDF: {str(e)}")
            flash('Erro ao gerar PDF do documento', 'error')
            return redirect(url_for('index'))

    except Exception as e:
        logging.error(f"Erro ao gerar documento: {str(e)} | request.form: {request.form}")
        flash(f'Erro ao gerar documento: {str(e)}', 'error')
        return redirect(url_for('index'))

@app.route('/download/<path:filename>')
@login_required
def download_file(filename):
    try:
        # Verifica se o arquivo existe e está dentro do diretório temporário
        if not os.path.exists(filename) or not filename.startswith(tempfile.gettempdir()):
            logging.error(f"Arquivo não encontrado ou acesso negado: {filename}")
            flash('Arquivo não encontrado ou acesso negado', 'error')
            return redirect(url_for('index'))
            
        # Obtém o nome do arquivo para download
        download_name = f"documento_juridico_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        
        return send_file(
            filename,
            as_attachment=True,
            download_name=download_name,
            mimetype='application/pdf'
        )
    except Exception as e:
        logging.error(f"Erro ao baixar arquivo: {str(e)}")
        flash('Erro ao baixar arquivo', 'error')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 