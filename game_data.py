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
            "description": "Recebe 5 pontos adicionais de ataque em combate.",
        },
        "Defensor": {
            "icon": "🛡️",
            "description": (
                "Recebe 5 pontos adicionais de defesa e pode interceptar "
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


def _character_from_row(row: dict[str, str], *, enemy: bool) -> dict:
    roles = [row["F"]]
    role_ranks = {row["F"]: row["G"]}
    if row.get("H"):
        roles.append(row["H"])
        role_ranks[row["H"]] = row["I"]

    draw_groups = [
        group for group in (row.get("C"), row.get("D")) if group
    ]
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
        "attack_rank": row["J"],
        "attack": int(float(row["K"])),
        "defense_rank": row["L"],
        "defense": int(float(row["M"])),
        "hp_rank": row["N"],
        "max_hp": int(float(row["O"])),
        "rank": row["P"],
        "enemy": enemy,
    }
    if enemy:
        character["recruitment_chance"] = float(row["Q"])
    return character


_WORKBOOK = _read_workbook(DATA_FILE)
PLAYABLE_CHARACTERS = [
    _character_from_row(row, enemy=False)
    for row in _WORKBOOK["Personagens jogáveis"][1:]
]
ENEMY_CHARACTERS = [
    _character_from_row(row, enemy=True)
    for row in _WORKBOOK["Personagens Inimigos"][1:]
]

# Alias mantido para reduzir o impacto em estados e imports antigos.
CHARACTERS = PLAYABLE_CHARACTERS
PLAYABLE_BY_NAME = {item["name"]: item for item in PLAYABLE_CHARACTERS}
ENEMY_BY_NAME = {item["name"]: item for item in ENEMY_CHARACTERS}
CHARACTER_BY_NAME = {**ENEMY_BY_NAME, **PLAYABLE_BY_NAME}

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
        "x": 8,
        "y": 76,
    },
    {
        "name": "Shell's Town",
        "subtitle": "A força da Marinha",
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
        "name": "Shell's Town",
        "description": "Enfrente a primeira filiação que cruzar sua rota.",
        "reward": 500,
    },
    {
        "location_index": 2,
        "name": "Orange Town",
        "description": "Uma nova tripulação disputa o controle da rota.",
        "reward": 900,
    },
    {
        "location_index": 3,
        "name": "Baratie",
        "description": "As filiações mais perigosas começam a se aproximar.",
        "reward": 1_400,
    },
    {
        "location_index": 4,
        "name": "Arlong Park",
        "description": "A disputa pelo East Blue chega ao seu ponto crítico.",
        "reward": 2_000,
    },
    {
        "location_index": 5,
        "name": "Reverse Mountain",
        "description": "Supere uma filiação de alto nível antes da Grand Line.",
        "reward": 3_000,
    },
]
