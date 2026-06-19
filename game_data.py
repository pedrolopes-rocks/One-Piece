from __future__ import annotations

from collections import OrderedDict


ROLES = OrderedDict(
    {
        "Líder": {
            "icon": "☠️",
            "description": (
                "Amplia os atributos do time e pode recrutar um inimigo "
                "derrotado por meio de uma rolagem."
            ),
        },
        "Vice-líder": {
            "icon": "⭐",
            "description": (
                "Assume o comando se o líder cair. Sua liderança determina "
                "quanto do bônus original será preservado."
            ),
        },
        "Atacante": {
            "icon": "⚔️",
            "description": (
                "Causa mais dano e tem maior chance de eliminar, mas também "
                "fica mais exposto aos ataques inimigos."
            ),
        },
        "Defensor": {
            "icon": "🛡️",
            "description": (
                "Pode interceptar golpes destinados a aliados e se sacrificar "
                "para manter membros importantes vivos."
            ),
        },
        "Espião": {
            "icon": "🗡️",
            "description": (
                "Pode eliminar um oponente antes da primeira rodada, correndo "
                "também o risco de morrer durante a infiltração."
            ),
        },
        "Tático": {
            "icon": "🧭",
            "description": (
                "Aumenta ou reduz a eficiência de todas as outras funções "
                "conforme sua pontuação tática."
            ),
        },
    }
)


def character(
    name: str,
    roles: tuple[str, ...],
    attack: int,
    defense: int,
    rank: str,
    *,
    leadership: int = 0,
    vice: int = 0,
    assault: int = 0,
    guard: int = 0,
    espionage: int = 0,
    tactics: int = 0,
    faction: str,
) -> dict:
    return {
        "name": name,
        "roles": list(roles),
        "attack": attack,
        "defense": defense,
        "rank": rank,
        "faction": faction,
        "skills": {
            "Líder": leadership,
            "Vice-líder": vice,
            "Atacante": assault,
            "Defensor": guard,
            "Espião": espionage,
            "Tático": tactics,
        },
    }


# Escala inicial do East Blue: 1 a 10. Regiões futuras podem ultrapassar 10.
CHARACTERS = [
    character(
        "Luffy",
        ("Líder", "Atacante"),
        8,
        7,
        "A",
        leadership=9,
        assault=8,
        faction="Chapéus de Palha",
    ),
    character(
        "Zoro",
        ("Vice-líder", "Atacante"),
        9,
        7,
        "A",
        vice=9,
        assault=9,
        faction="Chapéus de Palha",
    ),
    character(
        "Nami",
        ("Tático", "Espião"),
        3,
        4,
        "B",
        espionage=8,
        tactics=10,
        faction="Chapéus de Palha",
    ),
    character(
        "Usopp",
        ("Líder", "Tático"),
        4,
        3,
        "B",
        leadership=6,
        tactics=8,
        faction="Chapéus de Palha",
    ),
    character(
        "Sanji",
        ("Atacante", "Tático"),
        8,
        7,
        "A",
        assault=8,
        tactics=7,
        faction="Chapéus de Palha",
    ),
    character(
        "Koby",
        ("Tático",),
        2,
        3,
        "C",
        tactics=5,
        faction="Marinha",
    ),
    character(
        "Helmeppo",
        ("Espião",),
        2,
        2,
        "D",
        espionage=4,
        faction="Marinha",
    ),
    character(
        "Morgan",
        ("Líder", "Espião"),
        6,
        6,
        "B",
        leadership=6,
        espionage=3,
        faction="Marinha",
    ),
    character(
        "Garp",
        ("Líder", "Defensor"),
        9,
        10,
        "S",
        leadership=10,
        guard=10,
        faction="Marinha",
    ),
    character(
        "Buggy",
        ("Líder", "Tático"),
        6,
        5,
        "B",
        leadership=7,
        tactics=7,
        faction="Piratas do Buggy",
    ),
    character(
        "Kabaji",
        ("Vice-líder", "Atacante"),
        6,
        5,
        "B",
        vice=6,
        assault=6,
        faction="Piratas do Buggy",
    ),
    character(
        "Mohji",
        ("Defensor",),
        5,
        6,
        "C",
        guard=6,
        faction="Piratas do Buggy",
    ),
    character(
        "Richie",
        ("Atacante", "Defensor"),
        7,
        6,
        "B",
        assault=7,
        guard=7,
        faction="Piratas do Buggy",
    ),
    character(
        "Alvida",
        ("Líder", "Defensor"),
        6,
        7,
        "B",
        leadership=6,
        guard=7,
        faction="Piratas da Alvida",
    ),
    character(
        "Zeff",
        ("Tático", "Defensor"),
        7,
        8,
        "A",
        guard=8,
        tactics=9,
        faction="Baratie",
    ),
    character(
        "Krieg",
        ("Atacante", "Tático"),
        8,
        8,
        "A",
        assault=8,
        tactics=7,
        faction="Piratas do Krieg",
    ),
    character(
        "Gin",
        ("Vice-líder",),
        8,
        7,
        "A",
        vice=8,
        faction="Piratas do Krieg",
    ),
    character(
        "Mihawk",
        ("Atacante",),
        10,
        9,
        "S",
        assault=10,
        faction="Independente",
    ),
    character(
        "Yosaku",
        ("Defensor",),
        4,
        5,
        "C",
        guard=5,
        faction="Caçadores de Recompensa",
    ),
    character(
        "Johnny",
        ("Defensor",),
        4,
        5,
        "C",
        guard=5,
        faction="Caçadores de Recompensa",
    ),
    character(
        "Arlong",
        ("Líder", "Vice-líder"),
        8,
        8,
        "A",
        leadership=8,
        vice=8,
        faction="Piratas do Arlong",
    ),
    character(
        "Hacchi",
        ("Atacante",),
        7,
        7,
        "B",
        assault=7,
        faction="Piratas do Arlong",
    ),
    character(
        "Kuroobi",
        ("Atacante", "Defensor"),
        7,
        8,
        "B",
        assault=7,
        guard=8,
        faction="Piratas do Arlong",
    ),
    character(
        "Chew",
        ("Atacante", "Tático"),
        6,
        5,
        "B",
        assault=6,
        tactics=6,
        faction="Piratas do Arlong",
    ),
]

