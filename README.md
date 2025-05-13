# 🚀 LexGenius

<div align="center">
  <img src="static/logo.png" alt="LexGenius Logo" width="200"/>
  <h3>Gerador Inteligente de Documentos Jurídicos</h3>
</div>

## 📋 Sobre o Projeto

LexGenius é uma aplicação web moderna que utiliza inteligência artificial para gerar documentos jurídicos profissionais de forma rápida e eficiente. Desenvolvido com Python e Flask, o sistema oferece uma interface intuitiva e recursos avançados para advogados e profissionais do direito.

## ✨ Funcionalidades

- 🤖 Geração de documentos jurídicos usando IA (Gemini API)
- 📝 Suporte a múltiplos tipos de peças jurídicas:
  - Petição Inicial
  - Contestação
  - Recurso
  - Agravo
  - Embargos
- 🔒 Sistema de autenticação seguro
- 📊 Interface moderna e responsiva
- 📄 Exportação em PDF
- 📋 Copiar documento para área de transferência
- ⚡ Validação em tempo real
- 📱 Design responsivo

## 🛠️ Tecnologias Utilizadas

- Python 3.8+
- Flask
- Google Gemini AI
- Bootstrap 5
- TailwindCSS
- PDFKit
- HTML5/CSS3
- JavaScript

## 🚀 Instalação

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/lexgenius.git
cd lexgenius
```

2. Crie um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```
Edite o arquivo `.env` com suas configurações:
```
GEMINI_API_KEY=sua_chave_api
SECRET_KEY=sua_chave_secreta
```

5. Instale o wkhtmltopdf:
- Windows: Baixe e instale de https://wkhtmltopdf.org/downloads.html
- Linux: `sudo apt-get install wkhtmltopdf`
- Mac: `brew install wkhtmltopdf`

6. Execute a aplicação:
```bash
python app.py
```

## 🔧 Configuração

### Credenciais Padrão
- Usuário: admin
- Senha: admin123

### Tipos de Documentos Suportados
- Petição Inicial
- Contestação
- Recurso
- Agravo
- Embargos

## 📝 Uso

1. Acesse a aplicação em `http://localhost:5000`
2. Faça login com as credenciais
3. Selecione o tipo de documento
4. Preencha os campos necessários:
   - Partes Envolvidas
   - Fatos
   - Fundamentação Jurídica
   - Pedidos
5. Clique em "Gerar Peça"
6. Visualize, copie ou baixe o documento em PDF

## 🔒 Segurança

- Autenticação de usuário
- Proteção contra CSRF
- Sanitização de inputs
- Validação de dados
- Sessões seguras
- Limite de tentativas de login

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## �� Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 📞 Suporte

Para suporte, envie um email para seu-email@exemplo.com ou abra uma issue no GitHub.

## 🙏 Agradecimentos

- Google Gemini AI
- Flask Framework
- Bootstrap
- TailwindCSS
- Comunidade Open Source

---

<div align="center">
  <p>Desenvolvido com ❤️ para a comunidade jurídica</p>
</div> 