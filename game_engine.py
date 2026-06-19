from __future__ import annotations

import copy
import random
from typing import Iterable

from game_data import CHARACTER_BY_NAME, CHARACTERS, ROLES


IMPORTANT_ROLES = {"Líder", "Vice-líder", "Tático", "Espião"}


def draft_crew(rng: random.Random | None = None) -> dict[str, dict]:
    """Fill every role with a unique eligible character."""
    rng = rng or random.Random()
    role_names = list(ROLES)
    candidates = {
        role: [item for item in CHARACTERS if role in item["roles"]]
        for role in role_names
    }
    ordered_roles = sorted(role_names, key=lambda role: len(candidates[role]))

    def assign(index: int, used: set[str], result: dict[str, dict]) -> bool:
        if index == len(ordered_roles):
            return True
        role = ordered_roles[index]
        options = [item for item in candidates[role] if item["name"] not in used]
        rng.shuffle(options)
        for item in options:
            result[role] = copy.deepcopy(item)
            used.add(item["name"])
            if assign(index + 1, used, result):
                return True
            used.remove(item["name"])
            result.pop(role, None)
        return False

    crew: dict[str, dict] = {}
    if not assign(0, set(), crew):
        raise RuntimeError("Não foi possível formar uma tripulação válida.")
    return {role: crew[role] for role in role_names}


def reroll_role(
    crew: dict[str, dict],
    role: str,
    rng: random.Random | None = None,
) -> dict[str, dict]:
    rng = rng or random.Random()
    used = {
        item["name"]
        for current_role, item in crew.items()
        if current_role != role
    }
    options = [
        item
        for item in CHARACTERS
        if role in item["roles"] and item["name"] not in used
    ]
    if not options:
        return crew
    updated = copy.deepcopy(crew)
    updated[role] = copy.deepcopy(rng.choice(options))
    return updated


def role_score(character: dict, assigned_role: str) -> int:
    return int(character["skills"].get(assigned_role, 0))


def team_summary(crew: dict[str, dict]) -> dict[str, float]:
    if not crew:
        return {
            "attack": 0,
            "defense": 0,
            "tactical_modifier": 0,
            "leader_bonus": 0,
            "power": 0,
        }
    attack = sum(item["attack"] for item in crew.values())
    defense = sum(item["defense"] for item in crew.values())
    tactician = crew.get("Tático")
    leader = crew.get("Líder")
    tactical_score = role_score(tactician, "Tático") if tactician else 5
    leader_score = role_score(leader, "Líder") if leader else 0
    tactical_modifier = (tactical_score - 5) * 0.035
    leader_bonus = leader_score * 0.018
    power = (attack + defense) * (1 + tactical_modifier + leader_bonus)
    return {
        "attack": attack,
        "defense": defense,
        "tactical_modifier": tactical_modifier,
        "leader_bonus": leader_bonus,
        "power": power,
    }


def _build_fighter(
    character: dict,
    assigned_role: str,
    *,
    hp_multiplier: float = 1.0,
    attack_override: int | None = None,
    defense_override: int | None = None,
) -> dict:
    defense = defense_override if defense_override is not None else character["defense"]
    attack = attack_override if attack_override is not None else character["attack"]
    return {
        "name": character["name"],
        "assigned_role": assigned_role,
        "roles": copy.deepcopy(character["roles"]),
        "skills": copy.deepcopy(character["skills"]),
        "rank": character["rank"],
        "attack": attack,
        "defense": defense,
        "max_hp": max(10, round((16 + defense * 4) * hp_multiplier)),
        "hp": max(10, round((16 + defense * 4) * hp_multiplier)),
        "alive": True,
    }


