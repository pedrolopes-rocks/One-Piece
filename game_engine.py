from __future__ import annotations

import copy
import random
from typing import Callable, Iterable

from game_data import (
    BOSSES_BY_PHASE,
    CHARACTER_BY_NAME,
    ENEMY_CHARACTERS,
    ENEMY_GROUPS,
    PLAYABLE_CHARACTERS,
    PLAYABLE_DRAW_GROUPS,
    ROLES,
)


IMPORTANT_ROLES = {"Capitão", "Imediato", "Tático", "Espião"}
ISLAND_POWER_STEP = 0.20
MIN_COMMON_ENEMY_GROUP_SIZE = 6
BLUE_MAX_LOCATION_INDEX = 5


def triggers_imu_event(
    rng: random.Random | None = None,
    chance: float = 0.01,
) -> bool:
    """Return whether Imu erases the current island before the battle."""
    rng = rng or random.Random()
    return rng.random() < chance


def choose_campaign_bosses(rng: random.Random | None = None) -> dict[str, dict]:
    rng = rng or random.Random()
    return {
        phase: copy.deepcopy(rng.choice(bosses))
        for phase, bosses in BOSSES_BY_PHASE.items()
        if bosses
    }


def choose_campaign_boss_locations(
    stages: Iterable[dict],
    bosses: dict[str, dict],
    rng: random.Random | None = None,
) -> dict[str, int]:
    rng = rng or random.Random()
    locations = {}
    for phase in bosses:
        candidates = [
            stage["location_index"]
            for stage in stages
            if stage.get("phase") == phase
        ]
        if candidates:
            locations[phase] = rng.choice(candidates)
    return locations


def phase_arc(phase: str | None) -> str | None:
    if phase == "Blue":
        return "East Blue"
    if phase in {"Paraíso", "ParaÃ­so"}:
        return phase
    return None


def _same_arc(character: dict, arc: str | None) -> bool:
    return not arc or character.get("arc") == arc


def _boss_key(boss: dict | None) -> str:
    if not boss:
        return ""
    name = boss.get("name", "")
    phase = boss.get("phase", "")
    faction = boss.get("faction", "")
    if name.startswith("Marinha"):
        return "smoker_blue"
    if name == "Piratas Gigante":
        return "giants"
    if name == "Luffy" and phase == "Blue":
        return "luffy_blue"
    if name == "Luffy":
        return "luffy_paradise"
    if name == "Teach":
        return "teach"
    if name == "Foxy":
        return "foxy"
    if name == "Kuzan":
        return "kuzan"
    if name == "Spandam":
        return "spandam"
    if name == "Enel":
        return "enel"
    if name == "Crocodile":
        return "crocodile"
    if name == "Mihawk":
        return "mihawk"
    if name == "Shanks":
        return "shanks"
    return f"{phase}:{name}:{faction}"


def island_power_index(location_index: int) -> int:
    return max(0, min(location_index, BLUE_MAX_LOCATION_INDEX) - 1)


def _valid_roles(character: dict, selected_crew: dict[str, dict]) -> list[str]:
    return [
        role
        for role in character["roles"]
        if role in ROLES and role not in selected_crew
    ]


def _can_complete_crew(selected_crew: dict[str, dict]) -> bool:
    open_roles = [role for role in ROLES if role not in selected_crew]
    used_names = {character["name"] for character in selected_crew.values()}
    candidates = {
        role: [
            character
            for character in PLAYABLE_CHARACTERS
            if character["name"] not in used_names
            and role in character["roles"]
        ]
        for role in open_roles
    }
    ordered_roles = sorted(open_roles, key=lambda role: len(candidates[role]))

    def assign(index: int, used: set[str]) -> bool:
        if index == len(ordered_roles):
            return True
        role = ordered_roles[index]
        for character in candidates[role]:
            if character["name"] in used:
                continue
            used.add(character["name"])
            if assign(index + 1, used):
                return True
            used.remove(character["name"])
        return False

    return assign(0, set(used_names))


