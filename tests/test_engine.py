import random
import unittest

from game_data import ROLES, STAGES
from game_engine import (
    _damage,
    draft_crew,
    play_round,
    recruitment_roll,
    start_battle,
    team_summary,
)


class CrewTests(unittest.TestCase):
    def test_draft_fills_every_role_without_duplicates(self):
        for seed in range(50):
            crew = draft_crew(random.Random(seed))
            self.assertEqual(set(crew), set(ROLES))
            names = [character["name"] for character in crew.values()]
            self.assertEqual(len(names), len(set(names)))
            for role, character in crew.items():
                self.assertIn(role, character["roles"])

    def test_team_summary_has_positive_power(self):
        crew = draft_crew(random.Random(42))
        summary = team_summary(crew)
        self.assertGreater(summary["attack"], 0)
        self.assertGreater(summary["defense"], 0)
        self.assertGreater(summary["power"], 0)


class BattleTests(unittest.TestCase):
    def test_strong_encounter_chance_grows_by_island(self):
        crew = draft_crew(random.Random(2))
        expected = [0.05, 0.10, 0.15, 0.20, 0.25]
        for stage, chance in zip(STAGES, expected):
            battle = start_battle(crew, stage, random.Random(100))
            self.assertAlmostEqual(battle["strong_chance"], chance)

    def test_smoker_logia_can_dodge_all_damage(self):
        class DodgeRoll:
            @staticmethod
            def random():
                return 0.10

        attacker = {
            "attack": 10,
            "assigned_role": "Atacante",
            "skills": {"Atacante": 10},
        }
        smoker = {
            "defense": 9,
            "assigned_role": "Líder",
            "skills": {"Líder": 9},
            "special": "Logia",
        }
        damage, critical, defended, dodged = _damage(
            attacker,
            smoker,
            DodgeRoll(),
        )
        self.assertEqual(damage, 0)
        self.assertFalse(critical)
        self.assertFalse(defended)
        self.assertTrue(dodged)

    def test_life_equals_defense_and_enemy_team_has_six_members(self):
        rng = random.Random(12)
        crew = draft_crew(rng)
        battle = start_battle(crew, STAGES[0], rng)
        self.assertEqual(len(battle["enemies"]), 6)
        for fighter in battle["player"] + battle["enemies"]:
            self.assertEqual(fighter["max_hp"], fighter["defense"])
            self.assertEqual(fighter["hp"], fighter["defense"])

    def test_normal_damage_is_half_attack(self):
        class NoSpecialRolls:
            @staticmethod
            def random():
                return 0.99

        attacker = {
            "attack": 10,
            "assigned_role": "Líder",
            "skills": {},
        }
        defender = {
            "defense": 2,
            "assigned_role": "Líder",
            "skills": {},
        }
        damage, critical, defended, dodged = _damage(
            attacker,
            defender,
            NoSpecialRolls(),
        )
        self.assertEqual(damage, 5)
        self.assertFalse(critical)
        self.assertFalse(defended)
        self.assertFalse(dodged)

    def test_battle_reaches_terminal_state(self):
        rng = random.Random(8)
        crew = draft_crew(rng)
        battle = start_battle(crew, STAGES[0])
        for _ in range(30):
            play_round(battle, rng)
            if battle["status"] != "active":
                break
        self.assertIn(battle["status"], {"victory", "defeat"})

    def test_recruitment_returns_structured_result(self):
        rng = random.Random(3)
        crew = draft_crew(rng)
        battle = start_battle(crew, STAGES[0])
        while battle["status"] == "active":
            play_round(battle, rng)
        if battle["status"] == "victory":
            result = recruitment_roll(
                battle,
                {character["name"] for character in crew.values()},
                set(),
                rng,
            )
            self.assertIn("success", result)
            self.assertIn("message", result)

    def test_recruitment_uses_fixed_half_chance_and_free_role(self):
        rng = random.Random(9)
        crew = draft_crew(rng)
        battle = start_battle(crew, STAGES[0], rng)
        while battle["status"] == "active":
            play_round(battle, rng)
        if battle["status"] == "victory":
            result = recruitment_roll(
                battle,
                {character["name"] for character in crew.values()},
                {"Atacante"},
                rng,
            )
            if result["attempted"]:
                self.assertEqual(result["chance"], 0.50)
                self.assertNotEqual(result["reserve_role"], "Atacante")


if __name__ == "__main__":
    unittest.main()
