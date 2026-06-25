from __future__ import annotations

from collections import OrderedDict
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile


ROLES = OrderedDict(
    {
        "Capitão": {
            "icon": "☠️",
            "description": (
                "Aumenta o poder de combate da tripulação e melhora a chance "
                "de recrutar adversários após uma vitória."
            ),
        },
        "Imediato": {
            "icon": "⭐",
            "description": (
                "Assume o comando quando o Capitão é derrotado e preserva "
                "parte do bônus de combate da equipe."
            ),
        },
        "Atacante": {
            "icon": "⚔️",
            "description": "Recebe pontos adicionais de ataque em combate.",
        },
        "Defensor": {
            "icon": "🛡️",
            "description": (
                "Recebe pontos adicionais de defesa e pode interceptar "
                "golpes destinados a aliados."
            ),
        },
        "Tático": {
            "icon": "🧭",
            "description": "Aumenta a chance de golpes críticos da equipe.",
        },
        "Espião": {
            "icon": "🗡️",
            "description": (
                "Pode ferir ou eliminar um inimigo antes da batalha, mas "
                "também corre o risco de sofrer dano na infiltração."
            ),
        },
    }
)

RANK_ORDER = {
    "SSS": 9,
    "SS": 8,
    "S": 7,
    "A": 6,
    "B": 5,
    "C": 4,
    "D": 3,
    "E": 2,
    "F": 1,
}

# Valor interno representativo de cada faixa. A interface mostra somente o rank.
RANK_SCORE = {
    "SSS": 100,
    "SS": 97,
    "S": 92,
    "A": 85,
    "B": 75,
    "C": 65,
    "D": 55,
    "E": 40,
    "F": 15,
}

ROLE_ALIASES = {
    "Líder": "Capitão",
    "LÃ­der": "CapitÃ£o",
    "Vice-líder": "Imediato",
    "Vice-lÃ­der": "Imediato",
}

PHASE_TO_ARC = {
    "Blue": "East Blue",
    "Paraíso": "Paraíso",
    "ParaÃ­so": "ParaÃ­so",
}

DATA_FILE = Path(__file__).with_name("assets") / "rei_dos_mares.xlsx"
_MAIN_NS = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_REL_NS = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"


def _read_workbook(path: Path) -> dict[str, list[dict[str, str]]]:
    """Read the small game workbook without requiring openpyxl at runtime."""
    namespaces = {"m": _MAIN_NS, "r": _REL_NS}
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            shared_strings = [
                "".join(
                    node.text or ""
                    for node in item.iterfind(".//m:t", namespaces)
                )
                for item in root.findall("m:si", namespaces)
            ]

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relationships = ET.fromstring(
            archive.read("xl/_rels/workbook.xml.rels")
        )
        targets = {
            item.attrib["Id"]: item.attrib["Target"]
            for item in relationships
        }
        sheets: dict[str, list[dict[str, str]]] = {}

        for sheet in workbook.find("m:sheets", namespaces) or []:
            relation_id = sheet.attrib[f"{{{_REL_NS}}}id"]
            target = targets[relation_id]
            sheet_path = (
                target if target.startswith("xl/") else f"xl/{target.lstrip('/')}"
            )
            root = ET.fromstring(archive.read(sheet_path))
            rows: list[dict[str, str]] = []
            for row in root.findall(".//m:sheetData/m:row", namespaces):
                values: dict[str, str] = {}
                for cell in row.findall("m:c", namespaces):
                    reference = cell.attrib.get("r", "")
                    match = re.match(r"[A-Z]+", reference)
                    if not match:
                        continue
                    column = match.group(0)
                    value_node = cell.find("m:v", namespaces)
                    cell_type = cell.attrib.get("t")
                    if cell_type == "s" and value_node is not None:
                        value = shared_strings[int(value_node.text or "0")]
                    elif cell_type == "inlineStr":
                        value = "".join(
                            node.text or ""
                            for node in cell.iterfind(".//m:t", namespaces)
                        )
                    else:
                        value = value_node.text if value_node is not None else ""
                    values[column] = (value or "").strip()
                if values.get("A"):
                    rows.append(values)
            sheets[sheet.attrib["name"]] = rows
    return sheets


def _normalize_role(role: str) -> str:
    return ROLE_ALIASES.get(role, role)


