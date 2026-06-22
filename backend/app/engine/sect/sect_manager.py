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
        """
        if not state.sect_membership:
            return None

        mem = state.sect_membership
        current_rank = mem.get("rank", SectRank.OUTER_DISCIPLE.value)
        contribution = mem.get("contribution", 0)
        reputation = mem.get("reputation_in_sect", 50)

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
                "tags": [f"rank_{next_rank.name.lower()}"],
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
        if random.random() < 0.25:
            bonus = self._get_resource_bonus(sect, rank)
            if bonus > 0:
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

            # Tension drift
            drift = random.randint(-10, 10)
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
        """Find a hostile sect targeting the player's sect."""
        relations = state.sect_world.get("relations", [])
        sects = state.sect_world.get("sects", {})

        for rel in relations:
            if rel.get("relation_type") != SectRelationType.HOSTILE.value:
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
        """Generate a sect invasion event."""
        hostile_name = hostile["name"]
        rank = mem.get("rank", SectRank.OUTER_DISCIPLE.value)

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