def draft_candidate_group(
    selected_crew: dict[str, dict] | None = None,
    rng: random.Random | None = None,
    group_appearance_counts: dict[str, int] | None = None,
) -> dict:
    """Draw a group and return choices that keep crew completion possible."""
    rng = rng or random.Random()
    selected_crew = selected_crew or {}
    group_appearance_counts = group_appearance_counts or {}
    valid_groups: list[dict] = []

    for group in PLAYABLE_DRAW_GROUPS:
        group_members = [
            character
            for character in PLAYABLE_CHARACTERS
            if group in character["draw_groups"]
        ]
        if len(group_members) < 5:
            continue
        options = []
        for character in group_members:
            already_selected = any(
                selected["name"] == character["name"]
                for selected in selected_crew.values()
            )
            roles = _valid_roles(character, selected_crew)
            valid_option_roles = []
            if not already_selected:
                for role in roles:
                    tentative = dict(selected_crew)
                    tentative[role] = character
                    if _can_complete_crew(tentative):
                        valid_option_roles.append(role)
            options.append(
                {
                    "character": copy.deepcopy(character),
                    "roles": valid_option_roles,
                    "available": bool(valid_option_roles),
                    "unavailable_reason": (
                        "Já integra a tripulação."
                        if already_selected
                        else "As funções deste personagem já estão ocupadas."
                    ),
                }
            )
        if any(option["available"] for option in options):
            valid_groups.append({"group": group, "options": options})

    if not valid_groups:
        raise RuntimeError("Não foi possível sortear um grupo válido.")
    weights = [
        0.5 ** group_appearance_counts.get(item["group"], 0)
        for item in valid_groups
    ]
    result = copy.deepcopy(rng.choices(valid_groups, weights=weights, k=1)[0])
    if len(result["options"]) > 6:
        sampled = rng.sample(result["options"], 6)
        if not any(option["available"] for option in sampled):
            available_option = rng.choice(
                [
                    option
                    for option in result["options"]
                    if option["available"]
                ]
            )
            sampled[-1] = available_option
        result["options"] = sampled
    else:
        rng.shuffle(result["options"])
    return result


def draft_candidate_team(
    selected_crew: dict[str, dict] | None = None,
    rng: random.Random | None = None,
) -> dict:
    """Compatibility alias for the former draft API."""
    return draft_candidate_group(selected_crew, rng)


def draft_crew(rng: random.Random | None = None) -> dict[str, dict]:
    """Build a complete deterministic-test-friendly crew through group draws."""
    rng = rng or random.Random()
    crew: dict[str, dict] = {}
    while len(crew) < len(ROLES):
        draw = draft_candidate_group(crew, rng)
        option = rng.choice(
            [item for item in draw["options"] if item["available"]]
        )
        role = rng.choice(option["roles"])
        crew[role] = copy.deepcopy(option["character"])
    return crew


def role_score(character: dict | None, assigned_role: str) -> int:
    if not character:
        return 0
    return int(character["skills"].get(assigned_role, 0))


def team_summary(crew: dict[str, dict]) -> dict[str, float]:
    if not crew:
        return {
            "attack": 0,
            "defense": 0,
            "captain_modifier": 0,
            "tactical_modifier": 0,
            "power": 0,
        }
    attack = sum(character["attack"] for character in crew.values())
    defense = sum(character["defense"] for character in crew.values())
    captain_modifier = role_score(crew.get("Capitão"), "Capitão") * 0.002
    tactical_modifier = role_score(crew.get("Tático"), "Tático") * 0.0015
    return {
        "attack": attack,
        "defense": defense,
        "captain_modifier": captain_modifier,
        "tactical_modifier": tactical_modifier,
        "power": attack + defense,
    }


def _build_fighter(
    character: dict,
    assigned_role: str,
    *,
    role_modifiers: bool = True,
) -> dict:
    attack = character["attack"] + (
        5 if role_modifiers and assigned_role == "Atacante" else 0
    )
    defense = (
        character["defense"]
        + (5 if role_modifiers and assigned_role == "Defensor" else 0)
    )
    max_hp = max(1, character["max_hp"])
    return {
        "name": character["name"],
        "assigned_role": assigned_role,
        "roles": copy.deepcopy(character["roles"]),
        "skills": copy.deepcopy(character["skills"]),
        "role_ranks": copy.deepcopy(character["role_ranks"]),
        "rank": character["rank"],
        "attack_rank": character["attack_rank"],
        "defense_rank": character["defense_rank"],
        "hp_rank": character["hp_rank"],
        "attack": attack,
        "defense": defense,
        "max_hp": max_hp,
        "hp": max_hp,
        "alive": True,
        "recruitment_chance": character.get("recruitment_chance"),
        "source_arc": character.get("arc"),
        "boss_member": False,
        "critical_bonus": 0.0,
        "skip_rounds": 0,
    }


def _apply_enemy_size_bonus(
    fighter: dict,
    attack_multiplier: float,
    durability_multiplier: float,
) -> dict:
    boosted = copy.deepcopy(fighter)
    boosted["attack"] = max(1, round(boosted["attack"] * attack_multiplier))
    boosted["defense"] = max(
        1, round(boosted["defense"] * durability_multiplier)
    )
    boosted["max_hp"] = max(
        1, round(boosted["max_hp"] * durability_multiplier)
    )
    boosted["hp"] = boosted["max_hp"]
    boosted["combat_multiplier"] = durability_multiplier
    boosted["attack_multiplier"] = attack_multiplier
    return boosted