def _rank_value(rank: str) -> int:
    if rank not in RANK_SCORE:
        raise ValueError(f"Rank desconhecido na planilha: {rank!r}")
    return RANK_SCORE[rank]


def _rank_from_number(value: str) -> str | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number >= 100:
        return "SSS"
    if number >= 95:
        return "SS"
    if number >= 90:
        return "S"
    if number >= 80:
        return "A"
    if number >= 70:
        return "B"
    if number >= 60:
        return "C"
    if number >= 50:
        return "D"
    if number >= 30:
        return "E"
    return "F"


def _coerce_rank(row: dict[str, str], rank_column: str, value_column: str) -> str:
    rank = row.get(rank_column, "")
    if rank in RANK_SCORE:
        return rank
    adjacent = row.get(value_column, "")
    if adjacent in RANK_SCORE:
        return adjacent
    inferred = _rank_from_number(adjacent) or _rank_from_number(rank)
    if inferred:
        return inferred
    raise ValueError(
        f"Rank desconhecido para {row.get('A', 'personagem')}: {rank!r}"
    )


def _character_from_row(row: dict[str, str], *, enemy: bool) -> dict:
    roles = [_normalize_role(row["F"])]
    role_ranks = {roles[0]: row["G"]}
    if row.get("H"):
        second_role = _normalize_role(row["H"])
        roles.append(second_role)
        role_ranks[second_role] = row["I"]

    draw_groups = [
        group for group in (row.get("C"), row.get("D")) if group
    ]
    attack_rank = _coerce_rank(row, "J", "K")
    defense_rank = _coerce_rank(row, "L", "M")
    hp_rank = _coerce_rank(row, "N", "O")
    combat_rank = _coerce_rank(row, "P", "P")
    character = {
        "name": row["A"],
        "faction": row.get("B") or row.get("C") or "Sem filiação",
        "draw_groups": draw_groups,
        "arc": row.get("E", ""),
        "roles": roles,
        "role_ranks": role_ranks,
        "skills": {
            role: RANK_SCORE[role_rank]
            for role, role_rank in role_ranks.items()
        },
        "attack_rank": attack_rank,
        "attack": _rank_value(attack_rank),
        "defense_rank": defense_rank,
        "defense": _rank_value(defense_rank),
        "hp_rank": hp_rank,
        "max_hp": _rank_value(hp_rank),
        "rank": combat_rank,
        "combat": _rank_value(combat_rank),
        "enemy": enemy,
    }
    if enemy:
        character["recruitment_chance"] = (
            float(row["Q"]) if row.get("Q") else None
        )
    return character


def _split_required_names(value: str) -> list[str]:
    names = []
    for raw_name in value.split(" - "):
        name = raw_name.strip()
        if not name:
            continue
        name = re.sub(r"\s*\(.*$", "", name).strip()
        if name == "Benn Beckmann":
            name = "Benn Beckman"
        if name == "Kaliffa":
            name = "Kalifa"
        names.append(name)
    return names


def _boss_from_row(row: dict[str, str]) -> dict:
    phase = row.get("D", "")
    return {
        "id": f"{phase}:{row['A']}:{row.get('B', '')}",
        "name": row["A"],
        "faction": row.get("B", ""),
        "required_names": _split_required_names(row.get("C", "")),
        "phase": phase,
        "arc": PHASE_TO_ARC.get(phase, phase),
        "effect": row.get("E", ""),
    }


_WORKBOOK = _read_workbook(DATA_FILE)
PLAYABLE_CHARACTERS = [
    _character_from_row(row, enemy=False)
    for row in _WORKBOOK["Personagens jogáveis"][1:]
    if row.get("J")
]
ENEMY_CHARACTERS = [
    _character_from_row(row, enemy=True)
    for row in _WORKBOOK["Personagens Inimigos"][1:]
    if row.get("J")
]
BOSSES = [
    _boss_from_row(row)
    for row in _WORKBOOK.get("Bosses", [])[1:]
    if row.get("A")
]

# Alias mantido para reduzir o impacto em estados e imports antigos.
CHARACTERS = PLAYABLE_CHARACTERS
PLAYABLE_BY_NAME = {item["name"]: item for item in PLAYABLE_CHARACTERS}
ENEMY_BY_NAME = {item["name"]: item for item in ENEMY_CHARACTERS}
CHARACTER_BY_NAME = {**ENEMY_BY_NAME, **PLAYABLE_BY_NAME}
BOSSES_BY_PHASE = {
    phase: [boss for boss in BOSSES if boss["phase"] == phase]
    for phase in PHASE_TO_ARC
}