CHARACTER_BY_NAME = {item["name"]: item for item in CHARACTERS}

RANK_ORDER = {"S": 5, "A": 4, "B": 3, "C": 2, "D": 1}


LOCATIONS = [
    {
        "name": "Porto de Foosha",
        "subtitle": "Formação da tripulação",
        "x": 8,
        "y": 76,
    },
    {
        "name": "Shells Town",
        "subtitle": "A tirania de Morgan",
        "x": 25,
        "y": 55,
    },
    {
        "name": "Orange Town",
        "subtitle": "O circo de Buggy",
        "x": 42,
        "y": 68,
    },
    {
        "name": "Baratie",
        "subtitle": "A frota de Krieg",
        "x": 58,
        "y": 42,
    },
    {
        "name": "Arlong Park",
        "subtitle": "O domínio de Arlong",
        "x": 75,
        "y": 56,
    },
    {
        "name": "Reverse Mountain",
        "subtitle": "Entrada da Grand Line",
        "x": 91,
        "y": 24,
    },
]


STAGES = [
    {
        "location_index": 1,
        "name": "Shells Town",
        "boss": "Morgan",
        "enemies": ["Morgan", "Helmeppo", "Koby"],
        "difficulty": 0.75,
        "description": "Derrube o Capitão Morgan e liberte a base da Marinha.",
        "reward": 500,
    },
    {
        "location_index": 2,
        "name": "Orange Town",
        "boss": "Buggy",
        "enemies": ["Buggy", "Kabaji", "Mohji", "Richie", "Alvida"],
        "difficulty": 0.85,
        "description": "Sobreviva ao espetáculo caótico dos Piratas do Buggy.",
        "reward": 900,
    },
    {
        "location_index": 3,
        "name": "Baratie",
        "boss": "Krieg",
        "enemies": ["Krieg", "Gin", "Mihawk"],
        "difficulty": 0.90,
        "enemy_adjustments": {
            "Mihawk": {"attack": 7, "defense": 7, "hp_multiplier": 0.70}
        },
        "description": (
            "Defenda o restaurante de Krieg. Mihawk aparece como um encontro "
            "limitado para manter a escala do East Blue."
        ),
        "reward": 1_400,
    },
    {
        "location_index": 4,
        "name": "Arlong Park",
        "boss": "Arlong",
        "enemies": ["Arlong", "Hacchi", "Kuroobi", "Chew"],
        "difficulty": 1.00,
        "description": "Rompa as defesas dos Homens-Peixe e derrote Arlong.",
        "reward": 2_000,
    },
    {
        "location_index": 5,
        "name": "Reverse Mountain",
        "boss": "Garp",
        "enemies": ["Garp", "Morgan", "Koby", "Helmeppo"],
        "difficulty": 1.05,
        "enemy_adjustments": {
            "Garp": {"attack": 8, "defense": 8, "hp_multiplier": 0.85}
        },
        "description": (
            "Último bloqueio da Marinha antes da subida para a Grand Line. "
            "Vença para concluir a demo."
        ),
        "reward": 3_000,
    },
]