def enemy_combat_multipliers(
    character: dict,
    location_index: int,
    team_size: int,
) -> tuple[float, float]:
    island_attack_multiplier = 1 + ISLAND_POWER_STEP * island_power_index(
        location_index
    )
    size_multiplier = 1 + max(0, 6 - team_size) * 0.25
    tier_multiplier = {
        "SSS": 1.55,
        "SS": 1.40,
        "S": 1.25,
        "A": 1.12,
    }.get(character["rank"], 1.0)
    captain_multiplier = 1.15 if "Capitão" in character["roles"] else 1.0
    durability_multiplier = (
        size_multiplier * tier_multiplier * captain_multiplier
    )
    attack_multiplier = durability_multiplier * island_attack_multiplier
    if character["name"] == "Mihawk":
        attack_multiplier = 1 + (attack_multiplier - 1) * 2
        durability_multiplier = 1 + (durability_multiplier - 1) * 2
    return attack_multiplier, durability_multiplier


def _character_for_boss_name(name: str, boss: dict, arc: str | None) -> dict:
    pools = [ENEMY_CHARACTERS, PLAYABLE_CHARACTERS]
    for pool in pools:
        matches = [
            character
            for character in pool
            if character["name"] == name
            and _same_arc(character, arc)
            and (
                not boss.get("faction")
                or character.get("faction") == boss["faction"]
                or boss["faction"] in character.get("faction", "")
                or character.get("faction", "") in boss["faction"]
            )
        ]
        if matches:
            return matches[0]
    for pool in pools:
        matches = [
            character
            for character in pool
            if character["name"] == name and _same_arc(character, arc)
        ]
        if matches:
            return matches[0]
    if name in CHARACTER_BY_NAME:
        return CHARACTER_BY_NAME[name]
    raise RuntimeError(f"Personagem obrigatório do boss não encontrado: {name}.")


def _select_boss_team(stage: dict, maximum: int) -> list[dict]:
    boss = stage["boss"]
    arc = stage.get("arc") or boss.get("arc") or phase_arc(stage.get("phase"))
    team = []
    seen = set()
    for name in boss.get("required_names", []):
        character = copy.deepcopy(_character_for_boss_name(name, boss, arc))
        if character["name"] in seen:
            continue
        character["recruitment_chance"] = None
        character["boss_member"] = True
        team.append(character)
        seen.add(character["name"])
        if len(team) >= maximum:
            break
    if not team:
        raise RuntimeError(f"Boss sem equipe obrigatória: {boss['name']}.")
    return team


def select_enemy_team(
    stage: dict,
    rng: random.Random | None = None,
    maximum: int = 6,
) -> list[dict]:
    """Select up to six unique enemies from one group."""
    rng = rng or random.Random()
    if isinstance(stage.get("boss"), dict):
        return _select_boss_team(stage, maximum)

    arc = stage.get("arc") or phase_arc(stage.get("phase"))
    group = stage.get("enemy_group") or select_enemy_group(
        stage["location_index"], rng, arc=arc
    )
    eligible = [
        character
        for character in ENEMY_CHARACTERS
        if group in character["draw_groups"]
        and _same_arc(character, arc)
    ]
    if not eligible:
        raise RuntimeError(f"Nenhum inimigo encontrado para o grupo {group}.")

    boss_name = stage.get("boss")
    boss = next(
        (character for character in eligible if character["name"] == boss_name),
        None,
    )
    remaining = [
        character
        for character in eligible
        if not boss or character["name"] != boss["name"]
    ]
    captains = [
        character for character in remaining if "Capitão" in character["roles"]
    ]
    others = [
        character for character in remaining if "Capitão" not in character["roles"]
    ]
    rng.shuffle(captains)
    rng.shuffle(others)
    ordered = ([boss] if boss else []) + captains + others
    return copy.deepcopy(ordered[:maximum])


def enemy_group_strength(group: str, arc: str | None = None) -> float:
    members = [
        character
        for character in ENEMY_CHARACTERS
        if group in character["draw_groups"]
        and _same_arc(character, arc)
    ]
    if not members:
        return 0.0
    return sum(
        character["attack"] + character["defense"] + character["max_hp"]
        for character in members
    ) / (3 * len(members))


def enemy_group_size(group: str, arc: str | None = None) -> int:
    return sum(
        1
        for character in ENEMY_CHARACTERS
        if group in character["draw_groups"]
        and _same_arc(character, arc)
    )