PLAYABLE_DRAW_GROUPS = sorted(
    {
        group
        for character in PLAYABLE_CHARACTERS
        for group in character["draw_groups"]
    }
)
ENEMY_GROUPS = sorted(
    {
        group
        for character in ENEMY_CHARACTERS
        for group in character["draw_groups"]
    }
)


LOCATIONS = [
    {
        "name": "Porto de Foosha",
        "subtitle": "Formação da tripulação",
        "x": 7,
        "y": 66,
    },
    {
        "name": "Shell's Town",
        "subtitle": "A força da Marinha",
        "x": 16,
        "y": 48,
    },
    {
        "name": "Orange Town",
        "subtitle": "O circo de Buggy",
        "x": 25,
        "y": 66,
    },
    {
        "name": "Baratie",
        "subtitle": "A frota de Krieg",
        "x": 34,
        "y": 38,
    },
    {
        "name": "Arlong Park",
        "subtitle": "O domínio de Arlong",
        "x": 43,
        "y": 54,
    },
    {
        "name": "Reverse Mountain",
        "subtitle": "Entrada da Grand Line",
        "x": 50,
        "y": 48,
    },
    {
        "name": "Whiskey Peak",
        "subtitle": "Primeiros passos no Paraíso",
        "x": 58,
        "y": 54,
    },
    {
        "name": "Little Garden",
        "subtitle": "Ilha ancestral",
        "x": 67,
        "y": 66,
    },
    {
        "name": "Alabasta",
        "subtitle": "Reino em guerra",
        "x": 76,
        "y": 38,
    },
    {
        "name": "Jaya",
        "subtitle": "Rota para o céu",
        "x": 85,
        "y": 56,
    },
    {
        "name": "Enies Lobby",
        "subtitle": "Justiça mundial",
        "x": 94,
        "y": 40,
    },
]


STAGES = [
    {
        "location_index": 1,
        "name": "Shell's Town",
        "phase": "Blue",
        "arc": "East Blue",
        "description": "Enfrente a primeira filiação que cruzar sua rota.",
        "reward": 500,
    },
    {
        "location_index": 2,
        "name": "Orange Town",
        "phase": "Blue",
        "arc": "East Blue",
        "description": "Uma nova tripulação disputa o controle da rota.",
        "reward": 900,
    },
    {
        "location_index": 3,
        "name": "Baratie",
        "phase": "Blue",
        "arc": "East Blue",
        "description": "As filiações mais perigosas começam a se aproximar.",
        "reward": 1_400,
    },
    {
        "location_index": 4,
        "name": "Arlong Park",
        "phase": "Blue",
        "arc": "East Blue",
        "description": "A disputa pelo East Blue chega ao seu ponto crítico.",
        "reward": 2_000,
    },
    {
        "location_index": 5,
        "name": "Reverse Mountain",
        "phase": "Blue",
        "arc": "East Blue",
        "boss_slot": True,
        "description": "Supere uma filiação de alto nível antes da Grand Line.",
        "reward": 3_000,
    },
    {
        "location_index": 6,
        "name": "Whiskey Peak",
        "phase": "Paraíso",
        "arc": "Paraíso",
        "description": "O Paraíso abre sua rota com emboscadas e alianças frágeis.",
        "reward": 3_800,
    },
    {
        "location_index": 7,
        "name": "Little Garden",
        "phase": "Paraíso",
        "arc": "Paraíso",
        "description": "Tripulações rivais disputam território em uma ilha primitiva.",
        "reward": 4_600,
    },
    {
        "location_index": 8,
        "name": "Alabasta",
        "phase": "Paraíso",
        "arc": "Paraíso",
        "description": "A guerra do deserto coloca a tripulação contra forças maiores.",
        "reward": 5_500,
    },
    {
        "location_index": 9,
        "name": "Jaya",
        "phase": "Paraíso",
        "arc": "Paraíso",
        "description": "Rumores, caçadores e piratas se cruzam antes do próximo salto.",
        "reward": 6_400,
    },
    {
        "location_index": 10,
        "name": "Enies Lobby",
        "phase": "Paraíso",
        "arc": "Paraíso",
        "boss_slot": True,
        "description": "A rota do Paraíso termina contra uma força decisiva.",
        "reward": 8_000,
    },
]
