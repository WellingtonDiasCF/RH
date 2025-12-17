import csv
import os
import django
import dotenv
import re
from datetime import date

# 1. Configuração
dotenv.load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from core_rh.models import Funcionario, Cargo, Equipe

# --- CONFIGURAÇÕES ---
ARQUIVO_CSV = 'importacao.csv'
SENHA_PADRAO = '123'

def limpar_cpf(cpf):
    if not cpf: return ""
    return "".join(filter(str.isdigit, cpf))

def parse_horario_inteligente(texto_horario):
    try:
        if not texto_horario: return '08:00', '12:00', '13:00', '18:00'
        # Busca HH:MM
        horarios = re.findall(r'\d{2}:\d{2}', texto_horario)
        if len(horarios) >= 4:
            return horarios[0], horarios[1], horarios[2], horarios[3]
    except:
        pass
    return '08:00', '12:00', '13:00', '18:00'

def importar():
    print("--- INICIANDO IMPORTAÇÃO ---")
    
    try:
        f = open(ARQUIVO_CSV, 'r', encoding='utf-8-sig')
        # TENTA LER COM PONTO E VÍRGULA (Padrão BR)
        leitor = csv.DictReader(f, delimiter=';')
    except:
        f = open(ARQUIVO_CSV, 'r', encoding='latin-1')
        leitor = csv.DictReader(f, delimiter=';')

    # --- DIAGNÓSTICO (Para sabermos o que está acontecendo) ---
    print(f"Colunas encontradas no arquivo: {leitor.fieldnames}")
    
    if not leitor.fieldnames or 'Nome Completo' not in leitor.fieldnames:
        print("ALERTA CRÍTICO: A coluna 'Nome Completo' não foi achada.")
        print("Verifique se o separador é mesmo ';' ou se o nome da coluna está diferente.")
    # -----------------------------------------------------------

    count = 0
    with f:
        for linha in leitor:
            try:
                # Remove espaços em branco das chaves e valores
                row = {k.strip(): v.strip() for k, v in linha.items() if k}

                nome = row.get('Nome Completo')
                cpf_raw = row.get('CPF')
                email = row.get('Email') or row.get('E-mail')
                cargo_nome = row.get('Cargo')
                equipe_nome = row.get('Equipe')
                contrato = row.get('Nº do Contrato')
                horario_str = row.get('Horário')
                cep = row.get('CEP')

                if not cpf_raw or not nome:
                    # Linha vazia ou inválida
                    continue

                cpf_limpo = limpar_cpf(cpf_raw)
                
                # Tratamento Horário
                ent, sai_alm, volt_alm, sai = parse_horario_inteligente(horario_str)
                texto_intervalo = f"{sai_alm} às {volt_alm}"

                # Cria Dependências
                cargo_obj, _ = Cargo.objects.get_or_create(titulo=cargo_nome)
                equipe_obj, _ = Equipe.objects.get_or_create(nome=equipe_nome)

                # Verifica usuário
                if User.objects.filter(username=cpf_limpo).exists():
                    print(f"PULANDO: {nome} (Usuário já existe)")
                    continue

                # Cria Login
                nomes = nome.split()
                first = nomes[0]
                last = ' '.join(nomes[1:]) if len(nomes) > 1 else ''

                user = User.objects.create_user(
                    username=cpf_limpo,
                    email=email,
                    password=SENHA_PADRAO,
                    first_name=first,
                    last_name=last
                )

                # Cria Funcionário
                Funcionario.objects.create(
                    usuario=user,
                    nome_completo=nome,
                    email=email,
                    cpf=cpf_limpo,
                    cargo=cargo_obj,
                    equipe=equipe_obj,
                    numero_contrato=contrato,
                    cep=cep,
                    data_admissao=date.today(),
                    primeiro_acesso=True,
                    jornada_entrada=ent,
                    jornada_saida=sai,
                    intervalo_padrao=texto_intervalo
                )
                
                print(f"SUCESSO: {nome}")
                count += 1

            except Exception as e:
                print(f"ERRO na linha de {linha.get('Nome Completo', 'Desconhecido')}: {e}")

    print(f"--- FIM. Total importados: {count} ---")

if __name__ == '__main__':
    importar()
