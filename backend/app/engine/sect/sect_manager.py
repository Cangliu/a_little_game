"""Sect Manager — core class for the independent sect strategy system.

Handles all sect-related game logic:
- World initialization (generate sects + relations at game start)
- Player membership (join/leave/contribute/promote)
- Sect events (daily missions, grand tournaments, crises)
- World evolution (inter-sect relations shift over time)
"""
from __future__ import annotations

import logging
import random
import uuid
from typing import Optional, TYPE_CHECKING

from .models import (
    SectRank, SectRelationType, SectMembership,
    RANK_ORDER, RANK_PROMOTION_REQS,
)
from .sect_templates import generate_world_sects, generate_initial_relations

if TYPE_CHECKING:
    from ...models import GameState

logger = logging.getLogger(__name__)


class SectManager:
    """Manages the sect world and player's sect interactions."""

    # ── World Initialization ──────────────────────────────────────────

    def initialize_world(self, state: "GameState") -> None:
        """Generate world sects and relations at game start.

        Called once during start_game. Populates state.sect_world.
        """
        sects = generate_world_sects(num_sects=7)
        relations = generate_initial_relations(sects)

        state.sect_world = {
            "sects": {s["sect_id"]: s for s in sects},
            "relations": relations,
        }
        logger.info("Sect world initialized: %d sects, %d relations",
                    len(sects), len(relations))

    # ── Getters ───────────────────────────────────────────────────────

    def get_sect(self, state: "GameState", sect_id: str) -> Optional[dict]:
        """Get a sect dict by ID."""
        return state.sect_world.get("sects", {}).get(sect_id)

    def get_player_sect(self, state: "GameState") -> Optional[dict]:
        """Get the player's current sect, or None if散修."""
        membership = state.sect_membership
        if not membership:
            return None
        sect_id = membership.get("sect_id") if isinstance(membership, dict) else membership.sect_id
        return self.get_sect(state, sect_id)

    def get_player_membership(self, state: "GameState") -> Optional[dict]:
        """Get the player's SectMembership dict."""
        return state.sect_membership

    def get_all_sects(self, state: "GameState") -> list[dict]:
        """Get list of all non-destroyed sects."""
        sects = state.sect_world.get("sects", {})
        return [s for s in sects.values() if not s.get("is_destroyed")]

    # ── Player Membership ─────────────────────────────────────────────

    def join_sect(self, state: "GameState", sect_id: str) -> dict:
        """Player joins a sect as outer disciple.

        Returns an event dict describing the joining.
        """
        sect = self.get_sect(state, sect_id)
        if not sect:
            return {}
        if state.sect_membership:
            return {}  # Already in a sect

        membership = SectMembership(
            sect_id=sect_id,
            rank=SectRank.OUTER_DISCIPLE.value,
            contribution=0,
            reputation_in_sect=50,
            join_age=state.age,
            missions_completed=0,
            last_mission_age=0,
        )
        state.sect_membership = membership.model_dump()

        return {
            "id": f"sect_join_{uuid.uuid4().hex[:6]}",
            "text": f"你拜入{sect['name']}，成为一名外门弟子。",
            "expanded_text": f"经过一番考验，{sect['name']}终于向你敞开了大门。"
                             f"师兄引你入山，沿途灵气浮动，你深知修行之路从此不再孤独。",
            "event_type": "important",
            "category": "sect",
            "effects": {"cultivation": 10, "fortune": 1},
            "tags": ["sect_joined"],
        }

    def leave_sect(self, state: "GameState", reason: str = "主动退出") -> dict:
        """Player leaves their current sect.

        Returns an event dict describing the departure.
        Reasons: 主动退出, 叛门, 逐出师门, 宗门覆灭
        """
        sect = self.get_player_sect(state)
        if not sect:
            return {}

        sect_name = sect["name"]
        state.sect_membership = None

        event = {
            "id": f"sect_leave_{uuid.uuid4().hex[:6]}",
            "text": f"你离开了{sect_name}，重归散修之身。",
            "expanded_text": f"你与{sect_name}的缘分至此告一段落。"
                             f"背负行囊走下山门的那一刻，既有不舍，也有对未知的期待。",
            "event_type": "important",
            "category": "sect",
            "effects": {},
            "tags": ["sect_left"],
        }

        if reason == "叛门":
            event["text"] = f"你背叛了{sect_name}，遁入茫茫天地。"
            event["expanded_text"] = (f"你的叛离惊动了{sect_name}上下，追杀令已下。"
                                      f"从此江湖路远，步步惊心。")
            event["effects"] = {"fortune": -2}
            event["tags"].append("sect_betrayal")
        elif reason == "逐出师门":
            event["text"] = f"你被{sect_name}逐出山门，从此与师门恩断义绝。"
            event["expanded_text"] = (f"长老会当众宣布将你逐出{sect_name}。"
                                      f"昔日同门冷眼旁观，你咬牙一步步走下山阶。"
                                      f"身后是紧闭的山门，身前是未知的茫茫天地。")
            event["effects"] = {"willpower": 1, "fortune": -1}
            event["tags"].append("sect_expelled")
        elif reason == "宗门覆灭":
            event["text"] = f"{sect_name}山门破碎，你在火海中逃出，从此流落天涯。"
            event["expanded_text"] = (f"{sect_name}的护山大阵轰然崩碎，灵火焚尽了百年基业。"
                                      f"你在断壁残垣中挣扎逃出，身后是冲天的火光与同门的惨呼。"
                                      f"从此天地之大，再无归处。")
            event["effects"] = {"willpower": 2, "fortune": -2}
            event["tags"].append("sect_destroyed")

        return event

    def contribute(self, state: "GameState", amount: int) -> None:
        """Add contribution to the player's sect membership."""
        if not state.sect_membership:
            return
        mem = state.sect_membership
        mem["contribution"] = mem.get("contribution", 0) + amount

    def check_rank_promotion(self, state: "GameState") -> Optional[dict]:
        """Check if player qualifies for rank promotion.

        Returns event dict if promoted, None otherwise.
        Cooldown: at least 30 years between promotions.
        """
        if not state.sect_membership:
            return None

        mem = state.sect_membership
        current_rank = mem.get("rank", SectRank.OUTER_DISCIPLE.value)
        contribution = mem.get("contribution", 0)
        reputation = mem.get("reputation_in_sect", 50)

        # Cooldown: prevent rapid consecutive promotions (min 30 years apart)
        last_promotion_age = mem.get("last_promotion_age", 0)
        if state.age - last_promotion_age < 30:
            return None

        # Find current rank index
        current_idx = 0
        for i, r in enumerate(RANK_ORDER):
            if r.value == current_rank:
                current_idx = i
                break

        # Check if next rank is achievable
        if current_idx >= len(RANK_ORDER) - 1:
            return None  # Already sect master

        next_rank = RANK_ORDER[current_idx + 1]
        req = RANK_PROMOTION_REQS.get(next_rank)
        if not req:
            return None

        min_contribution, min_reputation, min_realm = req
        if (contribution >= min_contribution
                and reputation >= min_reputation
                and state.realm >= min_realm):
            # Promote!
            mem["rank"] = next_rank.value
            mem["last_promotion_age"] = state.age  # Record promotion time for cooldown

            sect = self.get_player_sect(state)
            sect_name = sect["name"] if sect else "宗门"

            return {
                "id": f"sect_promote_{uuid.uuid4().hex[:6]}",
                "text": f"你在{sect_name}中晋升为{next_rank.value}！",
                "expanded_text": f"多年来的付出终于得到认可。{sect_name}掌门亲自宣布，"
                                 f"你自今日起晋升为{next_rank.value}，门中弟子纷纷道贺。",
                "event_type": "fortune",
                "category": "sect",
                "effects": {"charisma": 1, "cultivation": 20},
                "tags": ["sect_promotion", f"rank_{next_rank.name.lower()}"],
            }

        return None

    # ── Sect Events (per turn) ────────────────────────────────────────

    def check_sect_events(self, state: "GameState") -> list[dict]:
        """Generate sect-related events for this turn.

        Called each turn (Phase 6.8). Returns list of events.
        """
        events = []
        if not state.sect_membership:
            return events

        mem = state.sect_membership
        sect = self.get_player_sect(state)
        if not sect:
            return events

        sect_name = sect["name"]
        rank = mem.get("rank", SectRank.OUTER_DISCIPLE.value)
        last_mission = mem.get("last_mission_age", 0)

        # Mission opportunity (every 5+ years if not recent)
        if state.age - last_mission >= 5 and random.random() < 0.35:
            mission_event = self._generate_mission(state, sect_name, rank)
            if mission_event:
                events.append(mission_event)

        # Sect resource distribution (passive cultivation bonus)
        # Cooldown: at least 5 years between distributions
        last_resource_age = mem.get("last_resource_age", 0)
        if state.age - last_resource_age >= 5 and random.random() < 0.25:
            bonus = self._get_resource_bonus(sect, rank)
            if bonus > 0:
                mem["last_resource_age"] = state.age
                events.append({
                    "id": f"sect_resource_{uuid.uuid4().hex[:6]}",
                    "text": f"{sect_name}按例发放修炼资源，你得到了灵石与丹药。",
                    "event_type": "normal",
                    "category": "sect",
                    "effects": {"cultivation": bonus},
                })

        # Sparring with fellow disciples (social + cultivation)
        if random.random() < 0.15:
            events.append({
                "id": f"sect_spar_{uuid.uuid4().hex[:6]}",
                "text": f"你与{sect_name}同门切磋，颇有所得。",
                "event_type": "normal",
                "category": "sect",
                "effects": {"cultivation": 5, "constitution": 1},
            })

        return events

    def _generate_mission(self, state: "GameState", sect_name: str, rank: str) -> Optional[dict]:
        """Generate a sect mission event based on rank."""
        mem = state.sect_membership
        missions = {
            SectRank.OUTER_DISCIPLE.value: [
                ("采药", "上山采集灵药", {"cultivation": 5}),
                ("巡山", "巡视山门", {"constitution": 1}),
                ("护送", "护送物资下山", {"fortune": 1}),
            ],
            SectRank.INNER_DISCIPLE.value: [
                ("斩妖", "下山除妖", {"cultivation": 15, "constitution": 1}),
                ("护矿", "守护灵矿", {"cultivation": 10}),
                ("传信", "代为传书", {"charisma": 1}),
            ],
            SectRank.CORE_DISCIPLE.value: [
                ("探秘", "探索前辈洞府", {"cultivation": 30, "comprehension": 1}),
                ("镇守", "镇守宗门禁地", {"willpower": 1, "cultivation": 20}),
                ("外交", "代表宗门出使", {"charisma": 2}),
            ],
            SectRank.ELDER.value: [
                ("传功", "指导弟子修行", {"comprehension": 1, "charisma": 1}),
                ("布阵", "维护宗门大阵", {"cultivation": 25}),
                ("征伐", "率队征伐敌对势力", {"constitution": 2, "cultivation": 30}),
            ],
        }

        rank_missions = missions.get(rank, missions[SectRank.OUTER_DISCIPLE.value])
        name, desc, effects = random.choice(rank_missions)

        # Complete mission
        mem["missions_completed"] = mem.get("missions_completed", 0) + 1
        mem["last_mission_age"] = state.age
        # Contribution reward
        contribution_reward = 10 + state.realm * 5
        mem["contribution"] = mem.get("contribution", 0) + contribution_reward
        # Reputation boost
        mem["reputation_in_sect"] = min(100, mem.get("reputation_in_sect", 50) + 3)

        return {
            "id": f"sect_mission_{uuid.uuid4().hex[:6]}",
            "text": f"{sect_name}派遣你{desc}，你圆满完成了任务。",
            "expanded_text": f"作为{rank}，你领命{desc}。一番波折后任务完成，"
                             f"贡献值增加了{contribution_reward}点。",
            "event_type": "normal",
            "category": "sect",
            "effects": effects,
            "tags": ["sect_mission"],
        }

    @staticmethod
    def _get_resource_bonus(sect: dict, rank: str) -> int:
        """Calculate resource cultivation bonus based on sect tier and player rank."""
        tier = sect.get("tier", 3)
        rank_multiplier = {
            SectRank.OUTER_DISCIPLE.value: 1,
            SectRank.INNER_DISCIPLE.value: 2,
            SectRank.CORE_DISCIPLE.value: 3,
            SectRank.ELDER.value: 4,
            SectRank.GRAND_ELDER.value: 5,
            SectRank.SECT_MASTER.value: 6,
        }
        mult = rank_multiplier.get(rank, 1)
        return tier * mult * 3

    # ── Sect World Evolution (per turn) ───────────────────────────────

    def advance_sect_world(self, state: "GameState") -> list[dict]:
        """Evolve inter-sect relations and sect power levels.

        Called each turn (Phase 6.9). Can generate world events.
        """
        events = []
        relations = state.sect_world.get("relations", [])
        sects = state.sect_world.get("sects", {})

        if not relations:
            return events

        # Randomly shift one relation per turn
        if random.random() < 0.2 and relations:
            rel = random.choice(relations)
            old_type = rel.get("relation_type", SectRelationType.NEUTRAL.value)
            tension = rel.get("tension", 50)

            # Tension drift with regression-to-mean bias
            # Extremes (hostile/ally) pull back toward neutral (50) slowly
            base_drift = random.randint(-10, 10)
            # Add a small nudge toward 50 (regression force)
            regression = (50 - tension) * 0.1  # e.g. tension=90 → -4, tension=10 → +4
            drift = int(base_drift + regression)
            tension = max(0, min(100, tension + drift))
            rel["tension"] = tension

            # Relation type change based on tension
            new_type = old_type
            if tension >= 85 and old_type != SectRelationType.HOSTILE.value:
                new_type = SectRelationType.HOSTILE.value
            elif tension <= 20 and old_type == SectRelationType.RIVAL.value:
                new_type = SectRelationType.NEUTRAL.value
            elif tension <= 10 and old_type == SectRelationType.NEUTRAL.value:
                new_type = SectRelationType.ALLY.value

            if new_type != old_type:
                rel["relation_type"] = new_type
                # Mark the turn this became hostile so invasion won't fire same turn
                if new_type == SectRelationType.HOSTILE.value:
                    rel["hostile_since_age"] = state.age
                sa = sects.get(rel["sect_a_id"], {})
                sb = sects.get(rel["sect_b_id"], {})
                if sa and sb:
                    events.append({
                        "id": f"sect_world_{uuid.uuid4().hex[:6]}",
                        "text": f"江湖传闻：{sa['name']}与{sb['name']}的关系变为{new_type}。",
                        "event_type": "normal",
                        "category": "sect_world",
                        "effects": {},
                    })

        # Sect resources grow each turn
        for sect in sects.values():
            if sect.get("is_destroyed"):
                continue
            resources = sect.get("resources", {})
            income = resources.get("monthly_income", 50)
            resources["spirit_stones"] = resources.get("spirit_stones", 500) + income

        return events

    # ── Major Sect Events (Crises) ────────────────────────────────────

    def check_sect_crisis(self, state: "GameState") -> Optional[dict]:
        """Check for major sect crises (low probability, high impact).

        Events: sect tournament, invasion, sect master death, merger.
        Returns at most one crisis event per turn.
        """
        if not state.sect_membership:
            return None

        sect = self.get_player_sect(state)
        if not sect:
            return None

        sect_name = sect["name"]
        mem = state.sect_membership

        # Grand tournament (every ~30 years, realm >= 1)
        if state.realm >= 1 and random.random() < 0.03:
            return self._sect_tournament(state, sect_name, mem)

        # Invasion by hostile sect (requires hostile relation)
        if random.random() < 0.02:
            hostile = self._find_hostile_sect(state, sect["sect_id"])
            if hostile:
                return self._sect_invasion(state, sect_name, hostile, mem)

        # Sect master change (very rare)
        if random.random() < 0.008:
            return self._sect_master_change(state, sect, mem)

        return None

    def _sect_tournament(self, state: "GameState", sect_name: str, mem: dict) -> dict:
        """Generate a sect grand tournament event."""
        rank = mem.get("rank", SectRank.OUTER_DISCIPLE.value)
        # Performance based on realm + constitution + willpower
        attrs = state.attributes
        score = state.realm * 20 + attrs.constitution * 3 + attrs.willpower * 2
        score += random.randint(-10, 10)

        if score >= 60:
            result = "名列前茅"
            effects = {"cultivation": 30, "charisma": 2}
            mem["reputation_in_sect"] = min(100, mem.get("reputation_in_sect", 50) + 10)
            mem["contribution"] = mem.get("contribution", 0) + 50
        elif score >= 30:
            result = "表现中等"
            effects = {"cultivation": 10}
            mem["reputation_in_sect"] = min(100, mem.get("reputation_in_sect", 50) + 3)
        else:
            result = "惜败"
            effects = {"willpower": 1}

        return {
            "id": f"sect_tournament_{uuid.uuid4().hex[:6]}",
            "text": f"{sect_name}举办宗门大比，你{result}。",
            "expanded_text": f"一年一度的宗门大比拉开帷幕。各路弟子齐聚比武台，"
                             f"你作为{rank}参赛，经过数轮激战，最终{result}。",
            "event_type": "important",
            "category": "sect",
            "effects": effects,
            "tags": ["sect_tournament"],
        }

    def _find_hostile_sect(self, state: "GameState", player_sect_id: str) -> Optional[dict]:
        """Find a hostile sect targeting the player's sect.
        
        Excludes relations that became hostile this same turn (prevents immediate invasion).
        """
        relations = state.sect_world.get("relations", [])
        sects = state.sect_world.get("sects", {})

        for rel in relations:
            if rel.get("relation_type") != SectRelationType.HOSTILE.value:
                continue
            # Skip if just became hostile this turn
            if rel.get("hostile_since_age", 0) == state.age:
                continue
            if rel["sect_a_id"] == player_sect_id:
                enemy = sects.get(rel["sect_b_id"])
            elif rel["sect_b_id"] == player_sect_id:
                enemy = sects.get(rel["sect_a_id"])
            else:
                continue
            if enemy and not enemy.get("is_destroyed"):
                return enemy

        return None

    def _sect_invasion(self, state: "GameState", sect_name: str,
                       hostile: dict, mem: dict) -> dict:
        """Generate a sect invasion event. May trigger sect destruction."""
        hostile_name = hostile["name"]
        rank = mem.get("rank", SectRank.OUTER_DISCIPLE.value)
        sect = self.get_player_sect(state)

        # Check if sect is too weak to survive: low resources + 30% chance
        sect_resources = sect.get("resources", {}).get("spirit_stones", 500) if sect else 500
        if sect_resources < 200 and random.random() < 0.30:
            return self._destroy_sect(state, sect, hostile_name)

        # Higher-rank players have bigger impact
        rank_idx = 0
        for i, r in enumerate(RANK_ORDER):
            if r.value == rank:
                rank_idx = i
                break

        if rank_idx >= 3:  # Elder or above
            text = f"{hostile_name}突袭{sect_name}！你身为{rank}，率众抵抗。"
            effects = {"constitution": -1, "willpower": 2, "cultivation": 20}
        else:
            text = f"{hostile_name}突袭{sect_name}！你在混战中奋力自保。"
            effects = {"constitution": -1, "cultivation": 5}

        mem["reputation_in_sect"] = min(100, mem.get("reputation_in_sect", 50) + 5)
        mem["contribution"] = mem.get("contribution", 0) + 30

        return {
            "id": f"sect_invasion_{uuid.uuid4().hex[:6]}",
            "text": text,
            "expanded_text": f"一个寻常的清晨，{hostile_name}的修士突破了山门护阵。"
                             f"一时间喊杀声四起，{sect_name}上下奋起迎敌。",
            "event_type": "danger",
            "category": "sect",
            "effects": effects,
            "tags": ["sect_invasion"],
        }

    def _destroy_sect(self, state: "GameState", sect: dict, hostile_name: str) -> dict:
        """Handle sect destruction — marks sect as destroyed and ejects player."""
        sect_name = sect["name"]
        sect["is_destroyed"] = True

        # Mark fellow disciples as dispersed/dead (宗门覆灭，同门流散)
        for rel_dict in state.relationships:
            if rel_dict.get("relation_type") != "同门":
                continue
            npc_id = rel_dict.get("npc_id", "")
            npc_dict = state.npc_registry.get(npc_id)
            if not npc_dict or not npc_dict.get("is_alive", True):
                continue
            # 50% chance dead in the destruction, 50% dispersed (alive but lost contact)
            if random.random() < 0.5:
                npc_dict["is_alive"] = False
                rel_dict["is_dead"] = True
            else:
                npc_dict["status"] = "dispersed"
                rel_dict["is_dispersed"] = True

        # Force player to leave
        leave_event = self.leave_sect(state, reason="宗门覆灭")

        return {
            "id": f"sect_destroy_{uuid.uuid4().hex[:6]}",
            "text": leave_event.get("text", f"{sect_name}被{hostile_name}攻灭！"),
            "expanded_text": (f"{hostile_name}倾巢而出，{sect_name}护山大阵不堪重负终于崩碎。"
                              f"掌门力战而亡，长老殒落大半。你在混乱中拼死突围，"
                              f"回首时只见冲天火光吞噬了你曾修行的一切。"
                              f"从此{sect_name}不复存在，你沦为无门散修。"),
            "event_type": "calamity",
            "category": "sect",
            "effects": {"willpower": 2, "fortune": -2, "constitution": -1},
            "tags": ["sect_destroyed", "sect_invasion"],
        }

    def _sect_master_change(self, state: "GameState", sect: dict, mem: dict) -> dict:
        """Generate a sect master change event."""
        sect_name = sect["name"]
        old_master = sect.get("sect_master_name", "前任掌门")

        # New master name
        from .sect_templates import _SECT_MASTER_NAMES
        new_master = random.choice([n for n in _SECT_MASTER_NAMES if n != old_master])
        sect["sect_master_name"] = new_master

        rank = mem.get("rank", SectRank.OUTER_DISCIPLE.value)

        # If player is grand elder, chance to become master
        if rank == SectRank.GRAND_ELDER.value and random.random() < 0.3:
            mem["rank"] = SectRank.SECT_MASTER.value
            return {
                "id": f"sect_master_change_{uuid.uuid4().hex[:6]}",
                "text": f"{sect_name}掌门{old_master}退隐，你被推举为新任掌门！",
                "expanded_text": f"{old_master}宣布闭关不出，长老会经过商议，"
                                 f"推举你为{sect_name}新一任掌门。从此宗门兴衰，系于你一身。",
                "event_type": "fortune",
                "category": "sect",
                "effects": {"charisma": 3, "willpower": 2},
                "tags": ["became_sect_master"],
            }

        return {
            "id": f"sect_master_change_{uuid.uuid4().hex[:6]}",
            "text": f"{sect_name}掌门{old_master}退隐，{new_master}接任掌门之位。",
            "expanded_text": f"一个时代结束了。{old_master}在一夜之间宣布退位，"
                             f"{new_master}在长老会的支持下执掌{sect_name}。宗门内暗流涌动。",
            "event_type": "important",
            "category": "sect",
            "effects": {},
            "tags": ["sect_master_changed"],
        }

    # ── Sect Political Intrigue (deeper narrative events) ──────────────

    def check_sect_politics(self, state: "GameState") -> Optional[dict]:
        """Generate sect political intrigue events (faction struggles, espionage, etc).

        Called each turn. Returns at most one political event.
        Low probability but high narrative impact for players at inner disciple+.
        """
        if not state.sect_membership:
            return None

        mem = state.sect_membership
        rank = mem.get("rank", SectRank.OUTER_DISCIPLE.value)
        sect = self.get_player_sect(state)
        if not sect:
            return None

        sect_name = sect["name"]

        # Only inner disciples and above get political events
        rank_idx = 0
        for i, r in enumerate(RANK_ORDER):
            if r.value == rank:
                rank_idx = i
                break
        if rank_idx < 1:  # Outer disciples don't see politics
            return None

        # Faction struggle (4% chance, inner disciple+)
        if rank_idx >= 1 and random.random() < 0.04:
            return self._faction_struggle(state, sect_name, rank, rank_idx)

        # Espionage / spy discovery (2.5% chance, core disciple+)
        if rank_idx >= 2 and random.random() < 0.025:
            return self._espionage_event(state, sect_name, rank)

        # Resource dispute with other sect (3% chance, elder+)
        if rank_idx >= 3 and random.random() < 0.03:
            return self._resource_war(state, sect, rank)

        # Internal power play (2% chance, grand elder+)
        if rank_idx >= 4 and random.random() < 0.02:
            return self._power_play(state, sect_name, mem)

        # Alliance negotiation (2% chance, elder+)
        if rank_idx >= 3 and random.random() < 0.02:
            return self._alliance_negotiation(state, sect)

        return None

    def _faction_struggle(self, state: "GameState", sect_name: str,
                          rank: str, rank_idx: int) -> dict:
        """Internal faction power struggle event."""
        factions = [
            ("丹道一脉", "剑修一脉"),
            ("长老派", "少壮派"),
            ("嫡传弟子", "外来弟子"),
            ("保守派", "改革派"),
            ("掌门亲传", "客卿势力"),
        ]
        fa, fb = random.choice(factions)

        # Higher rank = more agency
        if rank_idx >= 3:  # Elder+
            templates = [
                {
                    "text": f"{sect_name}内部{fa}与{fb}暗中角力，双方都在拉拢你。",
                    "expanded_text": f"近日{sect_name}内暗流涌动。{fa}的几位长老私下找到你，"
                                     f"言语间暗示若你支持他们，日后必有回报。"
                                     f"而{fb}的人也递来了橄榄枝。身处旋涡之中，你不得不谨慎抉择。",
                    "effects": {"charisma": 1},
                    "event_type": "important",
                },
                {
                    "text": f"你被卷入{sect_name}的派系之争，{fa}与{fb}矛盾激化。",
                    "expanded_text": f"一次长老会上，{fa}与{fb}因灵脉分配一事公然翻脸。"
                                     f"你作为{rank}，被迫表态。无论站哪边，都意味着得罪另一方。"
                                     f"这一晚你独坐洞府，权衡再三。",
                    "effects": {"willpower": 1},
                    "event_type": "important",
                },
            ]
        else:  # Inner/Core disciple
            templates = [
                {
                    "text": f"{sect_name}内{fa}与{fb}关系紧张，你受到了波及。",
                    "expanded_text": f"师兄悄悄告诉你，最近{fa}和{fb}斗得厉害。"
                                     f"有人向你示好，也有人给你使绊子。"
                                     f"你虽不想卷入纷争，但身在其中已由不得你。",
                    "effects": {"comprehension": 1},
                    "event_type": "normal",
                },
            ]

        event = random.choice(templates)
        event["id"] = f"sect_faction_{uuid.uuid4().hex[:6]}"
        event["category"] = "sect"
        event["tags"] = ["sect_politics", "faction_struggle"]
        mem = state.sect_membership
        # Low-rank players may suffer collateral damage (15% reputation loss)
        if rank_idx < 3 and random.random() < 0.15:
            mem["reputation_in_sect"] = max(0, mem.get("reputation_in_sect", 50) - 15)
            event["text"] += "你被卷入纷争，声望受损。"
            event["effects"] = {"fortune": -1}
        else:
            mem["reputation_in_sect"] = min(100, mem.get("reputation_in_sect", 50) + 2)
        return event

    def _espionage_event(self, state: "GameState", sect_name: str, rank: str) -> dict:
        """Spy/espionage discovery within the sect."""
        templates = [
            {
                "text": f"你发现{sect_name}中有人暗通外敌，将宗门秘密外泄。",
                "expanded_text": f"你无意中撞见一名同门深夜与外人接头。那人发现你后面色大变，"
                                 f"反咬一口说你才是奸细。一时间真假难辨，宗门上下人心惶惶。"
                                 f"你必须找到真相，否则自身难保。",
                "effects": {"comprehension": 1, "willpower": 1},
                "event_type": "danger",
            },
            {
                "text": f"掌门密令你暗中调查{sect_name}内的叛徒。",
                "expanded_text": f"掌门私下召见你，面色凝重：\'近日有人将宗门功法泄露给了外敌，"
                                 f"你且暗中查访。\' 你领命之后方觉此事棘手——"
                                 f"叛徒可能是你熟识之人，也可能早已察觉到了你。",
                "effects": {"fortune": 1, "charisma": 1},
                "event_type": "important",
            },
            {
                "text": f"一名外敌探子潜入{sect_name}被你识破。",
                "expanded_text": f"那人伪装得极好，若非你无意中察觉他灵力运行方式异于本门心法，"
                                 f"恐怕无人能识破。你当机立断将此人制住，"
                                 f"掌门闻讯大加赞赏，宗门上下对你刮目相看。",
                "effects": {"cultivation": 15, "charisma": 2},
                "event_type": "fortune",
            },
        ]
        event = random.choice(templates)
        event["id"] = f"sect_espionage_{uuid.uuid4().hex[:6]}"
        event["category"] = "sect"
        event["tags"] = ["sect_politics", "espionage"]
        mem = state.sect_membership
        # 20% chance of being falsely accused as spy → heavy reputation loss
        if random.random() < 0.20:
            mem["reputation_in_sect"] = max(0, mem.get("reputation_in_sect", 50) - 30)
            event["text"] = f"有人向掌门密报你是内奸，你百口莫辩。"
            event["expanded_text"] = (f"不知是谁向掌门告密，说你暗通外敌。"
                                      f"你被带到长老会前受审，虽然最终没有实证，"
                                      f"但嫌疑的种子已经种下，你在宗门中的处境变得艰难。")
            event["effects"] = {"fortune": -1, "willpower": 1}
        else:
            mem["contribution"] = mem.get("contribution", 0) + 25
        return event

    def _resource_war(self, state: "GameState", sect: dict, rank: str) -> dict:
        """Inter-sect resource dispute event."""
        sect_name = sect["name"]
        # Find a rival/hostile sect
        rival = self._find_rival_sect(state, sect["sect_id"])
        rival_name = rival["name"] if rival else "临近的散修联盟"

        templates = [
            {
                "text": f"{sect_name}与{rival_name}因灵脉归属爆发冲突，你奉命率队出征。",
                "expanded_text": f"那条灵脉位于两家地盘交界处，双方觊觎已久。"
                                 f"这一次{rival_name}率先动手抢占，{sect_name}怎能坐视？"
                                 f"你作为{rank}，率一队精锐弟子前往争夺。"
                                 f"一场恶战不可避免。",
                "effects": {"cultivation": 20, "constitution": 1},
                "event_type": "danger",
            },
            {
                "text": f"{sect_name}新发现一处秘境，与{rival_name}争夺入场名额。",
                "expanded_text": f"秘境入口每百年开启一次，名额有限。"
                                 f"{sect_name}与{rival_name}各不相让，最终决定各派精英比试，"
                                 f"胜者多占名额。你被选为代表之一，压力陡增。",
                "effects": {"willpower": 1, "cultivation": 15},
                "event_type": "important",
            },
        ]
        event = random.choice(templates)
        event["id"] = f"sect_resource_war_{uuid.uuid4().hex[:6]}"
        event["category"] = "sect"
        event["tags"] = ["sect_politics", "resource_war"]
        mem = state.sect_membership
        mem["contribution"] = mem.get("contribution", 0) + 40
        mem["reputation_in_sect"] = min(100, mem.get("reputation_in_sect", 50) + 5)
        return event

    def _power_play(self, state: "GameState", sect_name: str, mem: dict) -> dict:
        """High-level power play (grand elder+)."""
        templates = [
            {
                "text": f"有人暗中联络你，意图逼宫掌门，问你是否参与。",
                "expanded_text": f"深夜，一位长老秘密来访。他压低声音说出了一个惊天计划："
                                 f"现任掌门近年修为停滞，几位大长老密谋逼其退位。"
                                 f"你的态度将左右局势走向。这一夜，你辗转难眠。",
                "effects": {"willpower": 2},
                "event_type": "important",
            },
            {
                "text": f"掌门召集心腹密议{sect_name}百年大计，你位列其中。",
                "expanded_text": f"掌门在密室中摊开一卷地图，上面标注着数条灵脉和数个势力范围。"
                                 f"'百年之内，{sect_name}必须再进一步，否则就是退。'"
                                 f"作为掌门心腹之一，你被赋予了一项极其重要的任务。",
                "effects": {"charisma": 2, "cultivation": 25},
                "event_type": "fortune",
            },
            {
                "text": f"{sect_name}内部有人散布谣言中伤你，意图动摇你的地位。",
                "expanded_text": f"不知何时起，宗门内开始流传一些关于你的谣言——"
                                 f"有人说你暗通魔修，有人说你私吞了宗门资源。"
                                 f"虽是无中生有，但三人成虎，你必须尽快澄清。",
                "effects": {"charisma": -1, "willpower": 1},
                "event_type": "danger",
            },
        ]
        event = random.choice(templates)
        event["id"] = f"sect_power_play_{uuid.uuid4().hex[:6]}"
        event["category"] = "sect"
        event["tags"] = ["sect_politics", "power_play"]
        # 30% chance the power play backfires → reputation crash (may lead to expulsion)
        if random.random() < 0.30:
            mem["reputation_in_sect"] = max(0, mem.get("reputation_in_sect", 50) - 25)
            event["text"] = f"你在{sect_name}的权力博弈中落了下风，处境危急。"
            event["expanded_text"] = (f"你卷入的那场权力斗争以失败告终。"
                                      f"对手开始清算，你的政治资本一落千丈。"
                                      f"已有人在长老会上提议贬黜你。")
            event["effects"] = {"fortune": -2, "charisma": -1}
        return event

    def _alliance_negotiation(self, state: "GameState", sect: dict) -> dict:
        """Inter-sect alliance negotiation event."""
        sect_name = sect["name"]
        sects = self.get_all_sects(state)
        other_sects = [s for s in sects if s["sect_id"] != sect["sect_id"]]
        if not other_sects:
            return None
        target = random.choice(other_sects)
        target_name = target["name"]

        templates = [
            {
                "text": f"你作为{sect_name}使者出使{target_name}，商谈结盟事宜。",
                "expanded_text": f"掌门命你持宗门令牌出使{target_name}。"
                                 f"对方掌门亲自设宴接待，言语间试探{sect_name}的底牌。"
                                 f"你小心斟酌每一句话，既不能失了面子，"
                                 f"也不能泄露真正的筹码。外交之道，比斗法更凶险。",
                "effects": {"charisma": 2, "comprehension": 1},
                "event_type": "important",
            },
            {
                "text": f"{target_name}派使者前来{sect_name}求援，请你代为接待。",
                "expanded_text": f"{target_name}遭遇大敌，急需盟友相助。使者态度恳切，"
                                 f"但你知道：出兵相助意味着耗损自身实力，"
                                 f"按兵不动则可能坐视唇亡齿寒。你将利弊呈报掌门，"
                                 f"最终的决定将影响两宗未来百年的格局。",
                "effects": {"charisma": 1, "willpower": 1},
                "event_type": "important",
            },
        ]
        event = random.choice(templates)
        event["id"] = f"sect_alliance_{uuid.uuid4().hex[:6]}"
        event["category"] = "sect"
        event["tags"] = ["sect_politics", "diplomacy"]
        mem = state.sect_membership
        mem["reputation_in_sect"] = min(100, mem.get("reputation_in_sect", 50) + 5)
        mem["contribution"] = mem.get("contribution", 0) + 30
        return event

    def _find_rival_sect(self, state: "GameState", player_sect_id: str) -> Optional[dict]:
        """Find a rival or hostile sect (not necessarily hostile, just competing)."""
        relations = state.sect_world.get("relations", [])
        sects = state.sect_world.get("sects", {})
        for rel in relations:
            if rel.get("relation_type") in (SectRelationType.HOSTILE.value, SectRelationType.RIVAL.value):
                if rel["sect_a_id"] == player_sect_id:
                    enemy = sects.get(rel["sect_b_id"])
                elif rel["sect_b_id"] == player_sect_id:
                    enemy = sects.get(rel["sect_a_id"])
                else:
                    continue
                if enemy and not enemy.get("is_destroyed"):
                    return enemy
        return None

    # ── Expulsion / Demotion / Rejoin ──────────────────────────────────

    def check_expulsion(self, state: "GameState") -> Optional[dict]:
        """Check if player should be expelled due to low reputation.

        Returns expulsion event if triggered, None otherwise.
        """
        if not state.sect_membership:
            return None

        mem = state.sect_membership
        reputation = mem.get("reputation_in_sect", 50)

        # Reputation below 10 → 70% chance of expulsion
        if reputation < 10 and random.random() < 0.70:
            return self.leave_sect(state, reason="逐出师门")

        return None

    def check_demotion(self, state: "GameState") -> Optional[dict]:
        """Check if player should be demoted due to low reputation.

        Returns demotion event if triggered, None otherwise.
        """
        if not state.sect_membership:
            return None

        mem = state.sect_membership
        rank = mem.get("rank", SectRank.OUTER_DISCIPLE.value)
        reputation = mem.get("reputation_in_sect", 50)

        # Find current rank index
        current_idx = 0
        for i, r in enumerate(RANK_ORDER):
            if r.value == rank:
                current_idx = i
                break

        # Only demote if inner disciple+ AND reputation < 30 AND 15% chance
        if current_idx < 1:
            return None  # Can't demote outer disciples
        if reputation >= 30:
            return None
        if random.random() >= 0.15:
            return None

        # Demote one rank
        new_rank = RANK_ORDER[current_idx - 1]
        mem["rank"] = new_rank.value

        sect = self.get_player_sect(state)
        sect_name = sect["name"] if sect else "宗门"

        return {
            "id": f"sect_demotion_{uuid.uuid4().hex[:6]}",
            "text": f"因近年表现不佳，你在{sect_name}中被贬为{new_rank.value}。",
            "expanded_text": (f"长老会认为你近年修为欠缺、贡献不足，"
                              f"经商议后决定将你贬为{new_rank.value}。"
                              f"消息传开，同门中有人幸灾乐祸，有人唯恐避之不及。"
                              f"你心中苦涩，却只能默默承受。"),
            "event_type": "important",
            "category": "sect",
            "effects": {"willpower": 1},
            "tags": ["sect_demoted"],
        }

    def check_new_sect_opportunity(self, state: "GameState") -> Optional[dict]:
        """Check if a wandering cultivator gets a chance to join a new sect.

        Only fires when player has no sect and is a cultivator (realm >= 1).
        Returns join event if triggered, None otherwise.
        """
        if state.sect_membership:
            return None  # Already in a sect
        if state.realm < 1:
            return None  # Mortals don't get invited

        # 8% chance per turn
        if random.random() >= 0.08:
            return None

        available = self.get_all_sects(state)
        if not available:
            return None

        chosen = random.choice(available)
        sect_name = chosen["name"]

        # Determine entry rank based on realm
        if state.realm >= 4:  # 元婴+
            entry_rank = SectRank.ELDER
        elif state.realm >= 3:  # 金丹
            entry_rank = SectRank.CORE_DISCIPLE
        elif state.realm >= 2:  # 筑基
            entry_rank = SectRank.INNER_DISCIPLE
        else:
            entry_rank = SectRank.OUTER_DISCIPLE

        # Join the sect
        membership = SectMembership(
            sect_id=chosen["sect_id"],
            rank=entry_rank.value,
            contribution=0,
            reputation_in_sect=50,
            join_age=state.age,
            missions_completed=0,
            last_mission_age=0,
        )
        state.sect_membership = membership.model_dump()

        return {
            "id": f"sect_rejoin_{uuid.uuid4().hex[:6]}",
            "text": f"{sect_name}向你递来拜帖，欲招揽你入门为{entry_rank.value}。",
            "expanded_text": (f"你流落江湖已久，一日{sect_name}的人找上门来。"
                              f"來人言辞恳切：'{sect_name}缺人，久仰阁下修为，"
                              f"特来相邀入门。'你权衡再三，终于点头应下。"
                              f"从今以后，你便是{sect_name}的{entry_rank.value}了。"),
            "event_type": "fortune",
            "category": "sect",
            "effects": {"cultivation": 10, "fortune": 1},
            "tags": ["sect_joined", "sect_recruited"],
        }

    # ── Sect Joining Logic (for awakening) ────────────────────────────

    def get_available_sects_for_joining(self, state: "GameState") -> list[dict]:
        """Get sects available for the player to join (post-awakening).

        Filters out destroyed sects and demon sects (for initial join).
        """
        sects = self.get_all_sects(state)
        # Filter: non-demon for initial join, player can join demon later
        from .models import SectType
        return [s for s in sects if s.get("sect_type") != SectType.DEMON.value]

    def random_sect_join_at_awakening(self, state: "GameState") -> Optional[dict]:
        """Automatically assign player to a random sect at awakening.

        Called after Phase 3 (mortal awakening). 70% chance to join a sect.
        Returns join event or None (stays散修).
        """
        if random.random() > 0.70:
            return None  # 30% chance to stay as散修

        available = self.get_available_sects_for_joining(state)
        if not available:
            return None

        # Weighted by tier (higher tier = slightly more likely)
        weights = [s.get("tier", 3) for s in available]
        chosen = random.choices(available, weights=weights, k=1)[0]

        return self.join_sect(state, chosen["sect_id"])
