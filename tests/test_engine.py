import random
import unittest

from game_data import ROLES, STAGES
from game_engine import (
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
                rng,
            )
            self.assertIn("success", result)
            self.assertIn("message", result)


if __name__ == "__main__":
    unittest.main()

