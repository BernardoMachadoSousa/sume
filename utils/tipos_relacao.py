"""
Tipos de relação semântica — vocabulário controlado pra grafo de conhecimento pessoal.

Cada tipo define o significado de um link de entidade a outra, além de propriedades extra opicionais (dirigibilidade, transitividade, etc.).
"""

from dataclasses import dataclass
from typing import Dict, Any

@dataclass
class RelacaoSemantica:
    tipo: str
    dirigivel: bool = True            # Quem é sujeito (sujeito) e quem é objeto
    transitivo: bool = False          # Se A R B e B R C => A R C
    tempo: bool = False               # Requer marcação de tempo (passado, presente, futuro)
    descricao: str = ""
    exemplos: list[str] = None

# Vocabulário completo de tipos de relacionamento semântico (pouco extenso, focado em casos de uso pessoais, jurídicos e acadêmicos)

TIPOS_RELACAO: Dict[str, RelacaoSemantica] = {
    # Relações básicas de posse/atribuição
    "possui": RelacaoSemantica(
        tipo="possui",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A possui/entrega/entra em posse de entidade B (ex: 'possui um carro')",
        exemplos=["possui um carro", "possui casa", "possui membro da equipe"]
    ),
    "pertence_a": RelacaoSemantica(
        tipo="pertence_a",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A pertence a uma categoria, grupo ou tipo B",
        exemplos=["pertence ao time X", "pertence ao partido Y", "pertence à família Z"]
    ),

    # Relações geográficas
    "mora_em": RelacaoSemantica(
        tipo="mora_em",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A mora/atualmente vive em lugar B; pode ter período temporal (passado/presente/futuro)",
        exemplos=["mora em Salvador", "mora em Salvador (desde janeiro de 2024)"]
    ),
    "trabalha_em": RelacaoSemantica(
        tipo="trabalha_em",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A trabalha/atualmente trabalha em organização/lugar B",
        exemplos=["trabalha na UFMG", "trabalha no Senado (2022–presente)"]
    ),
    "estuda": RelacaoSemantica(
        tipo="estuda",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A estuda/atualmente estuda disciplina, curso ou instituição B",
        exemplos=["estuda Direito na UFMG", "estudou Medicina na USP"]
    ),
    "ensina": RelacaoSemantica(
        tipo="ensina",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A ensina/atualmente ensina disciplina ou curso B",
        exemplos=["ensina Direito Processual"]
    ),
    "conhece": RelacaoSemantica(
        tipo="conhece",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A conhece entidade B pessoalmente ou profissionalmente",
        exemplos=["conhece Paulo", "conhece a teoria da relatividade"]
    ),
    "gosta_de": RelacaoSemantica(
        tipo="gosta_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A gosta/é apaixonada por coisa/entidade B",
        exemplos=["gosta de jazz", "gosta da obra de Nietzsche"]
    ),

    # Relações de desenvolvimento/criação
    "desenvolve": RelacaoSemantica(
        tipo="desenvolve",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A desenvolve ou cria/entidade/conceito B (ex: projeto, software, paper)",
        exemplos=["desenvolve Sumé", "desenvolve aplicação móvel"]
    ),
    "cria": RelacaoSemantica(
        tipo="cria",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A cria ou produz coisa/entidade B",
        exemplos=["cria notas no Obsidian"]
    ),

    # Relações familiares
    "e_pai_de": RelacaoSemantica(
        tipo="e_pai_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é pai de entidade B",
        exemplos=["é pai de Maria"]
    ),
    "e_mae_de": RelacaoSemantica(
        tipo="e_mae_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é mãe de entidade B",
        exemplos=["é mãe de Bernardo"]
    ),
    "e_irmao_de": RelacaoSemantica(
        tipo="e_irmao_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é irmão de entidade B",
        exemplos=["é irmão de Ana"]
    ),
    "e_irma_de": RelacaoSemantica(
        tipo="e_irma_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é irmã de entidade B",
        exemplos=["é irmã de Carla"]
    ),
    "e_filho_de": RelacaoSemantica(
        tipo="e_filho_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é filho de entidade B",
        exemplos=["é filho de Paulo"]
    ),
    "e_filha_de": RelacaoSemantica(
        tipo="e_filha_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é filha de entidade B",
        exemplos=["é filha de Juliana"]
    ),
    "e_cunhado_de": RelacaoSemantica(
        tipo="e_cunhado_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é cunhado de entidade B (casado com irmão/irmã)",
        exemplos=["é cunhado de Roberto"]
    ),

    # Relações de parceria/úteis
    "namora": RelacaoSemantica(
        tipo="namora",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A namora/atualmente namora entidade B (relacionamento romântico)",
        exemplos=["namora com Ana Maria", "namorou com Luiza"]
    ),
    "e_marido_de": RelacaoSemantica(
        tipo="e_marido_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é marido de entidade B",
        exemplos=["é marido de Helena"]
    ),
    "e_esposa_de": RelacaoSemantica(
        tipo="e_esposa_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é esposa de entidade B",
        exemplos=["é esposa de Marcos"]
    ),
    "e_noiva_de": RelacaoSemantica(
        tipo="e_noiva_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é noiva de entidade B",
        exemplos=["é noiva de Sofia"]
    ),

    # Relações comparativas/de estado
    "igual_a": RelacaoSemantica(
        tipo="igual_a",
        dirigivel=True,
        transitivo=True,
        tempo=False,
        descricao="Entidade A é equivalente a/conceito/entidade B (mesma coisa)",
        exemplos=["é igual a Lei 13.709"]
    ),
    "similar_a": RelacaoSemantica(
        tipo="similar_a",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é semelhante a/conceito B (próximo, relacionado, mas não idêntico)",
        exemplos=["é similar a Direito Penal"]
    ),
    "contradiz": RelacaoSemantica(
        tipo="contradiz",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A contradiz afirmação/conhecimento/entidade B (oposição direta)",
        exemplos=["contradiz teoria clássica"]
    ),
    "corrige": RelacaoSemantica(
        tipo="corrige",
        dirigivel=False,
        transitivo=False,
        tempo=True,
        descricao="Entidade A corrige informação anterior (ex: 'corrige idade')",
        exemplos=["corrige idade (21 → 22)"]
    ),
    "sucessora_a": RelacaoSemantica(
        tipo="sucessora_a",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A é sucessora/atual sucessora de versão/anterior entidade B",
        exemplos=["é sucessora do v1.0"]
    ),

    # Relações temporais/de acontecimento
    "aconteceu_em": RelacaoSemantica(
        tipo="aconteceu_em",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A aconteceu/occorreu em local/tempo B (evento)",
        exemplos=["aconteceu em 2024"]
    ),
    "começou_em": RelacaoSemantica(
        tipo="começou_em",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A começou seu período/atividade em B",
        exemplos=["começou em 2020"]
    ),
    "termina_em": RelacaoSemantica(
        tipo="termina_em",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A termina/se encerra em B",
        exemplos=["termina em 31/12/2024"]
    ),

    # Relações de dependência e substituição
    "substitui": RelacaoSemantica(
        tipo="substitui",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A substitui/antiga/entidade B (novo substitui velho)",
        exemplos=["substitui v1 por v2"]
    ),
    "depende_de": RelacaoSemantica(
        tipo="depende_de",
        dirigivel=True,
        transitivo=True,
        tempo=False,
        descricao="Entidade A depende de entidade B; se B não existe, A não pode existir (ex: código base)",
        exemplos=["depende de banco de dados"]
    ),

    # Relações de atributo/meta-dado
    "tem_idade": RelacaoSemantica(
        tipo="tem_idade",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A tem atributo de idade B anos",
        exemplos=["tem idade 21"]
    ),
    "tem_genero": RelacaoSemantica(
        tipo="tem_genero",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A tem atributo de gênero B",
        exemplos=["tem gênero masculino"]
    ),
    "tem_cor": RelacaoSemantica(
        tipo="tem_cor",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A tem atributo de cor B",
        exemplos=["tem cor azul"]
    ),
    "tem_tamanho": RelacaoSemantica(
        tipo="tem_tamanho",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A tem atributo de tamanho B",
        exemplos=["tem tamanho grande"]
    ),

    # Relações pedagógicas
    "ensina_conceito": RelacaoSemantica(
        tipo="ensina_conceito",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A ensina conceito/entidade B em contexto de ensino",
        exemplos=["ensina conceito de contrato"]
    ),
    "aprendeu_de": RelacaoSemantica(
        tipo="aprendeu_de",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A aprendeu estudou/conheceu entidade B em algum momento",
        exemplos=["aprendeu de Direito Civil"]
    ),
    "referencia": RelacaoSemantica(
        tipo="referencia",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A referencia/entidade B como fonte, citação, inspiração",
        exemplos=["referencia artigo 'X'"]
    ),

    # Relações de poder/contratação
    "contrata": RelacaoSemantica(
        tipo="contrata",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A contrata/serviço/entidade B (acordo comercial)",
        exemplos=["contrata advogado"]
    ),
    "emprega": RelacaoSemantica(
        tipo="emprega",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A emprega/entidade B como funcionário/obra",
        exemplos=["emprega engenheiro"]
    ),
    "patrocina": RelacaoSemantica(
        tipo="patrocina",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A patrocina projeto/entidade B (financiamento)",
        exemplos=["patrocina pesquisa"]
    ),

    # Relações de localização/de estabelecimento
    "estabelecido_em": RelacaoSemantica(
        tipo="estabelecido_em",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A foi estabelecida/fundada em local/tempo B",
        exemplos=["estabelecido em Salvador (1549)"]
    ),
    "localizado_em": RelacaoSemantica(
        tipo="localizado_em",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A está localizada/atualmente localizada em B (geográfico)",
        exemplos=["localizado em Belo Horizonte"]
    ),
    "origina_de": RelacaoSemantica(
        tipo="origina_de",
        dirigivel=True,
        transitivo=False,
        tempo=True,
        descricao="Entidade A tem origem em B (pessoa, objeto, ideia)",
        exemplos=["origina de Rio de Janeiro"]
    ),

    # Relações de afinidade/categorização
    "pertence_a_categoria": RelacaoSemantica(
        tipo="pertence_a_categoria",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A pertence à categoria/bairro/área B (classificação)",
        exemplos=["pertence à categoria Direito Público"]
    ),
    "tipo_de": RelacaoSemantica(
        tipo="tipo_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é o tipo/especie/entidade B (hierarquia)",
        exemplos=["tipo de veículo"]
    ),

    # Relações de influência e aprendizagem
    "influencia": RelacaoSemantica(
        tipo="influencia",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A influencia/entidade B (pensamento, política, comportamento)",
        exemplos=["influenciação por Kant"]
    ),
    "inspirado_por": RelacaoSemantica(
        tipo="inspirado_por",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é inspirado por/entidade B (creativo, emocional)",
        exemplos=["inspirado por obras-primas"]
    ),

    # Relações de formato e conteúdo
    "contem": RelacaoSemantica(
        tipo="contem",
        dirigivel=True,
        transitivo=True,
        tempo=False,
        descricao="Entidade A contem/inclui/entidade B (ex: documento contém seção)",
        exemplos=["contem introdução"]
    ),
    "baseado_em": RelacaoSemantica(
        tipo="baseado_em",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A é fundamentada/fundamenta em entidade B (ex: lei baseada em princípio)",
        exemplos=["baseado no artigo 5º"]
    ),
    "deriva_de": RelacaoSemantica(
        tipo="deriva_de",
        dirigivel=True,
        transitivo=False,
        tempo=False,
        descricao="Entidade A deriva de/entidade B (genealogia, desenvolvimento)",
        exemplos=["deriva de reformas anteriores"]
    ),
}
