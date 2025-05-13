# LexGenius - Gerador de Peças Jurídicas

LexGenius é uma aplicação web que utiliza inteligência artificial para gerar peças jurídicas de forma rápida e eficiente.

## Funcionalidades

- Geração de diferentes tipos de peças jurídicas
- Interface intuitiva e responsiva
- Preview do documento antes do download
- Exportação para PDF
- Sistema de cache para melhor performance
- Rate limiting para proteção da API
- Validação de dados em tempo real
- Sistema de autenticação seguro

## Requisitos

- Python 3.8+
- wkhtmltopdf
- Conta no Google Cloud com acesso à API Gemini

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/dheiver2/LexGenius.git
cd LexGenius
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Instale as dependências:
```bash
pip install -r requirements.txt
```

4. Instale o wkhtmltopdf:
- Windows: Baixe e instale de https://wkhtmltopdf.org/downloads.html
- Linux: `sudo apt-get install wkhtmltopdf`
- Mac: `brew install wkhtmltopdf`

5. Configure as variáveis de ambiente:
```bash
cp .env.example .env
```
Edite o arquivo .env com suas configurações.

## Uso

1. Inicie o servidor:
```bash
python app.py
```

2. Acesse http://localhost:5000 no navegador

3. Faça login com as credenciais configuradas

4. Preencha o formulário com os dados da peça jurídica

5. Visualize o preview e baixe o PDF

## Estrutura do Projeto

```
LexGenius/
├── agents/
│   └── gemini_agent.py
├── utils/
│   └── cache_manager.py
├── templates/
│   ├── index.html
│   ├── login.html
│   └── preview.html
├── static/
│   └── css/
├── app.py
├── config.py
├── requirements.txt
└── README.md
```

## Segurança

- Autenticação com limite de tentativas
- Rate limiting para proteção contra abusos
- Sanitização de inputs
- Validação de dados
- Sessões seguras
- Cache para otimização

## Contribuição

1. Faça um fork do projeto
2. Crie uma branch para sua feature (`git checkout -b feature/nova-feature`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova feature'`)
4. Push para a branch (`git push origin feature/nova-feature`)
5. Crie um Pull Request

## Licença

Este projeto está licenciado sob a MIT License - veja o arquivo LICENSE para detalhes.

## 🤝 Contribuindo

1. Faça um Fork do projeto
2. Crie uma Branch para sua Feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a Branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

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