def start_battle(crew: dict[str, dict], stage: dict) -> dict:
    player = [
        _build_fighter(character, role)
        for role, character in crew.items()
    ]
    adjustments = stage.get("enemy_adjustments", {})
    enemies = []
    for name in stage["enemies"]:
        character = CHARACTER_BY_NAME[name]
        adjustment = adjustments.get(name, {})
        primary_role = character["roles"][0]
        enemies.append(
            _build_fighter(
                character,
                primary_role,
                hp_multiplier=adjustment.get("hp_multiplier", 1.0),
                attack_override=adjustment.get("attack"),
                defense_override=adjustment.get("defense"),
            )
        )
    return {
        "round": 0,
        "stage": copy.deepcopy(stage),
        "player": player,
        "enemies": enemies,
        "status": "active",
        "log": [f"⚓ Batalha iniciada em {stage['name']}."],
        "spy_resolved": False,
        "leader_fell": False,
        "command_mode": "leader",
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
    attack_multiplier: float,
    defense_multiplier: float,
    rng: random.Random,
) -> tuple[int, bool]:
    role_bonus = 1.0
    critical_chance = 0.05
    if attacker["assigned_role"] == "Atacante":
        assault = attacker["skills"].get("Atacante", 0)
        role_bonus += assault * 0.025
        critical_chance += assault * 0.018
    critical = rng.random() < critical_chance
    critical_multiplier = 1.55 if critical else 1.0
    raw = (
        attacker["attack"]
        * rng.uniform(1.45, 2.10)
        * attack_multiplier
        * role_bonus
        * critical_multiplier
    )
    mitigation = defender["defense"] * rng.uniform(0.48, 0.72) * defense_multiplier
    return max(1, round(raw - mitigation)), critical


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
    success_chance = min(0.55, 0.08 + score * 0.045)
    death_chance = max(0.04, 0.22 - score * 0.015)
    target_pool = _alive(battle["enemies"])

    if target_pool and rng.random() < success_chance:
        non_bosses = [
            enemy
            for enemy in target_pool
            if enemy["name"] != battle["stage"]["boss"]
        ]
        target = rng.choice(non_bosses or target_pool)
        target["hp"] = 0
        target["alive"] = False
        battle["log"].append(
            f"🗡️ {spy['name']} eliminou {target['name']} antes da primeira rodada."
        )
    else:
        battle["log"].append(
            f"🌫️ {spy['name']} não encontrou uma abertura para a infiltração."
        )

    if rng.random() < death_chance:
        spy["hp"] = 0
        spy["alive"] = False
        battle["log"].append(
            f"☠️ {spy['name']} foi descoberto e caiu durante a infiltração."
        )


def _command_multipliers(battle: dict) -> tuple[float, float, list[str]]:
    notes: list[str] = []
    leader = _find_role(battle["player"], "Líder")
    vice = _find_role(battle["player"], "Vice-líder")
    tactician = _find_role(battle["player"], "Tático")

    tactical_score = (
        tactician["skills"].get("Tático", 0) if tactician else 5
    )
    tactical_modifier = (tactical_score - 5) * 0.035

    if leader:
        leader_score = leader["skills"].get("Líder", 0)
        leader_bonus = leader_score * 0.018
        battle["command_mode"] = "leader"
    elif vice:
        if not battle["leader_fell"]:
            battle["leader_fell"] = True
            preservation = min(
                0.95,
                0.40 + vice["skills"].get("Vice-líder", 0) * 0.055,
            )
            notes.append(
                f"⭐ {vice['name']} assumiu o comando e preservou "
                f"{preservation:.0%} do bônus de liderança."
            )
        original_leader = next(
            (
                fighter
                for fighter in battle["player"]
                if fighter["assigned_role"] == "Líder"
            ),
            None,
        )
        original_bonus = (
            original_leader["skills"].get("Líder", 0) * 0.018
            if original_leader
            else 0
        )
        preservation = min(
            0.95,
            0.40 + vice["skills"].get("Vice-líder", 0) * 0.055,
        )
        leader_bonus = original_bonus * preservation
        battle["command_mode"] = "vice"
    else:
        leader_bonus = -0.08
        battle["command_mode"] = "none"

    attack_multiplier = max(0.65, 1 + tactical_modifier + leader_bonus)
    defense_multiplier = max(0.70, 1 + tactical_modifier * 0.65)
    return attack_multiplier, defense_multiplier, notes


def _choose_player_target(players: list[dict], rng: random.Random) -> dict:
    weights = []
    for fighter in players:
        weight = 1.0
        if fighter["assigned_role"] == "Atacante":
            weight += 1.20
        if fighter["assigned_role"] in IMPORTANT_ROLES:
            weight += 0.20
        missing_hp = 1 - fighter["hp"] / fighter["max_hp"]
        weight += missing_hp * 0.50
        weights.append(weight)
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
    importance_bonus = 0.12 if original_target["assigned_role"] in IMPORTANT_ROLES else 0
    danger_bonus = 0.10 if original_target["hp"] < original_target["max_hp"] * 0.42 else 0
    chance = min(0.72, 0.08 + guard_score * 0.045 + importance_bonus + danger_bonus)
    if rng.random() < chance:
        return defender, True
    return original_target, False


