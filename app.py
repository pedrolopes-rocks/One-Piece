from __future__ import annotations

import base64
import copy
import html
import random
import time
from pathlib import Path

import streamlit as st

from game_data import (
    CHARACTER_BY_NAME,
    LOCATIONS,
    ROLES,
    STAGES,
)
from game_engine import (
    boss_aftermath,
    choose_campaign_bosses,
    choose_campaign_boss_locations,
    draft_candidate_group,
    play_round,
    recruitment_roll,
    replace_survivor_with_recruit,
    start_battle,
    triggers_imu_event,
)


st.set_page_config(
    page_title="Rota dos Mares",
    page_icon="🏴‍☠️",
    layout="wide",
    initial_sidebar_state="collapsed",
)


CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Pirata+One&family=Inter:wght@400;600;700;800&display=swap');

:root {
    --ink: #102b3f;
    --paper: #f3dfad;
    --gold: #f4b942;
    --red: #c94135;
    --sea: #087f9c;
    --deep-sea: #064b65;
    --foam: #dff8f4;
}

.stApp {
    background:
        radial-gradient(circle at 12% 4%, rgba(244,185,66,.17), transparent 25rem),
        linear-gradient(160deg, #062c3c 0%, #07506a 48%, #083b50 100%);
    color: #f7f4e9;
}

.block-container { max-width: 1380px; padding-top: 1.35rem; }

h1, h2, h3 {
    font-family: "Pirata One", Georgia, serif !important;
    letter-spacing: .04em;
}

h1 { color: #ffd066 !important; text-shadow: 0 3px 0 #7f291f; }
h2, h3 { color: #ffe4a3 !important; }

[data-testid="stMetric"] {
    background: rgba(5, 39, 54, .72);
    border: 1px solid rgba(255, 226, 158, .25);
    border-radius: 16px;
    padding: .7rem 1rem;
}

[data-testid="stMetricValue"] { color: #ffd066; }

.hero {
    padding: 1.2rem 1.5rem;
    border-radius: 22px;
    background:
        linear-gradient(90deg, rgba(4,39,53,.95), rgba(4,68,88,.83)),
        repeating-linear-gradient(45deg, transparent 0 12px, rgba(255,255,255,.02) 12px 24px);
    border: 1px solid rgba(255, 218, 130, .34);
    box-shadow: 0 18px 50px rgba(0,0,0,.26);
    margin-bottom: 1rem;
}

.hero-kicker {
    color: #7fe0e6;
    text-transform: uppercase;
    font: 800 .72rem/1 "Inter", sans-serif;
    letter-spacing: .2em;
}

.hero-title {
    color: #ffd066;
    font: 3rem/1 "Pirata One", Georgia, serif;
    margin: .35rem 0;
    text-shadow: 0 3px 0 #8b3026;
}

.hero-copy { max-width: 850px; color: #e9f5f3; font: 500 .98rem/1.6 "Inter", sans-serif; }

.crew-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: .75rem;
    margin: .7rem 0 1rem;
}

.crew-card {
    position: relative;
    min-height: 168px;
    border-radius: 18px;
    padding: 1rem;
    overflow: hidden;
    background: linear-gradient(145deg, #f7e6b9, #d8b76e);
    color: var(--ink);
    border: 2px solid rgba(255,255,255,.28);
    box-shadow: 0 10px 25px rgba(0,0,0,.23);
}

.crew-card::after {
    content: "";
    position: absolute;
    width: 120px;
    height: 120px;
    border: 18px solid rgba(16,43,63,.08);
    border-radius: 50%;
    right: -45px;
    bottom: -50px;
}

.role-label {
    text-transform: uppercase;
    letter-spacing: .14em;
    color: #8c342b;
    font: 800 .68rem/1 "Inter", sans-serif;
}

.avatar {
    width: 48px;
    height: 48px;
    display: grid;
    place-items: center;
    float: right;
    border-radius: 50%;
    background: #11394e;
    color: #ffd066;
    border: 3px solid #fff1c9;
    font: 800 1.25rem/1 "Inter", sans-serif;
}

.crew-name {
    font: 2rem/1 "Pirata One", Georgia, serif;
    margin: .65rem 0 .35rem;
    color: #132e40;
}

.rank {
    display: inline-flex;
    min-width: 30px;
    height: 30px;
    align-items: center;
    justify-content: center;
    border-radius: 8px;
    background: #b93b31;
    color: white;
    font: 800 .9rem/1 "Inter", sans-serif;
}

.stat-line {
    display: flex;
    gap: .45rem;
    flex-wrap: wrap;
    margin-top: .55rem;
}

.stat-chip {
    background: rgba(16,43,63,.1);
    padding: .28rem .5rem;
    border-radius: 999px;
    font: 700 .72rem/1 "Inter", sans-serif;
}

.sea-map {
    position: relative;
    min-height: 430px;
    overflow: hidden;
    border-radius: 25px;
    border: 5px solid #c9994f;
    background:
        radial-gradient(ellipse at 7% 66%, #66b56f 0 2.3%, #d6bc69 2.5% 3.4%, transparent 3.7%),
        radial-gradient(ellipse at 16% 48%, #68a65b 0 2.4%, #ceb668 2.6% 3.6%, transparent 3.9%),
        radial-gradient(ellipse at 25% 66%, #4e995c 0 2.5%, #d3b267 2.7% 3.7%, transparent 4%),
        radial-gradient(ellipse at 34% 38%, #72ad64 0 2.5%, #d4b86c 2.7% 3.8%, transparent 4.1%),
        radial-gradient(ellipse at 43% 54%, #42925b 0 2.8%, #d7b96d 3% 4.1%, transparent 4.4%),
        radial-gradient(ellipse at 58% 54%, #6aa45c 0 2.3%, #c7a963 2.5% 3.5%, transparent 3.8%),
        radial-gradient(ellipse at 67% 66%, #5d9d5d 0 2.6%, #ceb668 2.8% 3.8%, transparent 4.1%),
        radial-gradient(ellipse at 76% 38%, #70a95f 0 2.6%, #d6bc69 2.8% 3.9%, transparent 4.2%),
        radial-gradient(ellipse at 85% 56%, #5f8f59 0 2.4%, #c7a963 2.6% 3.6%, transparent 3.9%),
        radial-gradient(ellipse at 94% 40%, #6f8753 0 2.6%, #c7a963 2.8% 3.8%, transparent 4.1%),
        repeating-radial-gradient(circle at 25% 20%, rgba(255,255,255,.08) 0 2px, transparent 3px 30px),
        linear-gradient(155deg, #23a6ba 0%, #087b9e 48%, #075976 100%);
    box-shadow: inset 0 0 55px rgba(2,34,50,.38), 0 16px 35px rgba(0,0,0,.22);
}

.sea-map::before {
    content: "";
    position: absolute;
    inset: 0;
    opacity: .42;
    background:
        repeating-linear-gradient(12deg, transparent 0 31px, rgba(224,250,245,.13) 32px 34px, transparent 35px 68px);
    pointer-events: none;
}

.route-svg { position: absolute; inset: 0; width: 100%; height: 100%; }
.route-path {
    fill: none;
    stroke: rgba(255,235,171,.78);
    stroke-width: 1.1;
    stroke-dasharray: 2.2 1.8;
    vector-effect: non-scaling-stroke;
}

.reverse-mountain {
    position: absolute;
    left: 50%;
    top: 50%;
    width: 190px;
    height: 300px;
    transform: translate(-50%, -50%);
    z-index: 1;
    pointer-events: none;
}
.reverse-mountain::before {
    content: "";
    position: absolute;
    left: 50%;
    top: 30px;
    width: 118px;
    height: 214px;
    transform: translateX(-50%);
    clip-path: polygon(50% 0, 100% 100%, 0 100%);
    background:
        linear-gradient(135deg, transparent 0 38%, rgba(255,255,255,.76) 39% 52%, transparent 53%),
        linear-gradient(160deg, #7f765f 0%, #554b3f 48%, #2f3d45 100%);
    border: 2px solid rgba(255,239,189,.58);
    box-shadow: 0 14px 22px rgba(3,34,49,.38);
}
.reverse-mountain::after {
    content: "";
    position: absolute;
    left: 50%;
    top: 0;
    width: 24px;
    height: 300px;
    transform: translateX(-50%);
    border-radius: 999px;
    background:
        linear-gradient(
            to bottom,
            transparent 0,
            rgba(191,247,255,.8) 18%,
            rgba(42,166,186,.9) 52%,
            rgba(191,247,255,.75) 82%,
            transparent 100%
        );
    opacity: .85;
}
.reverse-divider {
    position: absolute;
    left: 50%;
    top: 0;
    width: 118px;
    height: 100%;
    transform: translateX(-50%);
    z-index: 0;
    pointer-events: none;
    background:
        linear-gradient(
            to right,
            transparent 0,
            rgba(21,73,86,.35) 26%,
            rgba(230,217,166,.2) 50%,
            rgba(21,73,86,.35) 74%,
            transparent 100%
        );
}

.map-node {
    position: absolute;
    transform: translate(-50%, -50%);
    width: 22px;
    height: 22px;
    border-radius: 50%;
    border: 3px solid #ffefbd;
    background: #5c6f73;
    box-shadow: 0 0 0 5px rgba(6,50,68,.27);
    z-index: 2;
}
.map-node.done { background: #2dac75; }
.map-node.current { background: #e44d3c; animation: pulse 1.45s infinite; }
.map-node.locked { filter: grayscale(1); opacity: .72; }
.map-node.reverse {
    width: 18px;
    height: 18px;
    border-color: #fff4ca;
    background: #1c4d5a;
    box-shadow: 0 0 0 7px rgba(255,230,154,.2);
}

.map-label {
    position: absolute;
    transform: translate(-50%, 18px);
    width: 135px;
    text-align: center;
    color: #fff8de;
    text-shadow: 0 2px 5px #043044;
    font: 800 .74rem/1.2 "Inter", sans-serif;
    z-index: 3;
}
.map-label small { display: block; color: #bcecf0; font-size: .58rem; margin-top: 3px; }
.map-label.reverse {
    transform: translate(-50%, 70px);
    color: #ffe5a1;
}

.ship {
    position: absolute;
    transform: translate(-50%, -50%);
    width: 54px;
    height: 55px;
    z-index: 4;
    filter: drop-shadow(0 5px 3px rgba(0,0,0,.35));
    animation: bob 2s ease-in-out infinite;
}
.pirate-mast {
    position: absolute;
    left: 27px;
    top: 3px;
    width: 3px;
    height: 34px;
    border-radius: 2px;
    background: #3e281b;
}
.pirate-sail {
    position: absolute;
    left: 29px;
    top: 5px;
    width: 27px;
    height: 24px;
    display: grid;
    place-items: center;
    clip-path: polygon(0 0, 100% 16%, 82% 100%, 0 88%);
    background: linear-gradient(145deg, #151515, #020202);
    border-left: 1px solid #8f7657;
    color: #f3ead4;
    font-size: 15px;
    line-height: 1;
}
.pirate-hull {
    position: absolute;
    left: 5px;
    bottom: 7px;
    width: 45px;
    height: 15px;
    clip-path: polygon(0 0, 100% 0, 82% 100%, 18% 100%);
    background: linear-gradient(#75472a, #2f1b13);
    border-top: 2px solid #c08a4b;
}
.ship::after {
    content: "⚓";
    position: absolute;
    left: 50%;
    top: 78%;
    transform: translateX(-50%);
    font-size: .9rem;
}

@keyframes pulse {
    0%,100% { box-shadow: 0 0 0 5px rgba(255,230,154,.16); }
    50% { box-shadow: 0 0 0 13px rgba(255,230,154,.34); }
}
@keyframes bob {
    0%,100% { margin-top: 0; rotate: -2deg; }
    50% { margin-top: -7px; rotate: 2deg; }
}

.battle-panel {
    padding: 1.1rem 1.25rem;
    border-radius: 14px;
    background: #f4f0e4;
    border: 1px solid #c8bea3;
    color: #18242c;
}
.battle-score {
    display: grid;
    grid-template-columns: 1fr auto 1fr;
    align-items: center;
    gap: 1rem;
    padding-bottom: .8rem;
    border-bottom: 3px solid #d7cfb8;
    font: 800 .9rem/1.2 "Inter", sans-serif;
}
.battle-score .enemy-title { text-align: right; }
.battle-score strong { color: #23805d; font-size: 1.45rem; }
.enemy-title.boss-title {
    color: #d7322d;
    text-transform: uppercase;
    letter-spacing: .08em;
}
.boss-banner {
    margin: .8rem 0 0;
    padding: .65rem .8rem;
    border-radius: 10px;
    background: #3d1718;
    border: 1px solid #d7322d;
    color: #ffd7bd;
    font: 800 .78rem/1.35 "Inter", sans-serif;
    letter-spacing: .03em;
}
.boss-note {
    margin-top: .45rem;
    color: #ffe6d8;
    font-weight: 700;
}
.battle-lineups {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 2rem;
    padding-top: .8rem;
}
.battle-side h4 {
    margin: 0 0 .65rem;
    color: #7c6040;
    font: 800 .72rem/1 "Inter", sans-serif;
    letter-spacing: .16em;
    text-transform: uppercase;
}
.battle-side.enemy h4 { text-align: right; }
.fighter-name {
    margin: .42rem 0;
    font: 800 .86rem/1.25 "Inter", sans-serif;
}
.battle-side.enemy .fighter-name { text-align: right; }
.fighter-name.defeated {
    color: #8a8a82;
    text-decoration: line-through;
    text-decoration-thickness: 2px;
}
.fighter-name.defeated::before { content: "✓ "; color: #23805d; }
.battle-side.player .fighter-name.alive::before { content: "• "; }
.battle-side.enemy .fighter-name.alive::after { content: " •"; }
.unavailable-character {
    color: #7d868b;
    opacity: .62;
    filter: grayscale(1);
}
@media (max-width: 620px) {
    .battle-lineups { gap: .8rem; }
    .fighter-name { font-size: .72rem; }
}

.rule-card {
    min-height: 145px;
    padding: 1rem;
    border-radius: 16px;
    background: rgba(5,39,54,.74);
    border: 1px solid rgba(255,226,158,.2);
}
.rule-icon { font-size: 1.55rem; }
.rule-title { color: #ffd066; font: 800 .86rem/1.2 "Inter", sans-serif; margin: .4rem 0; }
.rule-copy { color: #d8eceb; font: 500 .76rem/1.5 "Inter", sans-serif; }

div.stButton > button {
    border-radius: 12px;
    font-weight: 800;
    border: 1px solid rgba(255,224,151,.55);
}

@media (max-width: 900px) {
    .crew-grid { grid-template-columns: 1fr 1fr; }
    .hero-title { font-size: 2.25rem; }
    .sea-map { min-height: 520px; }
}
@media (max-width: 620px) {
    .crew-grid { grid-template-columns: 1fr; }
}
</style>
"""
st.html(CSS)


def initialize_state() -> None:
    defaults = {
        "crew": {},
        "stage_index": 0,
        "battle": None,
        "berries": 0,
        "wins": 0,
        "last_recruitment": None,
        "recruitment_attempted": False,
        "last_battle_result": None,
        "campaign_defeated": False,
        "game_seed": random.randint(1, 999_999),
        "draft_team": {},
        "crew_rerolls": 0,
        "draft_group_appearances": {},
        "imu_event_active": False,
        "campaign_destroyed": False,
        "destroyed_location_index": None,
        "faced_enemy_groups": [],
        "selected_bosses": {},
        "selected_boss_locations": {},
        "crew_statuses": {},
        "boss_messages": [],
        "allow_understaffed_journey": False,
        "battle_frames": [],
        "battle_frame_index": 0,
        "battle_animation_active": False,
        "preferred_battle_speed": "Normal",
        "battle_last_frame_at": 0.0,
        "current_view": "crew",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    role_migration = {"Líder": "Capitão", "Vice-líder": "Imediato"}
    migrated_crew = {}
    for old_role, character in st.session_state.crew.items():
        role = role_migration.get(old_role, old_role)
        name = character.get("name") if isinstance(character, dict) else None
        if (
            role in ROLES
            and isinstance(character, dict)
            and role in character.get("roles", [])
            and "role_ranks" in character
        ):
            migrated_crew[role] = character
        elif role in ROLES and name in CHARACTER_BY_NAME:
            refreshed = CHARACTER_BY_NAME[name]
            if role in refreshed["roles"]:
                migrated_crew[role] = refreshed
    st.session_state.crew = migrated_crew
    if "reserves" in st.session_state:
        del st.session_state.reserves
    if st.session_state.draft_team and "group" not in st.session_state.draft_team:
        st.session_state.draft_team = {}
    if "crew_options" in st.session_state:
        del st.session_state.crew_options
    if "battle_speed" in st.session_state:
        st.session_state.preferred_battle_speed = st.session_state.battle_speed
        del st.session_state.battle_speed
    if st.session_state.current_view not in {"crew", "journey"}:
        st.session_state.current_view = "crew"
    if not st.session_state.selected_bosses:
        st.session_state.selected_bosses = choose_campaign_bosses(
            random.Random(st.session_state.game_seed)
        )
    if not st.session_state.selected_boss_locations:
        st.session_state.selected_boss_locations = choose_campaign_boss_locations(
            STAGES,
            st.session_state.selected_bosses,
            random.Random(st.session_state.game_seed + 1),
        )


def reset_campaign() -> None:
    st.session_state.crew = {}
    st.session_state.stage_index = 0
    st.session_state.battle = None
    st.session_state.berries = 0
    st.session_state.wins = 0
    st.session_state.last_recruitment = None
    st.session_state.recruitment_attempted = False
    st.session_state.last_battle_result = None
    st.session_state.campaign_defeated = False
    st.session_state.game_seed = random.randint(1, 999_999)
    st.session_state.draft_team = {}
    st.session_state.crew_rerolls = 0
    st.session_state.draft_group_appearances = {}
    st.session_state.imu_event_active = False
    st.session_state.campaign_destroyed = False
    st.session_state.destroyed_location_index = None
    st.session_state.faced_enemy_groups = []
    st.session_state.selected_bosses = choose_campaign_bosses(
        random.Random(st.session_state.game_seed)
    )
    st.session_state.selected_boss_locations = choose_campaign_boss_locations(
        STAGES,
        st.session_state.selected_bosses,
        random.Random(st.session_state.game_seed + 1),
    )
    st.session_state.crew_statuses = {}
    st.session_state.boss_messages = []
    st.session_state.allow_understaffed_journey = False
    st.session_state.battle_frames = []
    st.session_state.battle_frame_index = 0
    st.session_state.battle_animation_active = False
    st.session_state.battle_last_frame_at = 0.0
    st.session_state.current_view = "crew"


def crew_names() -> set[str]:
    return {item["name"] for item in st.session_state.crew.values()}


def draw_crew_group(*, apply_reroll_penalty: bool = False) -> dict:
    appearance_counts = (
        st.session_state.draft_group_appearances
        if apply_reroll_penalty
        else None
    )
    try:
        draw = draft_candidate_group(
            st.session_state.crew,
            group_appearance_counts=appearance_counts,
        )
    except TypeError as error:
        if "group_appearance_counts" not in str(error):
            raise
        # Compatibilidade com processos Streamlit que ainda mantêm a versão
        # anterior do motor carregada em memória.
        draw = draft_candidate_group(st.session_state.crew)
    group = draw["group"]
    appearances = st.session_state.draft_group_appearances
    appearances[group] = appearances.get(group, 0) + 1
    return draw


def crew_card(role: str, character: dict) -> str:
    icon = ROLES[role]["icon"]
    role_chips = "".join(
        (
            f'<span class="stat-chip">{ROLES[character_role]["icon"]} '
            f'{html.escape(character_role)} '
            f'{html.escape(character["role_ranks"][character_role])}</span>'
        )
        for character_role in character["roles"]
    )
    return f"""
    <div class="crew-card">
        <div class="avatar">{html.escape(character["rank"])}</div>
        <div class="role-label">{icon} {html.escape(role)}</div>
        <div class="crew-name">{html.escape(character["name"])}</div>
        <div class="stat-line">{role_chips}</div>
        <div class="stat-line">
            <span class="stat-chip">{html.escape(character["faction"])}</span>
        </div>
    </div>
    """


def render_crew_grid() -> None:
    if not st.session_state.crew:
        st.info("A tripulação ainda não foi formada.")
        return
    cards = "".join(
        crew_card(role, st.session_state.crew[role])
        for role in ROLES
        if role in st.session_state.crew
    )
    st.html(f'<div class="crew-grid">{cards}</div>')


def battle_board_html(battle: dict) -> str:
    def lineup(fighters: list[dict], side: str) -> str:
        def fighter_row(fighter: dict) -> str:
            status = "alive" if fighter["alive"] else "defeated"
            style = ' style="color:#d7322d;"' if fighter.get("boss_member") else ""
            return (
                f'<div class="fighter-name {status}"{style}>'
                f'{html.escape(fighter["name"])} '
                f'({html.escape(fighter["assigned_role"][0])})</div>'
            )

        rows = "".join(
            fighter_row(fighter)
            for fighter in fighters
        )
        title = "Sua tripulação" if side == "player" else "Inimigos"
        if side == "player":
            rows += "".join(
                (
                    f'<div class="fighter-name defeated" '
                    f'style="color:#85d8ff;text-decoration:none;">'
                    f'{html.escape(item["name"])} '
                    f'({html.escape(item["status"])})</div>'
                )
                for item in battle.get("inactive_player", [])
            )
        return (
            f'<div class="battle-side {side}"><h4>{title}</h4>{rows}</div>'
        )

    player_alive = sum(fighter["alive"] for fighter in battle["player"])
    enemy_alive = sum(fighter["alive"] for fighter in battle["enemies"])
    group = battle["stage"]["enemy_group"]
    is_boss = bool(battle["stage"].get("boss_key"))
    enemy_title = (
        f"☠ BOSS · {html.escape(group)}"
        if is_boss
        else html.escape(group)
    )
    enemy_class = "enemy-title boss-title" if is_boss else "enemy-title"
    boss_banner = ""
    if is_boss:
        boss_name = battle["stage"].get("boss", {}).get("name", group)
        boss_banner = (
            '<div class="boss-banner">'
            f'☠ Você encontrou um BOSS: {html.escape(boss_name)}'
            '</div>'
        )
    post_battle_notes = "".join(
        f'<div class="boss-note">{html.escape(message)}</div>'
        for message in st.session_state.get("boss_messages", [])
        if battle["status"] == "victory"
    )
    return f"""
    <div class="battle-panel">
        <div class="battle-score">
            <div>SUA EQUIPE</div>
            <strong>{player_alive} – {enemy_alive}</strong>
            <div class="{enemy_class}">{enemy_title}</div>
        </div>
        {boss_banner}
        {post_battle_notes}
        <div class="battle-lineups">
            {lineup(battle["player"], "player")}
            {lineup(battle["enemies"], "enemy")}
        </div>
    </div>
    """


def render_battle_board(battle: dict) -> None:
    st.html(battle_board_html(battle))


def render_map() -> None:
    if (
        st.session_state.campaign_destroyed
        and st.session_state.destroyed_location_index is not None
    ):
        current = st.session_state.destroyed_location_index
    elif len(st.session_state.crew) < len(ROLES):
        current = 0
    elif st.session_state.stage_index < len(STAGES):
        current = STAGES[st.session_state.stage_index]["location_index"]
    else:
        current = len(LOCATIONS) - 1
    points = " ".join(f"{item['x']},{item['y']}" for item in LOCATIONS)
    node_html = []
    destroyed_location = (
        current if st.session_state.campaign_destroyed else None
    )
    for index, location in enumerate(LOCATIONS):
        if index == destroyed_location:
            continue
        if index < current:
            status = "done"
        elif index == current:
            status = "current"
        else:
            status = "locked"
        reverse_class = (
            " reverse" if location["name"] == "Reverse Mountain" else ""
        )
        node_html.append(
            f"""
            <div class="map-node {status}{reverse_class}" style="left:{location['x']}%;top:{location['y']}%;"></div>
            <div class="map-label{reverse_class}" style="left:{location['x']}%;top:{location['y']}%;">
                {html.escape(location['name'])}
                <small>{html.escape(location['subtitle'])}</small>
            </div>
            """
        )
    ship_location = LOCATIONS[current]
    ship_html = ""
    if not st.session_state.campaign_destroyed:
        ship_html = (
            f'<div class="ship" style="left:{ship_location["x"]}%;'
            f'top:{ship_location["y"]}%;">'
            '<span class="pirate-mast"></span>'
            '<span class="pirate-sail">☠</span>'
            '<span class="pirate-hull"></span></div>'
        )
    st.html(
        f"""
        <div class="sea-map">
            <svg class="route-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
                <polyline class="route-path" points="{points}" />
            </svg>
            <div class="reverse-divider"></div>
            <div class="reverse-mountain"></div>
            {''.join(node_html)}
            {ship_html}
        </div>
        """
    )


def render_imu_event() -> None:
    video_path = Path(__file__).parent / "assets" / "imu_eye_cinematic.mp4"
    video_data = base64.b64encode(video_path.read_bytes()).decode("ascii")
    words = "Para início de conversa este lugar nunca existiu".split()
    word_html = "".join(
        (
            f'<span style="--word-delay:{2.4 + index * 0.43:.2f}s">'
            f"{html.escape(word)}</span>"
        )
        for index, word in enumerate(words)
    )
    st.html(
        f"""
        <style>
        .imu-event {{
            position: fixed;
            inset: 0;
            z-index: 999999;
            display: grid;
            place-items: center;
            overflow: hidden;
            background: #000;
            animation: imu-end 10.5s ease-in forwards;
        }}
        .imu-presence {{
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            opacity: 0;
            filter: contrast(1.12) brightness(.82);
            animation: imu-arrive 3.4s cubic-bezier(.2,.7,.2,1) .35s forwards;
        }}
        .imu-words {{
            position: relative;
            z-index: 2;
            max-width: min(900px, 88vw);
            padding-top: min(58vh, 520px);
            text-align: center;
            color: white;
            font: 500 clamp(1.15rem, 2.4vw, 2rem)/1.65 Georgia, serif;
            letter-spacing: .04em;
            text-shadow: 0 0 12px #000, 0 0 28px #000;
        }}
        .imu-words span {{
            display: inline-block;
            margin-right: .32em;
            opacity: 0;
            transform: translateY(5px);
            animation: imu-word .8s ease-out var(--word-delay) forwards;
        }}
        .erased-place {{
            position: absolute;
            left: 50%;
            bottom: 3vh;
            z-index: 3;
            display: flex;
            align-items: end;
            gap: .2rem;
            transform: translateX(-50%);
            font-size: clamp(2.2rem, 5vw, 4.5rem);
            filter: grayscale(.2) drop-shadow(0 0 12px rgba(255,255,255,.2));
            animation: erase-place 2.2s ease-in 7.7s forwards;
        }}
        .erased-place .tiny-flag {{
            font-size: .5em;
            margin-right: -.55em;
            margin-bottom: .75em;
            z-index: 2;
        }}
        @keyframes imu-arrive {{
            from {{ opacity: 0; transform: scale(1.07); filter: brightness(.3); }}
            to {{ opacity: .98; transform: scale(1); filter: brightness(.82); }}
        }}
        @keyframes imu-word {{
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        @keyframes erase-place {{
            0% {{ opacity: 1; filter: brightness(1); }}
            35% {{ opacity: .9; filter: brightness(4) blur(1px); }}
            100% {{ opacity: 0; transform: translateX(-50%) scale(.15);
                    filter: brightness(8) blur(18px); }}
        }}
        @keyframes imu-end {{
            0%, 93% {{ opacity: 1; }}
            100% {{ opacity: 0; }}
        }}
        </style>
        <div class="imu-event">
            <video class="imu-presence" autoplay muted playsinline preload="auto"
                   aria-label="O olhar de Imu">
                <source src="data:video/mp4;base64,{video_data}"
                        type="video/mp4">
            </video>
            <div class="imu-words">{word_html}</div>
            <div class="erased-place">
                <span class="tiny-flag">🏴‍☠️</span><span>⛵</span><span>🏝️</span>
            </div>
        </div>
        """
    )
    time.sleep(10.6)
    st.session_state.imu_event_active = False
    st.session_state.campaign_destroyed = True
    st.session_state.battle = None
    st.session_state.crew = {}
    st.session_state.draft_team = {}
    st.rerun()


def complete_stage() -> None:
    stage = st.session_state.battle["stage"]
    inactive_names = {
        item["name"] for item in st.session_state.battle.get("inactive_player", [])
    }
    for name in inactive_names:
        st.session_state.crew_statuses.pop(name, None)
    aftermath = boss_aftermath(
        st.session_state.battle,
        st.session_state.crew,
    )
    if aftermath["remove_names"]:
        remove_names = set(aftermath["remove_names"])
        st.session_state.crew = {
            role: character
            for role, character in st.session_state.crew.items()
            if character["name"] not in remove_names
        }
        st.session_state.allow_understaffed_journey = True
    st.session_state.crew_statuses.update(aftermath["statuses"])
    st.session_state.boss_messages = aftermath["messages"]
    st.session_state.berries += stage["reward"]
    st.session_state.wins += 1
    st.session_state.stage_index += 1
    st.session_state.battle = None
    st.session_state.last_recruitment = None
    st.session_state.recruitment_attempted = False
    st.session_state.battle_frames = []
    st.session_state.battle_frame_index = 0
    st.session_state.battle_animation_active = False


def begin_battle(stage: dict) -> None:
    battle_stage = copy.deepcopy(stage)
    boss_location = st.session_state.selected_boss_locations.get(
        battle_stage["phase"]
    )
    if battle_stage["location_index"] == boss_location:
        boss = st.session_state.selected_bosses.get(battle_stage["phase"])
        if boss:
            battle_stage["boss"] = boss
    st.session_state.boss_messages = []
    battle = start_battle(
        st.session_state.crew,
        battle_stage,
        excluded_groups=set(st.session_state.faced_enemy_groups),
        crew_statuses=st.session_state.crew_statuses,
    )
    st.session_state.battle = battle
    group = battle["stage"]["enemy_group"]
    st.session_state.faced_enemy_groups.append(group)
    frames = [copy.deepcopy(battle)]

    def capture_elimination(updated_battle: dict) -> None:
        current_status = tuple(
            fighter["alive"]
            for fighter in updated_battle["player"] + updated_battle["enemies"]
        )
        previous_status = tuple(
            fighter["alive"]
            for fighter in frames[-1]["player"] + frames[-1]["enemies"]
        )
        if current_status != previous_status:
            frames.append(copy.deepcopy(updated_battle))

    for _ in range(100):
        play_round(battle, on_update=capture_elimination)
        if battle["status"] != "active":
            break
    if frames[-1]["status"] != battle["status"]:
        frames.append(copy.deepcopy(battle))

    if battle["status"] == "victory":
        if battle["stage"].get("boss_key"):
            message = "Vitória. A rota para a próxima ilha foi aberta."
        else:
            message = "Vitória. Escolha se deseja tentar um recrutamento."
        st.session_state.last_battle_result = {
            "status": "victory",
            "message": message,
        }
    else:
        st.session_state.last_battle_result = {
            "status": "defeat",
            "message": f"A tripulação foi derrotada em {battle_stage['name']}.",
        }
    st.session_state.battle_frames = frames
    st.session_state.battle_frame_index = 0
    st.session_state.battle_animation_active = True
    st.session_state.battle_last_frame_at = time.time()


def update_battle_speed() -> None:
    st.session_state.preferred_battle_speed = (
        st.session_state.battle_speed_control
    )


@st.fragment(run_every=0.2)
def render_battle_animation() -> None:
    frames = st.session_state.battle_frames
    index = st.session_state.battle_frame_index
    if not frames:
        return

    render_battle_board(frames[index])
    speed_options = ["Lenta", "Normal", "Rápida"]
    st.radio(
        "Velocidade do combate",
        speed_options,
        index=speed_options.index(st.session_state.preferred_battle_speed),
        horizontal=True,
        key="battle_speed_control",
        on_change=update_battle_speed,
    )
    if index >= len(frames) - 1:
        st.session_state.battle_animation_active = False
        if st.session_state.battle["status"] == "defeat":
            st.session_state.campaign_defeated = True
        st.rerun()

    delays = {"Lenta": 1.8, "Normal": 1.0, "Rápida": 0.45}
    now = time.time()
    if now - st.session_state.battle_last_frame_at < delays[
        st.session_state.preferred_battle_speed
    ]:
        return

    if index < len(frames) - 1:
        st.session_state.battle_frame_index += 1
        st.session_state.battle_last_frame_at = now
        if st.session_state.battle_frame_index == len(frames) - 1:
            st.session_state.battle_animation_active = False
            if st.session_state.battle["status"] == "defeat":
                st.session_state.campaign_defeated = True
            st.rerun()


def render_recruitment() -> None:
    battle = st.session_state.battle
    if battle["stage"].get("boss_key"):
        st.info("Após esse confronto, a tripulação segue viagem sem recrutamento.")
        if st.button("Seguir viagem", type="primary"):
            complete_stage()
            st.rerun()
        return
    alive_roles = {
        fighter["assigned_role"]
        for fighter in battle["player"]
        if fighter["alive"]
    }
    candidates = [
        fighter
        for fighter in battle["enemies"]
        if fighter["name"] not in crew_names()
        and alive_roles.intersection(fighter["roles"])
        and fighter.get("recruitment_chance") is not None
        and not fighter.get("boss_member")
    ]

    st.subheader("Recrutamento")
    if not candidates:
        st.info(
            "Nenhum adversário pode ocupar a função de um sobrevivente."
        )
        if st.button("Seguir viagem", type="primary"):
            complete_stage()
            st.rerun()
        return

    if not st.session_state.recruitment_attempted:
        candidate_by_name = {
            fighter["name"]: fighter for fighter in candidates
        }

        def format_candidate(name: str) -> str:
            fighter = candidate_by_name[name]
            roles = " / ".join(
                (
                    f"{role} "
                    f"({fighter['role_ranks'][role]})"
                )
                for role in fighter["roles"]
            )
            return f"{name} — OVER {fighter['rank']} — {roles}"

        selected_name = st.selectbox(
            "Escolha um adversário para tentar recrutar",
            [fighter["name"] for fighter in candidates],
            format_func=format_candidate,
        )
        col_attempt, col_skip = st.columns(2)
        with col_attempt:
            if st.button(
                "Tentar recrutamento",
                type="primary",
                width="stretch",
            ):
                st.session_state.last_recruitment = recruitment_roll(
                    battle,
                    crew_names(),
                    selected_name,
                )
                st.session_state.recruitment_attempted = True
                st.rerun()
        with col_skip:
            if st.button("Não recrutar", width="stretch"):
                complete_stage()
                st.rerun()
        return

    result = st.session_state.last_recruitment
    if not result or not result.get("success"):
        st.info(
            result["message"]
            if result
            else "O recrutamento não foi realizado."
        )
        if st.button("Seguir viagem", type="primary"):
            complete_stage()
            st.rerun()
        return

    recruit_name = result["candidate"]
    recruit = next(
        fighter
        for fighter in candidates
        if fighter["name"] == recruit_name
    )
    replaceable_roles = [
        role
        for role in ROLES
        if role in alive_roles and role in recruit["roles"]
    ]
    st.success(result["message"])
    selected_role = st.selectbox(
        "Escolha o sobrevivente que deixará a tripulação",
        replaceable_roles,
        format_func=lambda role: (
            f"{st.session_state.crew[role]['name']} · {role}"
        ),
    )
    col_confirm, col_cancel = st.columns(2)
    with col_confirm:
        if st.button(
            "Confirmar substituição",
            type="primary",
            width="stretch",
        ):
            st.session_state.crew = replace_survivor_with_recruit(
                st.session_state.crew,
                battle,
                recruit_name,
                selected_role,
            )
            complete_stage()
            st.rerun()
    with col_cancel:
        if st.button("Desistir do recrutamento", width="stretch"):
            complete_stage()
            st.rerun()


initialize_state()

if st.session_state.imu_event_active:
    render_imu_event()

st.html(
    """
    <div class="hero">
        <div class="hero-kicker">Blue e Paraíso</div>
        <div class="hero-title">Rota dos Mares</div>
        <div class="hero-copy">
            Forme sua tripulação, vença os Blues, cruze a montanha e encare
            os conflitos do Paraíso.
        </div>
    </div>
    """
)

def render_journey_view() -> None:
    heading, action = st.columns([0.76, 0.24])
    with heading:
        st.header("🗺️ Nossa jornada")
    with action:
        if st.button(
            "Desistir da campanha",
            width="stretch",
            help="Abandona a jornada e retorna à formação da tripulação.",
        ):
            reset_campaign()
            st.rerun()

    top1, top2, top3, top4 = st.columns(4)
    top1.metric("Vitórias", st.session_state.wins)
    top2.metric("Berries", f"{st.session_state.berries:,}".replace(",", "."))
    top3.metric("Progresso", f"{st.session_state.stage_index}/{len(STAGES)}")
    top4.metric("Tripulantes", len(st.session_state.crew))

    render_map()
    st.write("")

    if st.session_state.stage_index >= len(STAGES):
        st.success(
            "A tripulação venceu os Blues, cruzou a montanha e superou o Paraíso."
        )
    elif st.session_state.campaign_destroyed:
        st.error(
            "Esse lugar nunca existiu. A ilha e sua tripulação foram apagadas."
        )
        if st.button("🔁 Reiniciar campanha", type="primary"):
            reset_campaign()
            st.rerun()
    elif st.session_state.battle_animation_active:
        render_battle_animation()
    elif st.session_state.campaign_defeated:
        if st.session_state.battle:
            render_battle_board(st.session_state.battle)
        result = st.session_state.last_battle_result
        st.error(
            result["message"]
            if result
            else "A tripulação foi derrotada."
        )
        if st.button("🔁 Iniciar nova campanha", type="primary"):
            reset_campaign()
            st.rerun()
    elif (
        len(st.session_state.crew) < len(ROLES)
        and not st.session_state.allow_understaffed_journey
    ):
        st.warning(
            "A tripulação precisa ocupar as seis funções antes de partir."
        )
    elif (
        st.session_state.battle
        and st.session_state.battle["status"] == "victory"
    ):
        render_battle_board(st.session_state.battle)
        st.success(st.session_state.last_battle_result["message"])
        render_recruitment()
    else:
        stage = STAGES[st.session_state.stage_index]
        col_info, col_action = st.columns([0.72, 0.28])
        with col_info:
            st.subheader(stage["name"])
            st.write(stage["description"])
            boss_location = st.session_state.selected_boss_locations.get(
                stage["phase"]
            )
            if stage["location_index"] == boss_location:
                boss = st.session_state.selected_bosses.get(stage["phase"])
                if boss:
                    st.markdown(
                        "☠ Encontro de "
                        "<span style='color:#ff4b43;font-weight:900'>BOSS</span>: "
                        f"<span style='color:#ff4b43;font-weight:800'>"
                        f"{html.escape(boss['name'])}</span>.",
                        unsafe_allow_html=True,
                    )
                else:
                    st.caption("Boss da parte.")
            else:
                st.caption(
                    "A filiação inimiga será sorteada ao iniciar o confronto."
                )
            st.caption(
                "Até 6 inimigos • Recompensa: "
                f"{stage['reward']:,} berries".replace(",", ".")
            )
        with col_action:
            st.write("")
            if st.button("⚔️ Iniciar batalha", type="primary", width="stretch"):
                st.session_state.last_battle_result = None
                st.session_state.last_recruitment = None
                st.session_state.recruitment_attempted = False
                if triggers_imu_event():
                    st.session_state.imu_event_active = True
                    st.session_state.destroyed_location_index = stage[
                        "location_index"
                    ]
                else:
                    begin_battle(stage)
                st.rerun()


def render_role_guide() -> None:
    cards = []
    for role, data in ROLES.items():
        cards.append(
            f"""
            <div class="rule-card">
                <div class="rule-icon">{data['icon']}</div>
                <div class="rule-title">{html.escape(role)}</div>
                <div class="rule-copy">{html.escape(data['description'])}</div>
            </div>
            """
        )
    with st.expander("📜 Guia de funções"):
        st.html(f'<div class="crew-grid">{"".join(cards)}</div>')


def render_crew_view() -> None:
    st.header("🏴‍☠️ Tripulação")
    crew_complete = len(st.session_state.crew) == len(ROLES)
    action1, action2, action3 = st.columns([0.34, 0.33, 0.33])
    with action1:
        has_candidate = bool(st.session_state.draft_team)
        rerolls_left = 2 - st.session_state.crew_rerolls
        draft_label = (
            f"🎲 Resortear grupo ({rerolls_left} restantes)"
            if has_candidate
            else "🎲 Sortear grupo"
        )
        if st.button(
            draft_label,
            type="primary",
            width="stretch",
            disabled=(
                crew_complete
                or (has_candidate and rerolls_left <= 0)
            ),
            help=(
                "Sorteia um grupo e apresenta seus personagens elegíveis."
            ),
        ):
            if has_candidate:
                st.session_state.crew_rerolls += 1
            st.session_state.draft_team = draw_crew_group(
                apply_reroll_penalty=has_candidate
            )
            st.session_state.battle = None
            st.session_state.last_recruitment = None
            st.rerun()
    with action2:
        if crew_complete:
            if st.button(
                "Jogar",
                type="primary",
                width="stretch",
                help="Inicia a jornada com a tripulação formada.",
            ):
                st.session_state.current_view = "journey"
                st.rerun()
        elif st.session_state.crew or st.session_state.draft_team:
            if st.button(
                "Recomeçar formação",
                width="stretch",
                help="Descarta as escolhas atuais e começa uma nova formação.",
            ):
                reset_campaign()
                st.rerun()
    with action3:
        st.metric(
            "Composição da equipe",
            f"{len(st.session_state.crew)}/{len(ROLES)}",
        )

    if st.session_state.draft_team and not crew_complete:
        draw = st.session_state.draft_team
        st.subheader(f"Grupo sorteado: {draw['group']}")
        st.caption(
            "Escolha um personagem e uma função disponível. O mesmo nome "
            "não pode ocupar duas vagas."
        )
        options = draw["options"]
        option_columns = st.columns(min(3, len(options)))
        for option_index, option in enumerate(options):
            character = option["character"]
            column = option_columns[option_index % len(option_columns)]
            with column:
                name_class = (
                    "" if option["available"] else "unavailable-character"
                )
                st.markdown(
                    f'<div class="{name_class}"><h4>{html.escape(character["name"])}</h4></div>',
                    unsafe_allow_html=True,
                )
                st.write(f"OVER **{character['rank']}**")
                st.caption(
                    "Funções: "
                    + " / ".join(
                        (
                            f"{role} "
                            f"({character['role_ranks'][role]})"
                        )
                        for role in character["roles"]
                    )
                )
                st.caption(character["faction"])
                if not option["available"]:
                    st.caption(option["unavailable_reason"])
                else:
                    for role in option["roles"]:
                        role_rank = character["role_ranks"][role]
                        if st.button(
                            f"{ROLES[role]['icon']} {role} · Rank {role_rank}",
                            key=(
                                f"choose_{draw['group']}_{option_index}_"
                                f"{character['name']}_{role}"
                            ),
                            type="primary",
                            width="stretch",
                        ):
                            st.session_state.crew[role] = character
                            if len(st.session_state.crew) < len(ROLES):
                                st.session_state.draft_team = draw_crew_group()
                            else:
                                st.session_state.draft_team = {}
                            st.session_state.battle = None
                            st.session_state.last_recruitment = None
                            st.rerun()
        st.caption(f"Resorteios utilizados: {st.session_state.crew_rerolls}/2")

    render_crew_grid()

    if st.session_state.crew:
        m1, m2, m3 = st.columns(3)
        captain = st.session_state.crew.get("Capitão")
        tactician = st.session_state.crew.get("Tático")
        m1.metric("Tripulação", f"{len(st.session_state.crew)}/{len(ROLES)}")
        m2.metric(
            "Capitão",
            captain["role_ranks"]["Capitão"] if captain else "—",
        )
        m3.metric(
            "Tático",
            tactician["role_ranks"]["Tático"] if tactician else "—",
        )

    render_role_guide()


if st.session_state.current_view == "journey":
    if (
        len(st.session_state.crew) < len(ROLES)
        and not st.session_state.campaign_destroyed
        and not st.session_state.allow_understaffed_journey
    ):
        st.session_state.current_view = "crew"
        st.rerun()
    render_journey_view()
else:
    render_crew_view()
