import random
import unittest
from collections import Counter

from game_data import (
    BOSSES,
    BOSSES_BY_PHASE,
    CHARACTER_BY_NAME,
    ENEMY_CHARACTERS,
    PLAYABLE_CHARACTERS,
    PLAYABLE_DRAW_GROUPS,
    RANK_ORDER,
    ROLES,
    STAGES,
)
from game_engine import (
    _damage,
    boss_aftermath,
    choose_campaign_bosses,
    choose_campaign_boss_locations,
    draft_candidate_group,
    draft_crew,
    enemy_combat_multipliers,
    island_power_index,
    play_round,
    recruitment_roll,
    replace_survivor_with_recruit,
    enemy_group_strength,
    select_enemy_team,
    select_enemy_group,
    start_battle,
    triggers_imu_event,
)


class DataTests(unittest.TestCase):
    def test_workbook_catalogs_are_loaded(self):
        self.assertEqual(len(PLAYABLE_CHARACTERS), 151)
        self.assertEqual(len(ENEMY_CHARACTERS), 152)
        self.assertEqual(len(BOSSES), 12)
        self.assertEqual(len(BOSSES_BY_PHASE["Blue"]), 4)
        self.assertEqual(len(BOSSES_BY_PHASE["Paraíso"]), 8)
        self.assertEqual(
            set(ROLES),
            {"Capitão", "Imediato", "Atacante", "Defensor", "Tático", "Espião"},
        )

    def test_public_attributes_use_ranks_and_internal_values_use_zero_to_hundred(self):
        for character in PLAYABLE_CHARACTERS + ENEMY_CHARACTERS:
            self.assertIn(character["rank"], RANK_ORDER)
            self.assertIn(character["attack_rank"], RANK_ORDER)
            self.assertIn(character["defense_rank"], RANK_ORDER)
            self.assertIn(character["hp_rank"], RANK_ORDER)
            self.assertLessEqual(character["attack"], 100)
            self.assertLessEqual(character["defense"], 100)
            self.assertLessEqual(character["max_hp"], 100)

    def test_combat_values_are_derived_from_over_ranks(self):
        luffy = next(
            character
            for character in PLAYABLE_CHARACTERS
            if character["name"] == "Luffy"
            and character["arc"] == "East Blue"
        )
        self.assertEqual(luffy["attack_rank"], "B")
        self.assertEqual(luffy["attack"], 75)
        self.assertEqual(luffy["hp_rank"], "B")
        self.assertEqual(luffy["max_hp"], 75)

    def test_moomoo_is_not_a_straw_hat_enemy_group(self):
        moomoo = next(
            character
            for character in ENEMY_CHARACTERS
            if character["name"] == "MooMoo"
        )
        self.assertEqual(moomoo["draw_groups"], ["Piratas do Arlong"])


class CrewTests(unittest.TestCase):
    def test_group_draw_returns_at_most_six_members_from_group(self):
        draw = draft_candidate_group({}, random.Random(4))
        self.assertTrue(draw["options"])
        expected_names = {
            character["name"]
            for character in PLAYABLE_CHARACTERS
            if draw["group"] in character["draw_groups"]
        }
        shown_names = {
            option["character"]["name"] for option in draw["options"]
        }
        self.assertLessEqual(len(shown_names), 6)
        self.assertGreaterEqual(len(shown_names), 5)
        self.assertLessEqual(shown_names, expected_names)
        if len(expected_names) <= 6:
            self.assertEqual(shown_names, expected_names)
        for option in draw["options"]:
            self.assertIn(
                draw["group"],
                option["character"]["draw_groups"],
            )

    def test_group_draw_marks_selected_names_and_occupied_roles_unavailable(self):
        first = draft_candidate_group({}, random.Random(7))
        option = next(item for item in first["options"] if item["available"])
        role = option["roles"][0]
        selected = {role: option["character"]}
        found_selected = False
        for seed in range(100):
            next_draw = draft_candidate_group(selected, random.Random(seed))
            for candidate in next_draw["options"]:
                self.assertNotIn(role, candidate["roles"])
                if candidate["character"]["name"] == option["character"]["name"]:
                    self.assertFalse(candidate["available"])
                    found_selected = True
            if found_selected:
                break
        self.assertTrue(found_selected)

    def test_appeared_group_has_half_weight_on_reroll(self):
        baseline = Counter(
            draft_candidate_group({}, random.Random(seed))["group"]
            for seed in range(80)
        )
        target = baseline.most_common(1)[0][0]
        penalized = Counter(
            draft_candidate_group(
                {},
                random.Random(seed),
                {target: 1},
            )["group"]
            for seed in range(80)
        )
        self.assertLess(penalized[target], baseline[target])

    def test_groups_with_fewer_than_five_members_are_never_drawn(self):
        valid_groups = {
            group
            for group in PLAYABLE_DRAW_GROUPS
            if sum(
                group in character["draw_groups"]
                for character in PLAYABLE_CHARACTERS
            )
            >= 5
        }
        drawn = {
            draft_candidate_group({}, random.Random(seed))["group"]
            for seed in range(40)
        }
        self.assertTrue(drawn)
        self.assertLessEqual(drawn, valid_groups)

    def test_draft_fills_every_role_without_duplicate_names(self):
        for seed in range(20):
            crew = draft_crew(random.Random(seed))
            self.assertEqual(set(crew), set(ROLES))
            names = [character["name"] for character in crew.values()]
            self.assertEqual(len(names), len(set(names)))
            for role, character in crew.items():
                self.assertIn(role, character["roles"])