def select_enemy_group(
    location_index: int,
    rng: random.Random | None = None,
    excluded_groups: set[str] | None = None,
    arc: str | None = None,
) -> str:
    """Favor stronger affiliations as the campaign approaches its end."""
    rng = rng or random.Random()
    excluded_groups = excluded_groups or set()
    available_groups = [
        group
        for group in ENEMY_GROUPS
        if group not in excluded_groups
        and any(
            group in character["draw_groups"]
            and _same_arc(character, arc)
            for character in ENEMY_CHARACTERS
        )
        and enemy_group_size(group, arc) >= MIN_COMMON_ENEMY_GROUP_SIZE
    ]
    if not available_groups:
        raise RuntimeError("Todas as filiações inimigas já foram enfrentadas.")
    ranked_groups = sorted(
        available_groups,
        key=lambda group: enemy_group_strength(group, arc),
    )
    if len(ranked_groups) == 1:
        return ranked_groups[0]
    progress = max(0.0, min(1.0, (location_index - 1) / 4))
    target = progress * (len(ranked_groups) - 1)
    spread = max(1.0, len(ranked_groups) * 0.28)
    weights = [
        1 / (1 + ((index - target) / spread) ** 2)
        for index in range(len(ranked_groups))
    ]
    return rng.choices(ranked_groups, weights=weights, k=1)[0]


def start_battle(
    crew: dict[str, dict],
    stage: dict,
    rng: random.Random | None = None,
    excluded_groups: set[str] | None = None,
    crew_statuses: dict[str, dict] | None = None,
) -> dict:
    rng = rng or random.Random()
    crew_statuses = crew_statuses or {}
    arc = stage.get("arc") or phase_arc(stage.get("phase"))
    battle_stage = copy.deepcopy(stage)
    boss = battle_stage.get("boss") if isinstance(battle_stage.get("boss"), dict) else None
    if boss:
        battle_stage["enemy_group"] = boss["faction"] or boss["name"]
        battle_stage["boss_key"] = _boss_key(boss)
    else:
        enemy_group = stage.get("enemy_group") or select_enemy_group(
            stage["location_index"], rng, excluded_groups, arc
        )
        battle_stage["enemy_group"] = enemy_group
        battle_stage["boss_key"] = ""
    active_crew = {}
    inactive_player = []
    for role, character in crew.items():
        status = crew_statuses.get(character["name"])
        if status and status.get("skip_battles", 0) > 0:
            inactive_player.append(
                {
                    "name": character["name"],
                    "assigned_role": role,
                    "status": status.get("kind", "debilitado"),
                }
            )
        else:
            active_crew[role] = character
    role_modifiers = battle_stage["boss_key"] != "teach"
    player = [
        _build_fighter(character, role, role_modifiers=role_modifiers)
        for role, character in active_crew.items()
    ]
    enemy_characters = select_enemy_team(battle_stage, rng)
    enemies = [
        _build_fighter(character, character["roles"][0])
        for character in enemy_characters
    ]
    for fighter, character in zip(enemies, enemy_characters):
        fighter["boss_member"] = bool(character.get("boss_member"))
    enemies = [
        _apply_enemy_size_bonus(
            fighter,
            *enemy_combat_multipliers(
                character, stage["location_index"], len(enemy_characters)
            ),
        )
        for fighter, character in zip(enemies, enemy_characters)
    ]
    battle = {
        "round": 0,
        "stage": battle_stage,
        "player": player,
        "inactive_player": inactive_player,
        "enemies": enemies,
        "status": "active",
        "log": [
            f"⚓ Batalha iniciada em {stage['name']}.",
            (
                f"🚨 Grupo inimigo: {battle_stage['enemy_group']} "
                f"({len(enemies)} integrantes)."
            ),
        ],
        "spy_resolved": False,
        "captain_fell": False,
        "command_mode": "captain",
        "enemy_size_multiplier": 1 + max(0, 6 - len(enemies)) * 0.25,
        "island_difficulty_multiplier": 1
        + ISLAND_POWER_STEP * island_power_index(stage["location_index"]),
        "player_role_modifiers_disabled": not role_modifiers,
        "boss_events": set(),
        "post_battle": {
            "lost_names": [],
            "debilitated_names": [],
            "frozen_names": [],
        },
    }
    if battle_stage["boss_key"] == "giants":
        for fighter in battle["enemies"]:
            if fighter["name"] in {"Dorry", "Broggy"}:
                fighter["attack"] = max(1, round(fighter["attack"] * 3))
        battle["log"].append("🗿 Os gigantes iniciaram o duelo com força esmagadora.")
    if inactive_player:
        names = ", ".join(item["name"] for item in inactive_player)
        battle["log"].append(f"🌫️ Fora de combate nesta ilha: {names}.")
    return battle