def play_round(
    battle: dict,
    rng: random.Random | None = None,
) -> dict:
    rng = rng or random.Random()
    if battle["status"] != "active":
        return battle

    battle["round"] += 1
    round_number = battle["round"]
    battle["log"].append(f"— Rodada {round_number} —")

    if round_number == 1:
        _resolve_spy(battle, rng)

    player_alive = _alive(battle["player"])
    enemy_alive = _alive(battle["enemies"])
    if not player_alive or not enemy_alive:
        return _finalize_status(battle)

    attack_multiplier, defense_multiplier, notes = _command_multipliers(battle)
    battle["log"].extend(notes)

    for attacker in list(player_alive):
        enemy_alive = _alive(battle["enemies"])
        if not attacker["alive"] or not enemy_alive:
            break
        target = rng.choice(enemy_alive)
        damage, critical = _damage(
            attacker,
            target,
            attack_multiplier,
            1.0,
            rng,
        )
        eliminated = _apply_hit(target, damage)
        marker = " CRÍTICO" if critical else ""
        ending = " e eliminou o alvo" if eliminated else ""
        battle["log"].append(
            f"⚔️ {attacker['name']} causou {damage} em "
            f"{target['name']}{marker}{ending}."
        )

    for attacker in list(_alive(battle["enemies"])):
        player_alive = _alive(battle["player"])
        if not attacker["alive"] or not player_alive:
            break
        original_target = _choose_player_target(player_alive, rng)
        target, intercepted = _maybe_intercept(
            battle["player"],
            original_target,
            rng,
        )
        if intercepted:
            battle["log"].append(
                f"🛡️ {target['name']} interceptou o golpe destinado a "
                f"{original_target['name']}."
            )
        enemy_multiplier = battle["stage"]["difficulty"]
        damage, critical = _damage(
            attacker,
            target,
            enemy_multiplier,
            defense_multiplier,
            rng,
        )
        if target["assigned_role"] == "Defensor":
            guard_score = target["skills"].get("Defensor", 0)
            damage = max(1, round(damage * (1 - guard_score * 0.025)))
        eliminated = _apply_hit(target, damage)
        marker = " CRÍTICO" if critical else ""
        ending = " e derrubou o alvo" if eliminated else ""
        battle["log"].append(
            f"💥 {attacker['name']} causou {damage} em "
            f"{target['name']}{marker}{ending}."
        )

    return _finalize_status(battle)


def _finalize_status(battle: dict) -> dict:
    if not _alive(battle["enemies"]):
        battle["status"] = "victory"
        battle["log"].append("🏆 Vitória! A rota para a próxima ilha foi aberta.")
    elif not _alive(battle["player"]):
        battle["status"] = "defeat"
        battle["log"].append("☠️ A tripulação foi derrotada nesta tentativa.")
    return battle


def recruitment_roll(
    battle: dict,
    existing_names: set[str],
    rng: random.Random | None = None,
) -> dict:
    rng = rng or random.Random()
    leader = _find_role(battle["player"], "Líder")
    if not leader:
        return {
            "attempted": False,
            "success": False,
            "message": "O líder caiu; não foi possível tentar o recrutamento.",
        }

    candidates = [
        enemy
        for enemy in battle["enemies"]
        if enemy["name"] not in existing_names
    ]
    if not candidates:
        return {
            "attempted": False,
            "success": False,
            "message": "Nenhum inimigo novo estava disponível para recrutamento.",
        }

    candidate = next(
        (
            enemy
            for enemy in candidates
            if enemy["name"] == battle["stage"]["boss"]
        ),
        rng.choice(candidates),
    )
    leader_score = leader["skills"].get("Líder", 0)
    chance = min(0.68, 0.10 + leader_score * 0.05)
    roll = rng.random()
    success = roll <= chance
    if success:
        message = (
            f"🤝 {candidate['name']} aceitou entrar para a reserva "
            f"({roll:.0%} ≤ {chance:.0%})."
        )
    else:
        message = (
            f"🎲 {candidate['name']} recusou o convite "
            f"({roll:.0%} > {chance:.0%})."
        )
    return {
        "attempted": True,
        "success": success,
        "candidate": candidate["name"],
        "chance": chance,
        "roll": roll,
        "message": message,
    }


def replace_with_reserve(
    crew: dict[str, dict],
    reserve_name: str,
    role: str,
) -> tuple[dict[str, dict], str]:
    reserve = CHARACTER_BY_NAME[reserve_name]
    if role not in reserve["roles"]:
        raise ValueError(f"{reserve_name} não pode exercer a função {role}.")
    updated = copy.deepcopy(crew)
    removed_name = updated[role]["name"]
    updated[role] = copy.deepcopy(reserve)
    return updated, removed_name