class EnemyTeamTests(unittest.TestCase):
    def test_enemy_team_has_at_most_six_unique_members_from_one_group(self):
        for index, stage in enumerate(STAGES):
            group = select_enemy_group(
                stage["location_index"],
                random.Random(index),
                arc=stage["arc"],
            )
            grouped_stage = {**stage, "enemy_group": group}
            team = select_enemy_team(grouped_stage, random.Random(index))
            names = [character["name"] for character in team]
            self.assertLessEqual(len(team), 6)
            self.assertEqual(len(names), len(set(names)))
            for character in team:
                self.assertIn(group, character["draw_groups"])

    def test_captain_is_prioritized_within_selected_group(self):
        for group in {
            character["draw_groups"][0]
            for character in ENEMY_CHARACTERS
            if character["draw_groups"]
        }:
            team = select_enemy_team(
                {"location_index": 1, "enemy_group": group, "arc": None},
                random.Random(2),
            )
            captains = [
                character for character in team if "Capitão" in character["roles"]
            ]
            if captains:
                self.assertIn("Capitão", team[0]["roles"])

    def test_stronger_groups_are_more_likely_near_campaign_end(self):
        early = [
            enemy_group_strength(select_enemy_group(1, random.Random(seed)))
            for seed in range(100)
        ]
        late = [
            enemy_group_strength(select_enemy_group(5, random.Random(seed)))
            for seed in range(100)
        ]
        self.assertGreater(sum(late) / len(late), sum(early) / len(early))

    def test_enemy_groups_are_not_repeated_when_excluded(self):
        faced = set()
        for stage in STAGES:
            group = select_enemy_group(
                stage["location_index"],
                random.Random(stage["location_index"]),
                faced,
                stage["arc"],
            )
            self.assertNotIn(group, faced)
            faced.add(group)
        self.assertEqual(len(faced), len(STAGES))

    def test_enemy_group_selection_respects_arc(self):
        blue_group = select_enemy_group(1, random.Random(1), arc="East Blue")
        paradise_group = select_enemy_group(6, random.Random(1), arc="Paraíso")
        blue_team = select_enemy_team(
            {
                "location_index": 1,
                "enemy_group": blue_group,
                "arc": "East Blue",
            },
            random.Random(1),
        )
        paradise_team = select_enemy_team(
            {
                "location_index": 6,
                "enemy_group": paradise_group,
                "arc": "Paraíso",
            },
            random.Random(1),
        )
        self.assertTrue(all(character["arc"] == "East Blue" for character in blue_team))
        self.assertTrue(all(character["arc"] == "Paraíso" for character in paradise_team))

    def test_small_enemy_groups_are_not_selected_as_common_filiations(self):
        selected = {
            select_enemy_group(1, random.Random(seed), arc="East Blue")
            for seed in range(80)
        }
        self.assertNotIn("Chapéus de Palha", selected)
        for group in selected:
            members = [
                character
                for character in ENEMY_CHARACTERS
                if group in character["draw_groups"]
                and character["arc"] == "East Blue"
            ]
            self.assertGreaterEqual(len(members), 6)

    def test_campaign_chooses_one_boss_per_part(self):
        bosses = choose_campaign_bosses(random.Random(1))
        self.assertEqual(set(bosses), {"Blue", "Paraíso"})
        self.assertEqual(bosses["Blue"]["phase"], "Blue")
        self.assertEqual(bosses["Paraíso"]["phase"], "Paraíso")
        locations = choose_campaign_boss_locations(
            STAGES,
            bosses,
            random.Random(2),
        )
        self.assertIn(locations["Blue"], {1, 2, 3, 4, 5})
        self.assertIn(locations["Paraíso"], {6, 7, 8, 9, 10})
        stage = {**STAGES[4], "boss": bosses["Blue"]}
        team = select_enemy_team(stage, random.Random(1))
        self.assertEqual(
            [character["name"] for character in team],
            bosses["Blue"]["required_names"][: len(team)],
        )


