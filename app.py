from __future__ import annotations

import html
import random

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
    draft_crew,
    play_round,
    recruitment_roll,
    replace_with_reserve,
    reroll_role,
    start_battle,
    team_summary,
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
    transform: translate(-50%, -65%);
    font-size: 2.65rem;
    z-index: 4;
    filter: drop-shadow(0 5px 3px rgba(0,0,0,.35));
    animation: bob 2s ease-in-out infinite;
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
        "reserves": [],
        "stage_index": 0,
        "battle": None,
        "berries": 0,
        "wins": 0,
        "last_recruitment": None,
        "game_seed": random.randint(1, 999_999),
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_campaign() -> None:
    st.session_state.crew = {}
    st.session_state.reserves = []
    st.session_state.stage_index = 0
    st.session_state.battle = None
    st.session_state.berries = 0
    st.session_state.wins = 0
    st.session_state.last_recruitment = None
    st.session_state.game_seed = random.randint(1, 999_999)


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
        st.info("A tripulação ainda não foi sorteada.")
        return
    cards = "".join(
        crew_card(role, st.session_state.crew[role])
        for role in ROLES
    )
    st.html(f'<div class="crew-grid">{cards}</div>')


def render_map() -> None:
    current = st.session_state.stage_index
    points = " ".join(f"{item['x']},{item['y']}" for item in LOCATIONS)
    node_html = []
    for index, location in enumerate(LOCATIONS):
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
    ship_location = LOCATIONS[min(current, len(LOCATIONS) - 1)]
    st.html(
        f"""
        <div class="sea-map">
            <svg class="route-svg" viewBox="0 0 100 100" preserveAspectRatio="none">
                <polyline class="route-path" points="{points}" />
            </svg>
            {''.join(node_html)}
            <div class="ship" style="left:{ship_location['x']}%;top:{ship_location['y']}%;">⛵</div>
        </div>
        """
    )


def fighter_rows(fighters: list[dict]) -> str:
    rows = []
    for fighter in fighters:
        percent = 0 if fighter["max_hp"] == 0 else fighter["hp"] / fighter["max_hp"] * 100
        state = "☠" if not fighter["alive"] else f"{fighter['hp']}"
        rows.append(
            f"""
            <div class="fighter-row">
                <span>{html.escape(fighter['name'])}</span>
                <div class="hp-track"><div class="hp-fill" style="width:{percent:.1f}%"></div></div>
                <span>{state}</span>
            </div>
            """
        )
    return "".join(rows)


def finish_victory() -> None:
    battle = st.session_state.battle
    stage = battle["stage"]
    existing = crew_names() | set(st.session_state.reserves)
    result = recruitment_roll(battle, existing)
    st.session_state.last_recruitment = result
    if result.get("success"):
        st.session_state.reserves.append(result["candidate"])
    st.session_state.berries += stage["reward"]
    st.session_state.wins += 1
    st.session_state.stage_index += 1
    st.session_state.battle = None


def render_battle() -> None:
    battle = st.session_state.battle
    if battle is None:
        return

    left, right = st.columns(2)
    with left:
        st.markdown("#### Sua tripulação")
        st.html(f'<div class="battle-panel">{fighter_rows(battle["player"])}</div>')
    with right:
        st.markdown(f"#### Inimigos — {battle['stage']['name']}")
        st.html(f'<div class="battle-panel">{fighter_rows(battle["enemies"])}</div>')

    controls, history = st.columns([0.35, 0.65])
    with controls:
        st.metric("Rodada", battle["round"])
        if battle["status"] == "active":
            if st.button("⚔️ Resolver próxima rodada", type="primary", width="stretch"):
                st.session_state.battle = play_round(battle)
                st.rerun()
        elif battle["status"] == "victory":
            st.success("Vitória confirmada.")
            if st.button("⛵ Avançar no mapa", type="primary", width="stretch"):
                finish_victory()
                st.rerun()
        else:
            st.error("A tripulação perdeu esta tentativa.")
            if st.button("🔄 Preparar nova tentativa", width="stretch"):
                st.session_state.battle = start_battle(
                    st.session_state.crew,
                    STAGES[st.session_state.stage_index],
                )
                st.rerun()
    with history:
        st.markdown("#### Diário da batalha")
        st.code("\n".join(battle["log"][-16:]), language=None)


