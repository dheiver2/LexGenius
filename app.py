from flask import Flask, request, render_template, send_file, flash, redirect, url_for, session, jsonify, make_response
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
from config import Config
from agents.gemini_agent import GeminiAgent
from utils.cache_manager import init_cache, cache_document, get_cached_document, clear_document_cache, limiter, CacheManager
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# Configuração de logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(Config.LOG_FILE),
        logging.StreamHandler()
    ]
)

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', secrets.token_hex(32))  # Usa SECRET_KEY do .env ou gera uma nova
load_dotenv()
app.config.from_object(Config)

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
pdfkit_config = pdfkit.configuration(wkhtmltopdf=Config.PDFKIT_PATH)

# Inicializa o cache e rate limiter
init_cache(app)

# Inicializa o agente Gemini
gemini_agent = GeminiAgent()

# Configuração do Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Classe de usuário para o Flask-Login
class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Simulação de banco de dados de usuários (em produção, use um banco de dados real)
users = {
    'admin': User('1', 'admin', generate_password_hash('admin123'))
}

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if user.id == user_id:
            return user
    return None

# Context processor para disponibilizar Config em todos os templates
@app.context_processor
def inject_config():
    return dict(Config=Config)

# Função para obter data/hora atual com timezone
def get_current_time():
    return datetime.now(timezone('America/Sao_Paulo'))

# Decorator para verificar se o usuário está logado
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'danger')
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
        
        user = users.get(username)
        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['login_attempts'] = 0  # Reset tentativas após login bem-sucedido
            session.permanent = True  # Mantém a sessão por 1 hora
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuário ou senha incorretos.', 'error')
            logging.warning(f'Tentativa de login falhou para usuário: {username}')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
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
    
    # Validação específica para o campo parties
    if field_name == 'parties':
        if len(text) < 50:
            return False, "O campo Partes Envolvidas deve ter pelo menos 50 caracteres. Descreva detalhadamente as partes envolvidas no processo."
    
    # Validação geral para outros campos
    if len(text) < Config.MIN_TEXT_LENGTH:
        return False, f"O campo {field_name} deve ter pelo menos {Config.MIN_TEXT_LENGTH} caracteres"
    if len(text) > Config.MAX_TEXT_LENGTH:
        return False, f"O campo {field_name} não pode ter mais que {Config.MAX_TEXT_LENGTH} caracteres"
    
    # Verifica caracteres especiais ou scripts maliciosos
    if re.search(r'<script|javascript:|on\w+\s*=', text, re.IGNORECASE):
        return False, f"O campo {field_name} contém caracteres não permitidos"
    
    return True, text

