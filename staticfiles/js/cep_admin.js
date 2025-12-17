/* core/static/js/cep_admin.js */

document.addEventListener("DOMContentLoaded", function() {
    // Mapeamento dos IDs gerados pelo Django Admin
    const cepInput = document.getElementById('id_cep');
    const ruaInput = document.getElementById('id_endereco');
    const bairroInput = document.getElementById('id_bairro');
    const cidadeInput = document.getElementById('id_cidade');
    const estadoInput = document.getElementById('id_estado');
    const localTrabalhoInput = document.getElementById('id_local_trabalho_estado');

    // Mapeamento de Sigla para Nome Completo
    const estadosNomes = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AP': 'Amapá', 'AM': 'Amazonas', 'BA': 'Bahia',
        'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo', 'GO': 'Goiás',
        'MA': 'Maranhão', 'MT': 'Mato Grosso', 'MS': 'Mato Grosso do Sul', 'MG': 'Minas Gerais',
        'PA': 'Pará', 'PB': 'Paraíba', 'PR': 'Paraná', 'PE': 'Pernambuco', 'PI': 'Piauí',
        'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte', 'RS': 'Rio Grande do Sul',
        'RO': 'Rondônia', 'RR': 'Roraima', 'SC': 'Santa Catarina', 'SP': 'São Paulo',
        'SE': 'Sergipe', 'TO': 'Tocantins'
    };

    if (cepInput) {
        cepInput.addEventListener('blur', function() {
            // Remove tudo que não é número
            let cep = this.value.replace(/\D/g, '');

            if (cep.length === 8) {
                // Consulta a API ViaCEP
                fetch(`https://viacep.com.br/ws/${cep}/json/`)
                    .then(response => response.json())
                    .then(data => {
                        if (!data.erro) {
                            // Preenche os campos de endereço
                            if(ruaInput) ruaInput.value = data.logradouro;
                            if(bairroInput) bairroInput.value = data.bairro;
                            if(cidadeInput) cidadeInput.value = data.localidade;
                            if(estadoInput) estadoInput.value = data.uf;

                            // Define o Local de Trabalho com o nome do Estado
                            if(localTrabalhoInput) {
                                const nomeCompleto = estadosNomes[data.uf] || data.uf;
                                localTrabalhoInput.value = nomeCompleto;
                            }
                        } else {
                            alert("CEP não encontrado.");
                        }
                    })
                    .catch(error => {
                        console.error('Erro na busca:', error);
                    });
            }
        });
    }
});