class BattleTests(unittest.TestCase):
    def test_imu_event_uses_configured_chance(self):
        class FixedRoll:
            def __init__(self, value):
                self.value = value

            def random(self):
                return self.value

        self.assertTrue(triggers_imu_event(FixedRoll(0.009)))
        self.assertFalse(triggers_imu_event(FixedRoll(0.01)))

    def test_battle_uses_spreadsheet_hp_and_role_bonuses(self):
        crew = draft_crew(random.Random(12))
        battle = start_battle(crew, STAGES[0], random.Random(12))
        for fighter in battle["player"]:
            source = crew[fighter["assigned_role"]]
            self.assertEqual(fighter["max_hp"], source["max_hp"])
            expected_attack = source["attack"] + (
                5 if fighter["assigned_role"] == "Atacante" else 0
            )
            expected_defense = source["defense"] + (
                5 if fighter["assigned_role"] == "Defensor" else 0
            )
            self.assertEqual(fighter["attack"], expected_attack)
            self.assertEqual(fighter["defense"], expected_defense)

    def test_incomplete_enemy_group_receives_size_bonus_and_blocks_boss_recruitment(self):
        crew = draft_crew(random.Random(12))
        mihawk = next(
            character
            for character in ENEMY_CHARACTERS
            if character["name"] == "Mihawk"
        )
        boss = next(boss for boss in BOSSES if boss["name"] == "Mihawk")
        stage = {
            "location_index": 5,
            "name": "Duelo",
            "phase": "Blue",
            "arc": "East Blue",
            "boss": boss,
            "reward": 0,
        }
        battle = start_battle(crew, stage, random.Random(12))
        self.assertEqual(len(battle["enemies"]), 1)
        self.assertEqual(battle["enemy_size_multiplier"], 2.25)
        fighter = battle["enemies"][0]
        attack_multiplier, durability_multiplier = enemy_combat_multipliers(
            mihawk, 5, 1
        )
        self.assertGreater(attack_multiplier, 2.25)
        self.assertGreater(durability_multiplier, 2.25)
        self.assertEqual(
            fighter["attack"],
            round((mihawk["attack"] + 5) * attack_multiplier),
        )
        self.assertEqual(
            fighter["defense"],
            round(mihawk["defense"] * durability_multiplier),
        )
        self.assertEqual(
            fighter["max_hp"],
            round(mihawk["max_hp"] * durability_multiplier),
        )
        self.assertEqual(mihawk["attack"], 92)
        result = recruitment_roll(
            battle,
            set(),
            "Mihawk",
            random.Random(1),
        )
        self.assertFalse(result["attempted"])

    def test_island_attack_difficulty_adds_five_percent_and_stops_after_blue(self):
        character = next(
            item
            for item in ENEMY_CHARACTERS
            if item["rank"] == "C" and "Capitão" not in item["roles"]
        )
        first_attack, first_durability = enemy_combat_multipliers(
            character, 1, 6
        )
        self.assertEqual(first_attack, 1.0)
        self.assertEqual(first_durability, 1.0)
        for island in range(2, 6):
            attack, durability = enemy_combat_multipliers(
                character, island, 6
            )
            self.assertEqual(attack, 1 + 0.05 * (island - 1))
            self.assertEqual(durability, 1.0)
        paradise_attack, paradise_durability = enemy_combat_multipliers(
            character, 10, 6
        )
        self.assertEqual(island_power_index(10), 4)
        self.assertEqual(paradise_attack, 1.20)
        self.assertEqual(paradise_durability, 1.0)

    def test_high_tiers_and_enemy_captains_receive_significant_bonuses(self):
        tier_a = next(
            item
            for item in ENEMY_CHARACTERS
            if item["rank"] == "A" and "Capitão" not in item["roles"]
        )
        tier_s = next(
            item
            for item in ENEMY_CHARACTERS
            if item["rank"] == "S" and "Capitão" not in item["roles"]
        )
        tier_s = {**tier_s, "name": "Inimigo S comum"}
        captain_s = next(
            item
            for item in ENEMY_CHARACTERS
            if item["rank"] == "S" and "Capitão" in item["roles"]
        )
        _, a_durability = enemy_combat_multipliers(tier_a, 1, 6)
        _, s_durability = enemy_combat_multipliers(tier_s, 1, 6)
        _, captain_durability = enemy_combat_multipliers(captain_s, 1, 6)
        self.assertGreater(a_durability, 1.0)
        self.assertGreater(s_durability, a_durability)
        self.assertGreater(captain_durability, s_durability)

    def test_mihawk_receives_double_the_normal_enemy_bonus(self):
        mihawk = next(
            item for item in ENEMY_CHARACTERS if item["name"] == "Mihawk"
        )
        comparable = {**mihawk, "name": "Outro Espadachim"}
        normal_attack, normal_durability = enemy_combat_multipliers(
            comparable, 5, 1
        )
        mihawk_attack, mihawk_durability = enemy_combat_multipliers(
            mihawk, 5, 1
        )
        self.assertAlmostEqual(
            mihawk_attack - 1,
            (normal_attack - 1) * 2,
        )
        self.assertAlmostEqual(
            mihawk_durability - 1,
            (normal_durability - 1) * 2,
        )

    def test_normal_damage_is_based_on_internal_attack(self):
        class NoSpecialRolls:
            @staticmethod
            def random():
                return 0.99

        attacker = {"attack": 100, "assigned_role": "Capitão", "skills": {}}
        defender = {"defense": 10, "assigned_role": "Capitão", "skills": {}}
        damage, critical, defended, dodged = _damage(
            attacker,
            defender,
            NoSpecialRolls(),
        )
        self.assertEqual(damage, 35)
        self.assertFalse(critical)
        self.assertFalse(defended)
        self.assertFalse(dodged)

    def test_battle_reaches_terminal_state(self):
        rng = random.Random(8)
        battle = start_battle(draft_crew(rng), STAGES[1], rng)
        for _ in range(40):
            play_round(battle, rng)
            if battle["status"] != "active":
                break
        self.assertIn(battle["status"], {"victory", "defeat"})

    def test_recruitment_uses_enemy_chance_and_captain_rank(self):
        captain = CHARACTER_BY_NAME["Luffy"]
        battle = {
            "player": [
                {
                    "name": captain["name"],
                    "assigned_role": "Capitão",
                    "skills": captain["skills"],
                }
            ],
            "enemies": [
                {
                    "name": "Pirata Buggy",
                    "assigned_role": "Atacante",
                    "recruitment_chance": 0.50,
                }
            ],
        }
        result = recruitment_roll(
            battle,
            set(),
            "Pirata Buggy",
            random.Random(1),
        )
        self.assertTrue(result["attempted"])
        self.assertAlmostEqual(
            result["chance"],
            0.50 + captain["skills"]["Capitão"] * 0.001,
        )
        self.assertNotIn("%", result["message"])

    def test_recruit_can_only_replace_a_compatible_survivor(self):
        battle = {
            "player": [],
            "enemies": [
                {
                    "name": "Pirata Buggy",
                    "assigned_role": "Atacante",
                    "recruitment_chance": 0.50,
                }
            ],
        }
        crew = draft_crew(random.Random(5))
        battle = start_battle(crew, STAGES[0], random.Random(5))
        for fighter in battle["player"]:
            fighter["alive"] = fighter["assigned_role"] == "Atacante"
        updated = replace_survivor_with_recruit(
            crew,
            battle,
            "Pirata Buggy",
            "Atacante",
        )
        self.assertEqual(updated["Atacante"]["name"], "Pirata Buggy")
        with self.assertRaises(ValueError):
            replace_survivor_with_recruit(
                crew,
                battle,
                "Pirata Buggy",
                "Defensor",
            )

    def test_boss_aftermath_applies_campaign_statuses(self):
        crew = draft_crew(random.Random(4))
        battle = {
            "status": "victory",
            "stage": {"boss_key": "kuzan"},
            "post_battle": {
                "lost_names": [],
                "debilitated_names": [],
                "frozen_names": [next(iter(crew.values()))["name"]],
            },
        }
        result = boss_aftermath(battle, crew, random.Random(1))
        frozen_name = next(iter(crew.values()))["name"]
        self.assertEqual(
            result["statuses"][frozen_name],
            {"kind": "congelado", "skip_battles": 1},
        )


if __name__ == "__main__":
    unittest.main()