def validate_case_type(case_type):
    """Valida o tipo de peça"""
    if case_type not in Config.ALLOWED_CASE_TYPES:
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
@limiter.limit("30 per minute")
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
@limiter.limit("10 per minute")
def generate_document():
    try:
        # Logging detalhado do request
        logging.info(f"Headers: {dict(request.headers)}")
        logging.info(f"Form data: {request.form}")
        logging.info(f"Files: {request.files}")

        # Verifica se é uma requisição POST
        if request.method != 'POST':
            raise ValueError("Método não permitido")

        # Obtém e valida os dados do formulário
        case_type = request.form.get('case_type', '').strip()
        parties = request.form.get('parties', '').strip()
        facts = request.form.get('facts', '').strip()
        legal_grounds = request.form.get('legal_grounds', '').strip()
        requests = request.form.get('requests', '').strip()

        # Valida o tipo de peça
        is_valid, message = validate_case_type(case_type)
        if not is_valid:
            flash(message, 'error')
            return redirect(url_for('index'))

        # Valida os outros campos
        fields = {
            'parties': parties,
            'facts': facts,
            'legal_grounds': legal_grounds,
            'requests': requests
        }

        for field_name, field_value in fields.items():
            is_valid, message = validate_text(field_value, field_name)
            if not is_valid:
                flash(message, 'error')
                return redirect(url_for('index'))

        # Gera o documento usando o agente Gemini
        try:
            sections = gemini_agent.generate_document(
                case_type=case_type,
                parties=parties,
                facts=facts,
                legal_grounds=legal_grounds,
                requests=requests
            )
        except Exception as e:
            logging.error(f"Erro na geração do documento: {str(e)}")
            flash("Erro ao gerar o documento. Por favor, tente novamente.", 'error')
            return redirect(url_for('index'))

        # Prepara variáveis para o template
        case_type_title = case_type.upper()
        court_header = "EXCELENTÍSSIMO(A) SENHOR(A) DOUTOR(A) JUIZ(A) DE DIREITO DA ____ª VARA CÍVEL DA COMARCA DE SÃO PAULO – SP"
        parties_html = '<p class="document-paragraph">' + sections.get('parties', '').replace('\n', '</p><p class="document-paragraph">') + '</p>' if sections.get('parties') else ''
        facts_html = '<p class="document-paragraph">' + sections.get('facts', '').replace('\n', '</p><p class="document-paragraph">') + '</p>' if sections.get('facts') else ''
        legal_grounds_html = '<p class="document-paragraph">' + sections.get('legal_grounds', '').replace('\n', '</p><p class="document-paragraph">') + '</p>' if sections.get('legal_grounds') else ''
        # Pedidos: cada linha vira <li>
        requests_html = ''.join(f'<li>{line.strip()}</li>' for line in sections.get('requests', '').split('\n') if line.strip())
        value_cause = sections.get('value_cause', '')
        city_date = sections.get('city_date', '')
        lawyer_name = sections.get('lawyer_name', '')
        lawyer_oab = sections.get('lawyer_oab', '')
        generation_date = datetime.now().strftime('%d de %B de %Y')

        # Monta o HTML final para o PDF
        html_for_pdf = render_template(
            'preview.html',
            case_type=case_type_title,
            court_header=court_header,
            parties=parties_html,
            facts=facts_html,
            legal_grounds=legal_grounds_html,
            requests=requests_html,
            value_cause=value_cause,
            city_date=city_date,
            lawyer_name=lawyer_name,
            lawyer_oab=lawyer_oab,
            generation_date=generation_date,
            pdf_path=None  # Não mostrar botão de download no PDF
        )

        # Gera o PDF
        try:
            pdf_options = {
                'page-size': 'A4',
                'margin-top': '2.5cm',
                'margin-right': '2.5cm',
                'margin-bottom': '2.5cm',
                'margin-left': '2.5cm',
                'encoding': 'UTF-8',
                'no-outline': None,
                'quiet': '',
                'print-media-type': '',
                'enable-local-file-access': '',
                'dpi': 300,
                'image-quality': 100,
                'enable-smart-shrinking': '',
                'zoom': 1.0
            }
            with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf:
                pdfkit.from_string(html_for_pdf, temp_pdf.name, configuration=pdfkit_config, options=pdf_options)
                pdf_path = os.path.basename(temp_pdf.name)
        except Exception as e:
            logging.error(f"Erro na geração do PDF: {str(e)}", exc_info=True)
            pdf_path = None

        # Renderiza o template de preview com as seções separadas
        return render_template(
            'preview.html',
            case_type=case_type_title,
            court_header=court_header,
            parties=parties_html,
            facts=facts_html,
            legal_grounds=legal_grounds_html,
            requests=requests_html,
            value_cause=value_cause,
            city_date=city_date,
            lawyer_name=lawyer_name,
            lawyer_oab=lawyer_oab,
            generation_date=generation_date,
            pdf_path=pdf_path
        )

    except Exception as e:
        logging.error(f"Erro na geração do documento: {str(e)}")
        flash("Ocorreu um erro ao processar sua solicitação.", 'error')
        return redirect(url_for('index'))

@app.route('/download/<path:filename>')
@login_required
def download_file(filename):
    """Download do arquivo PDF gerado."""
    try:
        # Configurações do PDF
        options = {
            'page-size': 'A4',
            'margin-top': '2.5cm',
            'margin-right': '2.5cm',
            'margin-bottom': '2.5cm',
            'margin-left': '2.5cm',
            'encoding': 'UTF-8',
            'no-outline': None,
            'quiet': '',
            'print-media-type': '',
            'enable-local-file-access': '',
            'dpi': 300,
            'image-quality': 100,
            'enable-smart-shrinking': '',
            'zoom': 1.0
        }
        # Gera o PDF com as configurações
        pdf = pdfkit.from_file(
            os.path.join(app.config['UPLOAD_FOLDER'], filename),
            False,
            options=options,
            configuration=pdfkit_config
        )
        # Configura o response para download
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        return response
    except Exception as e:
        logging.error(f"Erro ao gerar PDF: {str(e)}", exc_info=True)
        flash('Erro ao gerar o PDF. Por favor, tente novamente.', 'danger')
        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True) 