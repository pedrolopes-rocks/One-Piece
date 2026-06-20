from __future__ import annotations

import base64
import html
import random
import time
from pathlib import Path

import pandas as pd
import streamlit as st

from game_data import (
    CHARACTER_BY_NAME,
    CHARACTERS,
    LOCATIONS,
    RANK_ORDER,
    ROLES,
    STAGES,
)
from game_engine import (
    draft_candidate_team,
    play_round,
    recruitment_roll,
    replace_with_reserve,
    start_battle,
    team_summary,
    triggers_imu_event,
)


st.set_page_config(
    page_title="Rota dos Mares — Demo East Blue",
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
        radial-gradient(ellipse at 18% 77%, #66b56f 0 2.8%, #d6bc69 3% 4.2%, transparent 4.5%),
        radial-gradient(ellipse at 27% 50%, #68a65b 0 3%, #ceb668 3.2% 4.5%, transparent 4.8%),
        radial-gradient(ellipse at 45% 70%, #4e995c 0 3.2%, #d3b267 3.4% 4.7%, transparent 5%),
        radial-gradient(ellipse at 60% 40%, #72ad64 0 3.6%, #d4b86c 3.8% 5%, transparent 5.3%),
        radial-gradient(ellipse at 77% 57%, #42925b 0 4%, #d7b96d 4.2% 5.5%, transparent 5.8%),
        radial-gradient(ellipse at 92% 23%, #6f8753 0 4%, #c7a963 4.2% 5.6%, transparent 5.9%),
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
    padding: 1rem 1.2rem;
    border-radius: 18px;
    background: rgba(4,35,49,.78);
    border: 1px solid rgba(255,222,145,.27);
}

.fighter-row {
    display: grid;
    grid-template-columns: 115px 1fr 48px;
    gap: .5rem;
    align-items: center;
    margin: .35rem 0;
    font: 700 .75rem/1 "Inter", sans-serif;
}
.hp-track { height: 9px; border-radius: 10px; background: #183745; overflow: hidden; }
.hp-fill { height: 100%; border-radius: 10px; background: linear-gradient(90deg, #df4a3e, #f5c04d, #55bd7a); }

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
        "reserves": {},
        "stage_index": 0,
        "battle": None,
        "berries": 0,
        "wins": 0,
        "last_recruitment": None,
        "last_battle_result": None,
        "campaign_defeated": False,
        "game_seed": random.randint(1, 999_999),
        "draft_team": {},
        "crew_rerolls": 0,
        "imu_event_active": False,
        "campaign_destroyed": False,
        "destroyed_location_index": None,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value
    if isinstance(st.session_state.reserves, list):
        migrated = {}
        for name in st.session_state.reserves:
            for role in CHARACTER_BY_NAME[name]["roles"]:
                if role not in migrated:
                    migrated[role] = name
                    break
        st.session_state.reserves = migrated
    if "crew_options" in st.session_state:
        del st.session_state.crew_options


def reset_campaign() -> None:
    st.session_state.crew = {}
    st.session_state.reserves = {}
    st.session_state.stage_index = 0
    st.session_state.battle = None
    st.session_state.berries = 0
    st.session_state.wins = 0
    st.session_state.last_recruitment = None
    st.session_state.last_battle_result = None
    st.session_state.campaign_defeated = False
    st.session_state.game_seed = random.randint(1, 999_999)
    st.session_state.draft_team = {}
    st.session_state.crew_rerolls = 0
    st.session_state.imu_event_active = False
    st.session_state.campaign_destroyed = False
    st.session_state.destroyed_location_index = None


def crew_names() -> set[str]:
    return {item["name"] for item in st.session_state.crew.values()}


def crew_card(role: str, character: dict) -> str:
    icon = ROLES[role]["icon"]
    initials = "".join(part[0] for part in character["name"].split())[:2]
    role_value = character["skills"][role]
    return f"""
    <div class="crew-card">
        <div class="avatar">{html.escape(initials)}</div>
        <div class="role-label">{icon} {html.escape(role)}</div>
        <div class="crew-name">{html.escape(character["name"])}</div>
        <span class="rank">R{html.escape(character["rank"])}</span>
        <div class="stat-line">
            <span class="stat-chip">⚔ ATQ {character["attack"]}</span>
            <span class="stat-chip">🛡 DEF {character["defense"]}</span>
            <span class="stat-chip">◆ FUNÇÃO {role_value}</span>
        </div>
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
        node_html.append(
            f"""
            <div class="map-node {status}" style="left:{location['x']}%;top:{location['y']}%;"></div>
            <div class="map-label" style="left:{location['x']}%;top:{location['y']}%;">
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


def finish_victory() -> None:
    battle = st.session_state.battle
    stage = battle["stage"]
    existing = crew_names() | set(st.session_state.reserves.values())
    result = recruitment_roll(
        battle,
        existing,
        set(st.session_state.reserves),
    )
    st.session_state.last_recruitment = result
    if result.get("success"):
        st.session_state.reserves[result["reserve_role"]] = result["candidate"]
    st.session_state.berries += stage["reward"]
    st.session_state.wins += 1
    st.session_state.stage_index += 1
    st.session_state.battle = None


def resolve_battle(stage: dict) -> None:
    battle = start_battle(st.session_state.crew, stage)
    st.session_state.battle = battle
    progress = st.progress(0, text="Confronto em andamento")

    for round_index in range(30):
        play_round(battle)
        progress.progress(
            min(95, 12 + (round_index + 1) * 8),
            text="Confronto em andamento",
        )
        time.sleep(0.16)
        if battle["status"] != "active":
            break

    if battle["status"] == "victory":
        rounds = battle["round"]
        stage_name = battle["stage"]["name"]
        finish_victory()
        st.session_state.last_battle_result = {
            "status": "victory",
            "message": f"Vitória em {stage_name} após {rounds} rodadas.",
        }
        progress.progress(100, text="Vitória")
    else:
        st.session_state.last_battle_result = {
            "status": "defeat",
            "message": f"A tripulação foi derrotada em {stage['name']}.",
        }
        st.session_state.campaign_defeated = True
        st.session_state.battle = None
        progress.progress(100, text="Derrota")

    time.sleep(0.45)


initialize_state()

if st.session_state.imu_event_active:
    render_imu_event()

st.html(
    """
    <div class="hero">
        <div class="hero-kicker">Saga East Blue</div>
        <div class="hero-title">Rota dos Mares</div>
        <div class="hero-copy">
            Forme sua tripulação, vença os conflitos do East Blue e abra caminho
            até a Reverse Mountain.
        </div>
    </div>
    """
)

top1, top2, top3, top4 = st.columns(4)
top1.metric("Vitórias", st.session_state.wins)
top2.metric("Berries", f"{st.session_state.berries:,}".replace(",", "."))
top3.metric("Progresso", f"{st.session_state.stage_index}/5")
top4.metric("Reservas", len(st.session_state.reserves))

journey_tab, crew_tab, ranking_tab, rules_tab = st.tabs(
    ["🗺️ Jornada", "🏴‍☠️ Tripulação", "📊 Ranking", "📜 Funções"]
)

with journey_tab:
    render_map()
    st.write("")

    if st.session_state.stage_index >= len(STAGES):
        st.success(
            "A tripulação alcançou a Reverse Mountain. A Grand Line está à frente."
        )
    elif st.session_state.campaign_destroyed:
        st.error(
            "Esse lugar nunca existiu. A ilha e sua tripulação foram apagadas."
        )
        if st.button("🔁 Reiniciar campanha", type="primary"):
            reset_campaign()
            st.rerun()
    elif st.session_state.campaign_defeated:
        result = st.session_state.last_battle_result
        st.error(
            result["message"]
            if result
            else "A tripulação foi derrotada."
        )
        if st.button("🔁 Iniciar nova campanha", type="primary"):
            reset_campaign()
            st.rerun()
    elif len(st.session_state.crew) < len(ROLES):
        st.warning(
            "A tripulação precisa ocupar as seis funções antes de partir."
        )
    else:
        stage = STAGES[st.session_state.stage_index]
        col_info, col_action = st.columns([0.72, 0.28])
        with col_info:
            st.subheader(stage["name"])
            st.write(stage["description"])
            st.caption(
                f"Chefe: {stage['boss']} • Recompensa: "
                f"{stage['reward']:,} berries".replace(",", ".")
            )
        with col_action:
            st.write("")
            if st.button("⚔️ Iniciar batalha", type="primary", width="stretch"):
                st.session_state.last_battle_result = None
                st.session_state.last_recruitment = None
                if triggers_imu_event():
                    st.session_state.imu_event_active = True
                    st.session_state.destroyed_location_index = stage[
                        "location_index"
                    ]
                else:
                    resolve_battle(stage)
                st.rerun()
        if st.session_state.last_battle_result:
            result = st.session_state.last_battle_result
            if result["status"] == "victory":
                st.success(result["message"])
        if st.session_state.last_recruitment:
            result = st.session_state.last_recruitment
            if result.get("success"):
                st.success(result["message"])
            else:
                st.info(result["message"])

with crew_tab:
    action1, action2, action3 = st.columns([0.34, 0.33, 0.33])
    with action1:
        has_candidate = bool(st.session_state.draft_team)
        crew_complete = len(st.session_state.crew) == len(ROLES)
        rerolls_left = 3 - st.session_state.crew_rerolls
        draft_label = (
            f"🎲 Resortear equipe ({rerolls_left} restantes)"
            if has_candidate
            else "🎲 Sortear equipe candidata"
        )
        if st.button(
            draft_label,
            type="primary",
            width="stretch",
            disabled=(
                st.session_state.stage_index > 0
                or crew_complete
                or (has_candidate and rerolls_left <= 0)
            ),
            help=(
                "Apresenta um candidato para cada função disponível."
            ),
        ):
            if has_candidate:
                st.session_state.crew_rerolls += 1
            st.session_state.draft_team = draft_candidate_team(
                st.session_state.crew
            )
            st.session_state.battle = None
            st.session_state.last_recruitment = None
            st.rerun()
    with action2:
        if st.button(
            "🔁 Reiniciar campanha",
            width="stretch",
            help="Recomeça a jornada desde a formação da tripulação.",
        ):
            reset_campaign()
            st.rerun()
    with action3:
        st.metric(
            "Composição da equipe",
            f"{len(st.session_state.crew)}/{len(ROLES)}",
        )

    if st.session_state.draft_team and not crew_complete:
        st.subheader("Defina a próxima função")
        st.caption(
            "Escolha um integrante. Os demais cargos serão renovados na próxima seleção."
        )
        open_roles = list(st.session_state.draft_team)
        option_columns = st.columns(min(3, len(open_roles)))
        for option_index, role in enumerate(open_roles):
            character = st.session_state.draft_team[role]
            column = option_columns[option_index % len(option_columns)]
            with column:
                st.markdown(f"#### {ROLES[role]['icon']} {role}")
                st.write(f"**{character['name']}** · R{character['rank']}")
                st.caption(
                    f"ATQ {character['attack']} · DEF {character['defense']} · "
                    f"Função {character['skills'][role]} · {character['faction']}"
                )
                if st.button(
                    f"Escolher {character['name']} como {role}",
                    key=f"choose_role_{role}",
                    type="primary",
                    width="stretch",
                ):
                    st.session_state.crew[role] = character
                    if len(st.session_state.crew) < len(ROLES):
                        st.session_state.draft_team = draft_candidate_team(
                            st.session_state.crew
                        )
                    else:
                        st.session_state.draft_team = {}
                    st.session_state.battle = None
                    st.session_state.last_recruitment = None
                    st.rerun()
        st.caption(f"Novas formações: {st.session_state.crew_rerolls}/3")

    render_crew_grid()

    if st.session_state.crew:
        summary = team_summary(st.session_state.crew)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ataque base", int(summary["attack"]))
        m2.metric("Defesa base", int(summary["defense"]))
        m3.metric("Reservas", len(st.session_state.reserves))
        m4.metric("Bônus tático", f"+{summary['tactical_modifier']:.1%}")

    st.subheader("Reservas")
    if not st.session_state.reserves:
        st.caption("Nenhum personagem disponível na reserva.")
    else:
        reserve_role = st.selectbox(
            "Vaga da reserva",
            list(st.session_state.reserves),
            format_func=lambda role: (
                f"{role}: {st.session_state.reserves[role]}"
            ),
        )
        reserve_name = st.session_state.reserves[reserve_role]
        st.caption(
            f"{reserve_name} está disponível para a função {reserve_role}."
        )
        if st.button("Incluir na tripulação"):
            old_crew = st.session_state.crew
            updated, removed = replace_with_reserve(
                old_crew,
                reserve_name,
                reserve_role,
            )
            st.session_state.crew = updated
            if removed:
                st.session_state.reserves[reserve_role] = removed
            else:
                st.session_state.reserves.pop(reserve_role)
            st.session_state.battle = None
            st.rerun()

with ranking_tab:
    rows = []
    for item in CHARACTERS:
        rows.append(
            {
                "Ranking": item["rank"],
                "Personagem": item["name"],
                "Ataque": item["attack"],
                "Defesa": item["defense"],
                "Funções": " / ".join(item["roles"]),
                "Facção": item["faction"],
                "_ordem": RANK_ORDER[item["rank"]],
                "_geral": item["attack"] + item["defense"],
            }
        )
    ranking_df = pd.DataFrame(rows).sort_values(
        ["_ordem", "_geral", "Ataque"],
        ascending=[False, False, False],
    )
    st.dataframe(
        ranking_df.drop(columns=["_ordem", "_geral"]),
        width="stretch",
        hide_index=True,
        column_config={
            "Ataque": st.column_config.ProgressColumn(
                "Ataque",
                min_value=0,
                max_value=10,
                format="%d",
            ),
            "Defesa": st.column_config.ProgressColumn(
                "Defesa",
                min_value=0,
                max_value=10,
                format="%d",
            ),
        },
    )
    st.caption(
        "S: excepcional • A: elite • B: especialista • C: apoio • D: iniciante"
    )

    selected_name = st.selectbox(
        "Ver ficha detalhada",
        [item["name"] for item in CHARACTERS],
    )
    selected = CHARACTER_BY_NAME[selected_name]
    detail_cols = st.columns(len(selected["roles"]))
    for index, role in enumerate(selected["roles"]):
        detail_cols[index].metric(
            role,
            selected["skills"][role],
            help=ROLES[role]["description"],
        )

with rules_tab:
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
    st.html(f'<div class="crew-grid">{"".join(cards)}</div>')
    st.info(
        "A aptidão para uma função é avaliada separadamente dos atributos de ataque e defesa."
    )
