"""Basic Q-learning route selector for the Smart Traffic AI demo.

Rewards are simulated from route duration and distance; this is not a live
traffic-learning system. Q-values are kept in memory for the process lifetime.
"""
from random import Random
from typing import List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(tags=["Reinforcement Learning"])

# In-memory Q-table: state key -> action values. It resets when the API restarts.
_Q_TABLE = {}
_RNG = Random()


class RLRoute(BaseModel):
    distance_km: float = Field(..., gt=0, le=1000)
    duration_min: float = Field(..., gt=0, le=1000)


class RLRequest(BaseModel):
    routes: List[RLRoute] = Field(..., min_length=1, max_length=5)
    traffic_level: int = Field(default=0, ge=0, le=2)
    episodes: int = Field(default=250, ge=50, le=2000)


def _reward(route: RLRoute, traffic_level: int) -> float:
    """Synthetic reward: lower estimated trip cost produces a higher reward."""
    congestion_penalty = {0: 0.0, 1: 4.0, 2: 10.0}[traffic_level]
    estimated_cost = route.duration_min + (0.5 * route.distance_km) + congestion_penalty
    return -round(estimated_cost, 4)


@router.post("/rl/recommend")
def recommend_route(data: RLRequest):
    if not data.routes:
        raise HTTPException(status_code=422, detail="At least one route is required.")

    # One traffic state; each alternative route is an action.
    state = f"traffic_{data.traffic_level}_actions_{len(data.routes)}"
    rewards = [_reward(route, data.traffic_level) for route in data.routes]
    q_values = _Q_TABLE.setdefault(state, rewards.copy())

    # Q-learning update for a one-step route-choice task (terminal next state).
    alpha = 0.15
    gamma = 0.0
    epsilon = 0.25
    reward_history = []

    for episode in range(data.episodes):
        if _RNG.random() < epsilon:
            action = _RNG.randrange(len(data.routes))
        else:
            max_q = max(q_values)
            best_actions = [i for i, value in enumerate(q_values) if value == max_q]
            action = _RNG.choice(best_actions)

        reward = rewards[action]
        next_max = 0.0  # terminal state
        q_values[action] += alpha * (reward + gamma * next_max - q_values[action])
        reward_history.append(reward)
        epsilon = max(0.03, epsilon * 0.995)

    recommended_index = max(range(len(q_values)), key=lambda i: q_values[i])
    route_scores = []
    for index, route in enumerate(data.routes):
        route_scores.append({
            "route_index": index,
            "route_name": "Recommended Route" if index == 0 else f"Alternative {index}",
            "distance_km": round(route.distance_km, 1),
            "duration_min": round(route.duration_min, 1),
            "estimated_reward": rewards[index],
            "q_value": round(q_values[index], 4),
        })

    selected = data.routes[recommended_index]
    return {
        "algorithm": "Q-Learning",
        "state": state,
        "episodes": data.episodes,
        "recommended_route_index": recommended_index,
        "recommended_route_name": "Recommended Route" if recommended_index == 0 else f"Alternative {recommended_index}",
        "recommended_distance_km": round(selected.distance_km, 1),
        "recommended_duration_min": round(selected.duration_min, 1),
        "average_reward": round(sum(reward_history) / len(reward_history), 4),
        "best_reward": round(max(reward_history), 4),
        "route_scores": route_scores,
        "reward_source": "simulated_from_route_duration_and_distance",
    }
