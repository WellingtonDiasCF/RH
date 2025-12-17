import os
import django
import requests
import time
import dotenv

# 1. Configuração do Django
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from core_rh.models import Funcionario

# Mapeamento de Estados (Igual ao seu JS)
ESTADOS_NOMES = {
    'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia',
    'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás',
    'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
    'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí',
    'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul',
    'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo',
    'SE': 'Sergipe', 'TO': 'Tocantins'
}

def atualizar():
    print("--- INICIANDO ATUALIZAÇÃO DE ENDEREÇOS ---")
    
    # Pega todos os funcionários que têm CEP preenchido
    funcionarios = Funcionario.objects.exclude(cep__isnull=True).exclude(cep='')
    
    total = funcionarios.count()
    print(f"Encontrados {total} funcionários com CEP para verificar.")

    atualizados = 0
    erros = 0

    for func in funcionarios:
        cep_limpo = "".join(filter(str.isdigit, func.cep))
        
        if len(cep_limpo) != 8:
            print(f"PULANDO: {func.nome_completo} - CEP Inválido ({func.cep})")
            continue

        try:
            # Consulta a API (Mesma do JS)
            response = requests.get(f"https://viacep.com.br/ws/{cep_limpo}/json/")
            data = response.json()

            if 'erro' not in data:
                # Atualiza os dados
                func.endereco = data.get('logradouro', '')
                func.bairro = data.get('bairro', '')
                func.cidade = data.get('localidade', '')
                func.estado = data.get('uf', '')
                
                # Atualiza o Local de Trabalho (Estado por extenso)
                uf = data.get('uf', '')
                nome_estado_extenso = ESTADOS_NOMES.get(uf, uf)
                func.local_trabalho_estado = nome_estado_extenso
                
                # Salva no banco (mas evita rodar a lógica pesada de usuário do save() original se possível, 
                # ou roda normal para garantir)
                func.save()
                
                print(f"OK: {func.nome_completo} -> {func.cidade}/{func.estado}")
                atualizados += 1
            else:
                print(f"VIACEP ERRO: CEP não encontrado para {func.nome_completo} ({cep_limpo})")
                erros += 1

            # Pausa pequena para não bloquear a API por excesso de requisições
            time.sleep(0.3)

        except Exception as e:
            print(f"ERRO TÉCNICO em {func.nome_completo}: {e}")
            erros += 1

    print(f"\n--- FIM ---")
    print(f"Atualizados: {atualizados}")
    print(f"Erros/Não encontrados: {erros}")

if __name__ == '__main__':
    atualizar()