def _alive(fighters: Iterable[dict]) -> list[dict]:
    return [fighter for fighter in fighters if fighter["alive"]]


def _find_role(fighters: Iterable[dict], role: str) -> dict | None:
    return next(
        (
            fighter
            for fighter in fighters
            if fighter["assigned_role"] == role and fighter["alive"]
        ),
        None,
    )


def _damage(
    attacker: dict,
    defender: dict,
    rng: random.Random,
    tactical_crit_bonus: float = 0.0,
    attack_multiplier: float = 1.0,
    defense_multiplier: float = 1.0,
) -> tuple[int, bool, bool, bool]:
    critical_chance = 0.05 + tactical_crit_bonus + attacker.get(
        "critical_bonus", 0.0
    )
    critical = rng.random() < min(0.40, critical_chance)
    damage = max(1, round(attacker["attack"] * attack_multiplier * 0.35))
    if critical:
        damage *= 2

    effective_defense = defender["defense"] * defense_multiplier
    defense_chance = effective_defense * 0.002
    if defender["assigned_role"] == "Defensor":
        defense_chance += (
            defender["skills"].get("Defensor", 0) * 0.003
        )
    defended = rng.random() < min(0.60, defense_chance)
    if defended:
        damage = max(1, (damage + 1) // 2)
    return damage, critical, defended, False


def _tactical_crit_bonus(
    fighters: list[dict],
    disabled: bool = False,
) -> float:
    if disabled:
        return 0.0
    tactician = _find_role(fighters, "Tático")
    if not tactician:
        return 0.0
    return tactician["skills"].get("Tático", 0) * 0.0015


def _apply_hit(target: dict, damage: int) -> bool:
    target["hp"] = max(0, target["hp"] - damage)
    if target["hp"] == 0:
        target["alive"] = False
        return True
    return False


def _resolve_spy(battle: dict, rng: random.Random) -> None:
    if battle["spy_resolved"]:
        return
    battle["spy_resolved"] = True
    if battle.get("player_role_modifiers_disabled"):
        battle["log"].append("🌑 A tripulação não conseguiu ativar suas funções.")
        return
    spy = _find_role(battle["player"], "Espião")
    if not spy:
        battle["log"].append("🕶️ O time não possui espião disponível.")
        return

    score = spy["skills"].get("Espião", 0)
    target_pool = _alive(battle["enemies"])
    if not target_pool:
        return
    target = rng.choice(target_pool)
    success_chance = min(0.65, 0.10 + score * 0.005)
    failure_damage_chance = max(0.08, 0.38 - score * 0.003)

    if rng.random() < success_chance:
        if rng.random() < min(0.45, score * 0.0045):
            target["hp"] = 0
            target["alive"] = False
            battle["log"].append(
                f"🗡️ {spy['name']} eliminou {target['name']} na infiltração."
            )
        else:
            damage = max(1, round(spy["attack"] * 0.30))
            _apply_hit(target, damage)
            battle["log"].append(
                f"🗡️ {spy['name']} feriu {target['name']} antes da batalha."
            )
    elif rng.random() < failure_damage_chance:
        damage = max(1, round(spy["max_hp"] * 0.25))
        _apply_hit(spy, damage)
        battle["log"].append(
            f"💫 {spy['name']} foi descoberto e voltou ferido."
        )
    else:
        battle["log"].append(
            f"🌫️ {spy['name']} não encontrou uma abertura para agir."
        )


def _command_multipliers(battle: dict) -> tuple[float, float, list[str]]:
    notes: list[str] = []
    if battle.get("player_role_modifiers_disabled"):
        battle["command_mode"] = "none"
        return 1.0, 1.0, notes
    captain = _find_role(battle["player"], "Capitão")
    immediate = _find_role(battle["player"], "Imediato")

    if captain:
        captain_bonus = captain["skills"].get("Capitão", 0) * 0.002
        battle["command_mode"] = "captain"
    elif immediate:
        original_captain = next(
            (
                fighter
                for fighter in battle["player"]
                if fighter["assigned_role"] == "Capitão"
            ),
            None,
        )
        original_bonus = (
            original_captain["skills"].get("Capitão", 0) * 0.002
            if original_captain
            else 0
        )
        preservation = min(
            0.95,
            0.40 + immediate["skills"].get("Imediato", 0) * 0.0055,
        )
        captain_bonus = original_bonus * preservation
        battle["command_mode"] = "immediate"
        if not battle["captain_fell"]:
            battle["captain_fell"] = True
            notes.append(
                f"⭐ {immediate['name']} assumiu o comando da tripulação."
            )
    else:
        captain_bonus = -0.08
        battle["command_mode"] = "none"

    return max(0.75, 1 + captain_bonus), 1.0, notes


def _choose_player_target(players: list[dict], rng: random.Random) -> dict:
    weights = []
    for fighter in players:
        weight = 1.0
        if fighter["assigned_role"] == "Atacante":
            weight += 1.20
        if fighter["assigned_role"] in IMPORTANT_ROLES:
            weight += 0.20
        missing_hp = 1 - fighter["hp"] / fighter["max_hp"]
        weights.append(weight + missing_hp * 0.50)
    return rng.choices(players, weights=weights, k=1)[0]


def _maybe_intercept(
    players: list[dict],
    original_target: dict,
    rng: random.Random,
    disabled: bool = False,
) -> tuple[dict, bool]:
    if disabled:
        return original_target, False
    defender = _find_role(players, "Defensor")
    if not defender or defender is original_target:
        return original_target, False
    guard_score = defender["skills"].get("Defensor", 0)
    importance_bonus = (
        0.12 if original_target["assigned_role"] in IMPORTANT_ROLES else 0
    )
    danger_bonus = (
        0.10
        if original_target["hp"] < original_target["max_hp"] * 0.42
        else 0
    )
    chance = min(
        0.72,
        0.08 + guard_score * 0.0045 + importance_bonus + danger_bonus,
    )
    if rng.random() < chance:
        return defender, True
    return original_target, False


def _revive(fighter: dict, hp_ratio: float, log: list[str]) -> None:
    fighter["hp"] = max(1, round(fighter["max_hp"] * hp_ratio))
    fighter["alive"] = True
    log.append(f"🔥 {fighter['name']} voltou ao combate.")


def _handle_enemy_defeat(
    battle: dict,
    fighter: dict,
    rng: random.Random,
) -> None:
    key = battle["stage"].get("boss_key", "")
    events = battle["boss_events"]
    if key == "luffy_blue" and f"luffy_blue:{fighter['name']}" not in events:
        if rng.random() < 0.50:
            events.add(f"luffy_blue:{fighter['name']}")
            _revive(fighter, 0.50, battle["log"])
            battle["log"].append(
                f"🏴‍☠️ {fighter['name']} se ergueu de novo ao lado de Luffy."
            )
            return
    if key == "giants" and fighter["name"] in {"Dorry", "Broggy"}:
        other_name = "Broggy" if fighter["name"] == "Dorry" else "Dorry"
        event_key = f"giant_rage:{other_name}"
        other = next(
            (
                enemy
                for enemy in battle["enemies"]
                if enemy["name"] == other_name and enemy["alive"]
            ),
            None,
        )
        if other and event_key not in events:
            events.add(event_key)
            other["attack"] = max(1, round(other["attack"] * 2))
            other["defense"] = max(1, round(other["defense"] * 0.5))
            battle["log"].append(f"🗿 {other_name} entrou em fúria pelo rival.")
    if key == "spandam" and fighter["name"] == "Spandam":
        event_key = "buster_call"
        if event_key not in events:
            events.add(event_key)
            battle["log"].append("💣 Spandam convocou um Buster Call.")
            for target in _alive(battle["player"]) + _alive(battle["enemies"]):
                damage = max(1, round(target["max_hp"] * 0.20))
                _apply_hit(target, damage)
                battle["log"].append(f"●● {target['name']} foi atingido.")
    if key == "spandam" and fighter["name"] == "Rob Lucci":
        event_key = "lucci_zoan"
        if event_key not in events:
            events.add(event_key)
            fighter["attack"] = max(1, round(fighter["attack"] * 1.25))
            fighter["defense"] = max(1, round(fighter["defense"] * 1.25))
            fighter["critical_bonus"] = fighter.get("critical_bonus", 0.0) + 0.10
            _revive(fighter, 0.50, battle["log"])
            battle["log"].append("🐆 Lucci liberou sua forma animal.")
    if key == "luffy_paradise" and fighter["name"] == "Luffy":
        if "gear_2" not in events:
            events.add("gear_2")
            fighter["attack"] = max(1, round(fighter["attack"] * 1.50))
            _revive(fighter, 0.50, battle["log"])
            battle["log"].append("Gear 2.")
        elif "gear_3" not in events:
            events.add("gear_3")
            fighter["attack"] = max(1, round(fighter["attack"] * 1.70))
            fighter["defense"] = max(1, round(fighter["defense"] * 1.50))
            _revive(fighter, 0.25, battle["log"])
            battle["log"].append("Gear 3.")


def _handle_player_defeat(
    battle: dict,
    fighter: dict,
    attacker: dict,
    rng: random.Random,
) -> None:
    key = battle["stage"].get("boss_key", "")
    if key == "foxy" and rng.random() < 0.75:
        if fighter["name"] not in battle["post_battle"]["lost_names"]:
            battle["post_battle"]["lost_names"].append(fighter["name"])
        turncoat = copy.deepcopy(fighter)
        turncoat["hp"] = max(1, round(turncoat["max_hp"] * 0.50))
        turncoat["alive"] = True
        turncoat["assigned_role"] = turncoat["roles"][0]
        turncoat["recruitment_chance"] = None
        battle["enemies"].append(turncoat)
        battle["log"].append(
            f"{fighter['name']} deixou o bando após perder no Davy Back Fight."
        )
    if key == "kuzan" and attacker["name"] == "Kuzan":
        if fighter["name"] not in battle["post_battle"]["frozen_names"]:
            battle["post_battle"]["frozen_names"].append(fighter["name"])
        battle["log"].append(f"🧊 {fighter['name']} ficou congelado.")


def play_round(
    battle: dict,
    rng: random.Random | None = None,
    on_update: Callable[[dict], None] | None = None,
) -> dict:
    rng = rng or random.Random()
    if battle["status"] != "active":
        return battle

    battle["round"] += 1
    battle["log"].append(f"— Rodada {battle['round']} —")
    if battle["round"] == 1:
        _resolve_spy(battle, rng)
        if on_update:
            on_update(battle)

    if not _alive(battle["player"]) or not _alive(battle["enemies"]):
        return _finalize_status(battle)

    player_attack_multiplier, player_defense_multiplier, notes = (
        _command_multipliers(battle)
    )
    battle["log"].extend(notes)
    disabled_roles = battle.get("player_role_modifiers_disabled", False)
    player_tactical_bonus = _tactical_crit_bonus(
        battle["player"], disabled_roles
    )
    enemy_tactical_bonus = _tactical_crit_bonus(battle["enemies"])

    for attacker in list(_alive(battle["player"])):
        enemy_alive = _alive(battle["enemies"])
        if not attacker["alive"] or not enemy_alive:
            break
        if attacker.get("skip_rounds", 0) > 0:
            attacker["skip_rounds"] -= 1
            battle["log"].append(f"⚡ {attacker['name']} não conseguiu agir.")
            continue
        if battle["stage"].get("boss_key") == "foxy" and battle["round"] % 2 == 0:
            battle["log"].append(f"🌀 {attacker['name']} foi retardado pelo Noro Noro.")
            continue
        if battle["stage"].get("boss_key") == "crocodile":
            index = battle["player"].index(attacker)
            target = next(
                (
                    enemy
                    for enemy in battle["enemies"][index:index + 1]
                    if enemy["alive"]
                ),
                rng.choice(enemy_alive),
            )
        else:
            target = rng.choice(enemy_alive)
        if (
            battle["stage"].get("boss_key") == "smoker_blue"
            and target["name"] == "Smoker"
            and rng.random() < 0.50
        ):
            battle["log"].append(f"💨 {target['name']} escapou do golpe.")
            continue
        damage, critical, defended, _ = _damage(
            attacker,
            target,
            rng,
            player_tactical_bonus,
            player_attack_multiplier,
        )
        eliminated = _apply_hit(target, damage)
        markers = (
            (" CRÍTICO" if critical else "")
            + (" DEFENDIDO" if defended else "")
            + (" e nocauteou o alvo" if eliminated else "")
        )
        battle["log"].append(
            f"⚔️ {attacker['name']} atingiu {target['name']}{markers}."
        )
        if eliminated:
            _handle_enemy_defeat(battle, target, rng)
            if on_update:
                on_update(battle)

    for attacker in list(_alive(battle["enemies"])):
        player_alive = _alive(battle["player"])
        if not attacker["alive"] or not player_alive:
            break
        if attacker.get("skip_rounds", 0) > 0:
            attacker["skip_rounds"] -= 1
            continue
        if battle["stage"].get("boss_key") == "crocodile":
            index = battle["enemies"].index(attacker)
            original_target = next(
                (
                    player
                    for player in battle["player"][index:index + 1]
                    if player["alive"]
                ),
                _choose_player_target(player_alive, rng),
            )
        else:
            original_target = _choose_player_target(player_alive, rng)
        target, intercepted = _maybe_intercept(
            battle["player"], original_target, rng, disabled_roles
        )
        if intercepted:
            battle["log"].append(
                f"🛡️ {target['name']} interceptou o golpe destinado a "
                f"{original_target['name']}."
            )
        damage, critical, defended, _ = _damage(
            attacker,
            target,
            rng,
            enemy_tactical_bonus,
            defense_multiplier=player_defense_multiplier,
        )
        eliminated = _apply_hit(target, damage)
        markers = (
            (" CRÍTICO" if critical else "")
            + (" DEFENDIDO" if defended else "")
            + (" e nocauteou o alvo" if eliminated else "")
        )
        battle["log"].append(
            f"💥 {attacker['name']} atingiu {target['name']}{markers}."
        )
        if battle["stage"].get("boss_key") == "enel" and target["alive"]:
            target["skip_rounds"] = max(target.get("skip_rounds", 0), 1)
            battle["log"].append(f"⚡ {target['name']} ficou paralisado.")
        if eliminated:
            _handle_player_defeat(battle, target, attacker, rng)
            if on_update:
                on_update(battle)

    return _finalize_status(battle)


def _finalize_status(battle: dict) -> dict:
    if not _alive(battle["enemies"]):
        battle["status"] = "victory"
        battle["log"].append("🏆 Vitória! A rota para a próxima ilha foi aberta.")
    elif not _alive(battle["player"]):
        battle["status"] = "defeat"
        battle["log"].append("💫 Toda a tripulação foi nocauteada.")
    return battle


def recruitment_roll(
    battle: dict,
    existing_names: set[str],
    candidate_name: str,
    rng: random.Random | None = None,
) -> dict:
    rng = rng or random.Random()
    candidate = next(
        (
            enemy
            for enemy in battle["enemies"]
            if enemy["name"] == candidate_name
            and enemy["name"] not in existing_names
            and enemy.get("recruitment_chance") is not None
            and not enemy.get("boss_member")
        ),
        None,
    )
    if not candidate:
        return {
            "attempted": False,
            "success": False,
            "message": "Este personagem não está disponível para recrutamento.",
        }

    captain = next(
        (
            fighter
            for fighter in battle["player"]
            if fighter["assigned_role"] == "Capitão"
        ),
        None,
    )
    captain_score = (
        captain["skills"].get("Capitão", 0) if captain else 0
    )
    base_chance = float(candidate["recruitment_chance"])
    chance = min(0.95, base_chance + captain_score * 0.001)
    roll = rng.random()
    success = roll <= chance
    return {
        "attempted": True,
        "success": success,
        "candidate": candidate["name"],
        "chance": chance,
        "roll": roll,
        "message": (
            f"{candidate['name']} aceitou entrar para a tripulação."
            if success
            else f"{candidate['name']} recusou o convite."
        ),
    }


def boss_aftermath(
    battle: dict,
    crew: dict[str, dict],
    rng: random.Random | None = None,
) -> dict:
    rng = rng or random.Random()
    key = battle["stage"].get("boss_key", "")
    result = {
        "remove_names": [],
        "statuses": {},
        "messages": [],
    }
    if battle["status"] != "victory":
        return result

    if key == "mihawk":
        for role, character in crew.items():
            if role == "Capitão":
                continue
            if rng.random() < 0.50:
                result["statuses"][character["name"]] = {
                    "kind": "debilitado",
                    "skip_battles": 1,
                }
                result["messages"].append(
                    f"{character['name']} ficou debilitado para a próxima ilha."
                )
    if key == "shanks":
        candidates = [
            character
            for role, character in crew.items()
            if role != "Capitão"
        ] or list(crew.values())
        if candidates:
            taken = rng.choice(candidates)
            result["remove_names"].append(taken["name"])
            result["messages"].append(
                f"{taken['name']} deixou a tripulação após o encontro com Shanks."
            )
    for name in battle["post_battle"].get("lost_names", []):
        result["remove_names"].append(name)
    for name in battle["post_battle"].get("frozen_names", []):
        result["statuses"][name] = {
            "kind": "congelado",
            "skip_battles": 1,
        }
        result["messages"].append(
            f"{name} ficará congelado na próxima batalha."
        )
    return result


def replace_survivor_with_recruit(
    crew: dict[str, dict],
    battle: dict,
    recruit_name: str,
    role: str,
) -> dict[str, dict]:
    recruit = next(
        (
            character
            for character in ENEMY_CHARACTERS
            if character["name"] == recruit_name
        ),
        None,
    )
    if not recruit:
        raise ValueError("Personagem recrutado não encontrado.")
    if role not in recruit["roles"]:
        raise ValueError(f"{recruit_name} não pode exercer a função {role}.")
    survivor_roles = {
        fighter["assigned_role"]
        for fighter in battle["player"]
        if fighter["alive"]
    }
    if role not in survivor_roles:
        raise ValueError("Somente um sobrevivente pode ser substituído.")
    if any(
        character["name"] == recruit_name and assigned_role != role
        for assigned_role, character in crew.items()
    ):
        raise ValueError(f"{recruit_name} já integra a tripulação.")
    updated = copy.deepcopy(crew)
    updated[role] = copy.deepcopy(recruit)
    return updated
