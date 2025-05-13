from typing import Dict, Any
import json
from google import genai
from google.genai import types

class LegalCrew:
    def __init__(self, api_key: str):
        """Initialize the legal crew with the API key."""
        if not api_key or not api_key.startswith('AIza'):
            raise ValueError("API key inválida. A chave deve começar com 'AIza'")
            
        print(f"Configurando API key: {api_key[:10]}...")  # Mostra apenas os primeiros 10 caracteres por segurança
        self.api_key = api_key.strip()  # Remove espaços em branco
        
        try:
            self.client = genai.Client(api_key=self.api_key)
            # Teste simples para verificar se a chave funciona
            test_response = self.client.models.generate_content(
                model="gemini-pro",
                contents=["Teste de conexão"],
                config=types.GenerateContentConfig(
                    max_output_tokens=10,
                    temperature=0.1
                )
            )
            print("Teste de conexão com a API bem sucedido")
        except Exception as e:
            print(f"Erro ao configurar cliente Gemini: {str(e)}")
            raise ValueError(f"Erro ao configurar cliente Gemini: {str(e)}")

    def _generate_content(self, prompt: str) -> str:
        """Helper method to generate content with proper error handling."""
        try:
            print("Enviando prompt para o modelo...")
            response = self.client.models.generate_content(
                model="gemini-pro",
                contents=[prompt],
                config=types.GenerateContentConfig(
                    max_output_tokens=2048,
                    temperature=0.7
                )
            )
            if not response or not response.text:
                raise ValueError("Empty response from model")
            print("Resposta recebida com sucesso")
            return response.text
        except Exception as e:
            print(f"Erro ao gerar conteúdo: {str(e)}")
            raise ValueError(f"Error generating content: {str(e)}")

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """Helper method to parse JSON responses with proper error handling."""
        try:
            # Clean the response text to ensure it's valid JSON
            cleaned_text = text.strip()
            if not cleaned_text:
                raise ValueError("Empty response text")
            
            # Try to parse the JSON
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON response: {str(e)}")
        except Exception as e:
            raise ValueError(f"Error parsing response: {str(e)}")

    def process_case(self, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a legal case through all agents in sequence."""
        try:
            # Step 1: Case Analysis
            analysis_prompt = f"""
            Analise o seguinte caso jurídico e forneça uma análise estruturada em formato JSON:
            
            Tipo de Ação: {case_data['tipo_acao']}
            Autor: {case_data['autor']}
            Réu: {case_data['reu']}
            Fatos: {case_data['fatos']}
            Fundamentação: {case_data['fundamentacao']}
            Pedidos: {case_data['pedidos']}
            
            Forneça a análise no seguinte formato JSON:
            {{
                "pontos_fortes": ["ponto1", "ponto2", ...],
                "pontos_fracos": ["ponto1", "ponto2", ...],
                "riscos": ["risco1", "risco2", ...],
                "oportunidades": ["oportunidade1", "oportunidade2", ...],
                "sugestoes_melhoria": ["sugestao1", "sugestao2", ...]
            }}
            """
            analysis_text = self._generate_content(analysis_prompt)
            analysis = self._parse_json_response(analysis_text)

            # Step 2: Legal Basis Enhancement
            basis_prompt = f"""
            Com base na análise do caso, aprimore a fundamentação jurídica.
            Considere os pontos fortes, fracos, riscos e oportunidades identificados.
            
            Análise do caso:
            {json.dumps(analysis, indent=2, ensure_ascii=False)}
            
            Forneça uma fundamentação jurídica aprimorada, incluindo:
            1. Base legal mais robusta
            2. Jurisprudência relevante
            3. Argumentos complementares
            4. Contrarrazões a possíveis objeções
            """
            basis = self._generate_content(basis_prompt)

            # Step 3: Document Drafting
            drafting_prompt = f"""
            Elabore uma peça jurídica formal e bem estruturada, incluindo:
            1. Qualificação das partes
            2. Dos fatos
            3. Do direito
            4. Dos pedidos
            
            Utilize a análise do caso e a fundamentação aprimorada como base.
            
            Análise do caso:
            {json.dumps(analysis, indent=2, ensure_ascii=False)}
            
            Fundamentação aprimorada:
            {basis}
            """
            document = self._generate_content(drafting_prompt)

            # Step 4: Document Review
            review_prompt = f"""
            Revise a peça jurídica elaborada e forneça um parecer estruturado em formato JSON:
            
            Documento:
            {document}
            
            Forneça a revisão no seguinte formato JSON:
            {{
                "estrutura": "avaliação da estrutura do documento",
                "clareza": "avaliação da clareza do documento",
                "coerencia": "avaliação da coerência do documento",
                "sugestoes_melhoria": ["sugestao1", "sugestao2", ...]
            }}
            """
            review_text = self._generate_content(review_prompt)
            review = self._parse_json_response(review_text)

            return {
                "status": "success",
                "document": document,
                "analysis": analysis,
                "basis": basis,
                "review": review
            }

        except Exception as e:
            return {
                "status": "error",
                "error": f"Erro durante o processamento do caso: {str(e)}"
            } 