initialize_state()

st.html(
    """
    <div class="hero">
        <div class="hero-kicker">Protótipo jogável • Saga East Blue</div>
        <div class="hero-title">Rota dos Mares</div>
        <div class="hero-copy">
            Sorteie uma tripulação com seis funções, atravesse cinco conflitos do
            East Blue e alcance a Reverse Mountain. As forças desta demo usam a
            escala inicial de 1 a 10; sagas futuras poderão ultrapassar esse teto.
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
            "Demo concluída: sua tripulação alcançou a Reverse Mountain e está pronta para a Grand Line."
        )
        st.balloons()
    elif not st.session_state.crew:
        st.warning("Forme a tripulação na aba Tripulação antes de partir.")
    elif st.session_state.battle is None:
        stage = STAGES[st.session_state.stage_index]
        col_info, col_action = st.columns([0.72, 0.28])
        with col_info:
            st.subheader(f"Próximo desafio: {stage['name']}")
            st.write(stage["description"])
            st.caption(
                f"Chefe: {stage['boss']} • Recompensa: "
                f"{stage['reward']:,} berries".replace(",", ".")
            )
        with col_action:
            st.write("")
            if st.button("⚔️ Iniciar batalha", type="primary", width="stretch"):
                st.session_state.battle = start_battle(st.session_state.crew, stage)
                st.rerun()
        if st.session_state.last_recruitment:
            result = st.session_state.last_recruitment
            if result.get("success"):
                st.success(result["message"])
            else:
                st.info(result["message"])
    else:
        render_battle()

with crew_tab:
    action1, action2, action3 = st.columns([0.34, 0.33, 0.33])
    with action1:
        if st.button("🎲 Sortear tripulação completa", type="primary", width="stretch"):
            st.session_state.crew = draft_crew()
            st.session_state.battle = None
            st.session_state.last_recruitment = None
            st.rerun()
    with action2:
        if st.button(
            "🔁 Reiniciar campanha",
            width="stretch",
            help="Apaga tripulação, progresso, berries e reservas desta sessão.",
        ):
            reset_campaign()
            st.rerun()
    with action3:
        if st.session_state.crew:
            summary = team_summary(st.session_state.crew)
            st.metric("Poder estimado", f"{summary['power']:.1f}")

    render_crew_grid()

    if st.session_state.crew:
        st.subheader("Rerrolagem por função")
        cols = st.columns(3)
        for index, role in enumerate(ROLES):
            character_name = st.session_state.crew[role]["name"]
            with cols[index % 3]:
                if st.button(
                    f"{ROLES[role]['icon']} {role}: {character_name}",
                    key=f"reroll_{role}",
                    width="stretch",
                    help=f"Sortear novamente apenas a função {role}.",
                ):
                    st.session_state.crew = reroll_role(st.session_state.crew, role)
                    st.session_state.battle = None
                    st.rerun()

        summary = team_summary(st.session_state.crew)
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Ataque base", int(summary["attack"]))
        m2.metric("Defesa base", int(summary["defense"]))
        m3.metric("Bônus do líder", f"{summary['leader_bonus']:+.1%}")
        m4.metric("Modificador tático", f"{summary['tactical_modifier']:+.1%}")

    st.subheader("Reserva recrutada")
    if not st.session_state.reserves:
        st.caption("Inimigos recrutados após vitórias aparecerão aqui.")
    else:
        reserve_name = st.selectbox("Personagem da reserva", st.session_state.reserves)
        eligible_roles = CHARACTER_BY_NAME[reserve_name]["roles"]
        target_role = st.selectbox("Função que ele assumirá", eligible_roles)
        if st.button("Escalar personagem da reserva"):
            old_crew = st.session_state.crew
            updated, removed = replace_with_reserve(old_crew, reserve_name, target_role)
            st.session_state.crew = updated
            st.session_state.reserves.remove(reserve_name)
            if removed not in st.session_state.reserves:
                st.session_state.reserves.append(removed)
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
        "S = excepcional no East Blue; A = elite; B = forte/especialista; "
        "C = apoio limitado; D = iniciante."
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
        "A classificação funcional é independente de ataque e defesa. "
        "Nami, por exemplo, tem combate direto baixo, mas nota tática máxima no East Blue."
    )
