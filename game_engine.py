from __future__ import annotations

import copy
import random
from typing import Callable, Iterable

from game_data import (
    ENEMY_CHARACTERS,
    ENEMY_GROUPS,
    PLAYABLE_CHARACTERS,
    PLAYABLE_DRAW_GROUPS,
    ROLES,
)


IMPORTANT_ROLES = {"Capitão", "Imediato", "Tático", "Espião"}


def triggers_imu_event(
    rng: random.Random | None = None,
    chance: float = 0.01,
) -> bool:
    """Return whether Imu erases the current island before the battle."""
    rng = rng or random.Random()
    return rng.random() < chance


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
                    tentative = copy.deepcopy(selected_crew)
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


def _build_fighter(character: dict, assigned_role: str) -> dict:
    attack = character["attack"] + (5 if assigned_role == "Atacante" else 0)
    defense = (
        character["defense"] + (5 if assigned_role == "Defensor" else 0)
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
    island_attack_multiplier = 1 + 0.25 * max(0, location_index - 1)
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


def select_enemy_team(
    stage: dict,
    rng: random.Random | None = None,
    maximum: int = 6,
) -> list[dict]:
    """Select up to six unique enemies from one group."""
    rng = rng or random.Random()
    group = stage.get("enemy_group") or select_enemy_group(
        stage["location_index"], rng
    )
    eligible = [
        character
        for character in ENEMY_CHARACTERS
        if group in character["draw_groups"]
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


def enemy_group_strength(group: str) -> float:
    members = [
        character
        for character in ENEMY_CHARACTERS
        if group in character["draw_groups"]
    ]
    if not members:
        return 0.0
    return sum(
        character["attack"] + character["defense"] + character["max_hp"]
        for character in members
    ) / (3 * len(members))


def select_enemy_group(
    location_index: int,
    rng: random.Random | None = None,
    excluded_groups: set[str] | None = None,
) -> str:
    """Favor stronger affiliations as the campaign approaches its end."""
    rng = rng or random.Random()
    excluded_groups = excluded_groups or set()
    available_groups = [
        group for group in ENEMY_GROUPS if group not in excluded_groups
    ]
    if not available_groups:
        raise RuntimeError("Todas as filiações inimigas já foram enfrentadas.")
    ranked_groups = sorted(available_groups, key=enemy_group_strength)
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
) -> dict:
    rng = rng or random.Random()
    enemy_group = stage.get("enemy_group") or select_enemy_group(
        stage["location_index"], rng, excluded_groups
    )
    battle_stage = copy.deepcopy(stage)
    battle_stage["enemy_group"] = enemy_group
    player = [
        _build_fighter(character, role)
        for role, character in crew.items()
    ]
    enemy_characters = select_enemy_team(battle_stage, rng)
    enemies = [
        _build_fighter(character, character["roles"][0])
        for character in enemy_characters
    ]
    enemies = [
        _apply_enemy_size_bonus(
            fighter,
            *enemy_combat_multipliers(
                character, stage["location_index"], len(enemy_characters)
            ),
        )
        for fighter, character in zip(enemies, enemy_characters)
    ]
    return {
        "round": 0,
        "stage": battle_stage,
        "player": player,
        "enemies": enemies,
        "status": "active",
        "log": [
            f"⚓ Batalha iniciada em {stage['name']}.",
            (
                f"🚨 Grupo inimigo: {enemy_group} "
                f"({len(enemies)} integrantes)."
            ),
        ],
        "spy_resolved": False,
        "captain_fell": False,
        "command_mode": "captain",
        "enemy_size_multiplier": 1 + max(0, 6 - len(enemies)) * 0.25,
        "island_difficulty_multiplier": 1
        + 0.25 * max(0, stage["location_index"] - 1),
    }


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
    critical_chance = 0.05 + tactical_crit_bonus
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


def _tactical_crit_bonus(fighters: list[dict]) -> float:
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
) -> tuple[dict, bool]:
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
    player_tactical_bonus = _tactical_crit_bonus(battle["player"])
    enemy_tactical_bonus = _tactical_crit_bonus(battle["enemies"])

    for attacker in list(_alive(battle["player"])):
        enemy_alive = _alive(battle["enemies"])
        if not attacker["alive"] or not enemy_alive:
            break
        target = rng.choice(enemy_alive)
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
        if eliminated and on_update:
            on_update(battle)

    for attacker in list(_alive(battle["enemies"])):
        player_alive = _alive(battle["player"])
        if not attacker["alive"] or not player_alive:
            break
        original_target = _choose_player_target(player_alive, rng)
        target, intercepted = _maybe_intercept(
            battle["player"], original_target, rng
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
        if eliminated and on_update:
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
