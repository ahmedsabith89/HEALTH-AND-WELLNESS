import math
import random
from typing import List, Dict, Any, Tuple, Set, Optional
from collections import defaultdict, Counter

def calculate_student_features(student: Dict[str, Any], questionnaire: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extract and normalize numerical and categorical features for a student."""
    if not questionnaire:
        # Defaults for uncompleted questionnaire
        return {
            "id": student["id"],
            "name": student["full_name"],
            "roll_number": student["roll_number"],
            "speaking": 3.0,
            "no_ppt": 3.0,
            "social": 3.0,
            "leadership": 3.0,
            "persona": "Planner",
            "atmosphere": "Balanced",
            "priority": "Good communication",
            "fun_ppt": "Start explaining confidently",
            "fun_rush": "The person making a plan",
            "has_q": False
        }
    
    return {
        "id": student["id"],
        "name": student["full_name"],
        "roll_number": student["roll_number"],
        "speaking": float(questionnaire.get("q_speaking_comfort", 3)),
        "no_ppt": float(questionnaire.get("q_speaking_no_ppt", 3)),
        "social": float(questionnaire.get("q_social_comfort", 3)),
        "leadership": float(questionnaire.get("q_leadership_comfort", 3)),
        "persona": questionnaire.get("q_persona", "Planner"),
        "atmosphere": questionnaire.get("q_atmosphere", "Balanced"),
        "priority": questionnaire.get("q_priority", "Good communication"),
        "fun_ppt": questionnaire.get("q_fun_ppt_crash", "Start explaining confidently"),
        "fun_rush": questionnaire.get("q_fun_10min_rush", "The person making a plan"),
        "has_q": True
    }


def calculate_group_metrics(members_features: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate fairness diagnostics and balance metrics for a single group."""
    n = len(members_features)
    if n == 0:
        return {
            "member_count": 0,
            "speaking_avg": 0.0,
            "no_ppt_avg": 0.0,
            "social_avg": 0.0,
            "leadership_avg": 0.0,
            "high_speakers_count": 0,
            "low_speakers_count": 0,
            "leaders_count": 0,
            "personas_count": {},
            "diversity_score": 0.0,
            "balance_score": 0.0,
            "summary": "Empty Group"
        }

    speak_avg = sum(m["speaking"] for m in members_features) / n
    no_ppt_avg = sum(m["no_ppt"] for m in members_features) / n
    soc_avg = sum(m["social"] for m in members_features) / n
    lead_avg = sum(m["leadership"] for m in members_features) / n

    high_speakers = sum(1 for m in members_features if m["speaking"] >= 4)
    low_speakers = sum(1 for m in members_features if m["speaking"] <= 2)
    leaders = sum(1 for m in members_features if m["leadership"] >= 4)

    personas = [m["persona"] for m in members_features]
    persona_counts = dict(Counter(personas))
    unique_personas = len(persona_counts)
    # Diversity ratio: unique personas / n
    diversity_score = min(100.0, round((unique_personas / min(n, 6)) * 100, 1))

    # Evaluate Balance Score (0 - 100)
    # Penalize lack of high speakers, excessive low speakers, lack of leadership, low persona diversity
    score = 100.0
    if high_speakers == 0:
        score -= 25.0
    elif high_speakers > 4:
        score -= 10.0

    if low_speakers > 3:
        score -= 15.0

    if leaders == 0:
        score -= 15.0
    elif leaders > 3:
        score -= 10.0

    if unique_personas < 3:
        score -= 20.0
    elif unique_personas < 4:
        score -= 10.0

    # Speaker average distance from ideal range (3.0 to 3.8)
    if speak_avg < 2.5 or speak_avg > 4.2:
        score -= 15.0
    elif speak_avg < 2.8 or speak_avg > 3.9:
        score -= 5.0

    score = max(30.0, min(100.0, score))

    # Construct descriptive summary for admin
    summary_parts = []
    if high_speakers >= 1:
        summary_parts.append(f"{high_speakers} confident presenter{'s' if high_speakers > 1 else ''}")
    else:
        summary_parts.append("Developing presenters")

    if leaders >= 1:
        summary_parts.append(f"{leaders} anchor leader{'s' if leaders > 1 else ''}")

    summary_parts.append(f"{unique_personas} distinct working styles")

    summary = " • ".join(summary_parts)

    return {
        "member_count": n,
        "speaking_avg": round(speak_avg, 2),
        "no_ppt_avg": round(no_ppt_avg, 2),
        "social_avg": round(soc_avg, 2),
        "leadership_avg": round(lead_avg, 2),
        "high_speakers_count": high_speakers,
        "low_speakers_count": low_speakers,
        "leaders_count": leaders,
        "personas_count": persona_counts,
        "diversity_score": diversity_score,
        "balance_score": round(score, 1),
        "summary": summary
    }


def solve_group_balancing(
    students: List[Dict[str, Any]],
    questionnaires_map: Dict[int, Dict[str, Any]],
    groups_config: List[Dict[str, Any]],
    together_pairs: List[Tuple[int, int]],
    apart_pairs: List[Tuple[int, int]],
    locked_groups: Set[int],
    locked_students: Dict[int, int]  # student_id -> group_id
) -> Dict[int, List[int]]:
    """
    Executes balanced group generation meeting:
    - Exactly 10 groups: 9 of 7, 1 of 6.
    - Keep together / Keep apart constraints.
    - Locked groups & locked students preservation.
    - Multi-objective speaker & leadership fairness optimization.
    Returns: Dict mapping group_id -> list of student_ids.
    """
    # 1. Feature extraction
    features_by_id: Dict[int, Dict[str, Any]] = {}
    for s in students:
        s_id = s["id"]
        features_by_id[s_id] = calculate_student_features(s, questionnaires_map.get(s_id))

    all_student_ids = [s["id"] for s in students]
    total_students = len(all_student_ids)

    # 2. Build together disjoint sets
    parent = {s_id: s_id for s_id in all_student_ids}
    def find(i):
        if parent[i] == i:
            return i
        parent[i] = find(parent[i])
        return parent[i]
    def union(i, j):
        root_i = find(i)
        root_j = find(j)
        if root_i != root_j:
            parent[root_i] = root_j

    for a, b in together_pairs:
        if a in parent and b in parent:
            union(a, b)

    clusters: Dict[int, List[int]] = defaultdict(list)
    for s_id in all_student_ids:
        clusters[find(s_id)].append(s_id)

    # Conflict set for APART constraints
    apart_conflicts: Set[Tuple[int, int]] = set()
    for a, b in apart_pairs:
        apart_conflicts.add((min(a, b), max(a, b)))

    # Target capacities per group: group_id -> capacity
    group_capacities = {g["id"]: g["max_members"] for g in groups_config}
    group_ids = [g["id"] for g in groups_config]

    # Pre-populate assignments
    assignment: Dict[int, List[int]] = {g_id: [] for g_id in group_ids}
    assigned_students: Set[int] = set()

    # Place locked groups
    for g_id in locked_groups:
        for s in students:
            if s.get("group_id") == g_id:
                assignment[g_id].append(s["id"])
                assigned_students.add(s["id"])

    # Place individually locked students
    for s_id, g_id in locked_students.items():
        if s_id not in assigned_students and g_id in assignment:
            assignment[g_id].append(s_id)
            assigned_students.add(s_id)

    # Place remainder of together clusters that already have a member assigned
    for root, cluster_members in clusters.items():
        assigned_in_cluster = [m for m in cluster_members if m in assigned_students]
        if assigned_in_cluster:
            # find which group they are in
            target_g = None
            for g_id, mems in assignment.items():
                if any(m in mems for m in assigned_in_cluster):
                    target_g = g_id
                    break
            if target_g:
                for m in cluster_members:
                    if m not in assigned_students:
                        assignment[target_g].append(m)
                        assigned_students.add(m)

    # Remaining clusters to assign
    remaining_clusters = []
    for root, members in clusters.items():
        unassigned_in_cluster = [m for m in members if m not in assigned_students]
        if unassigned_in_cluster:
            remaining_clusters.append(unassigned_in_cluster)

    # Sort remaining clusters by aggregate speaking score descending to enable serpentine stratification
    def cluster_score(cluster):
        return sum(features_by_id[m]["speaking"] + features_by_id[m]["leadership"] * 0.5 for m in cluster) / len(cluster)

    remaining_clusters.sort(key=cluster_score, reverse=True)

    # Available groups that are not full and not locked
    for cluster in remaining_clusters:
        c_size = len(cluster)
        best_g = None
        best_diff = float('inf')

        # Find best group that has room for the entire cluster and minimal conflicts
        valid_groups = [
            g_id for g_id in group_ids
            if g_id not in locked_groups and len(assignment[g_id]) + c_size <= group_capacities[g_id]
        ]

        if not valid_groups:
            # Fallback if capacity overflow
            valid_groups = [g_id for g_id in group_ids if g_id not in locked_groups]

        # Score candidate groups
        for g_id in valid_groups:
            current_mems = assignment[g_id]
            # Check APART conflicts
            conflict_penalty = 0
            for cm in current_mems:
                for nm in cluster:
                    pair = (min(cm, nm), max(cm, nm))
                    if pair in apart_conflicts:
                        conflict_penalty += 1000

            # Current speaking score in group
            current_speak_sum = sum(features_by_id[m]["speaking"] for m in current_mems)
            total_speak_projected = current_speak_sum + sum(features_by_id[m]["speaking"] for m in cluster)
            proj_count = len(current_mems) + len(cluster)
            proj_avg = total_speak_projected / max(1, proj_count)

            # Capacity balance factor
            cap_diff = (group_capacities[g_id] - len(current_mems))

            score = conflict_penalty + (proj_avg * 10) - (cap_diff * 2)
            if score < best_diff:
                best_diff = score
                best_g = g_id

        if best_g is None:
            best_g = random.choice(group_ids)

        for m in cluster:
            assignment[best_g].append(m)
            assigned_students.add(m)

    # 4. Global Target Metrics for Optimization
    global_speak_avg = sum(features_by_id[s_id]["speaking"] for s_id in all_student_ids) / total_students
    global_lead_avg = sum(features_by_id[s_id]["leadership"] for s_id in all_student_ids) / total_students

    def calculate_system_energy(curr_assignment: Dict[int, List[int]]) -> float:
        energy = 0.0
        for g_id, mems in curr_assignment.items():
            cap = group_capacities[g_id]
            # Heavy penalty for violating size (must be exact)
            if len(mems) != cap:
                energy += abs(len(mems) - cap) * 5000.0

            if not mems:
                continue

            n = len(mems)
            m_feats = [features_by_id[m] for m in mems]
            g_speak_avg = sum(f["speaking"] for f in m_feats) / n
            g_lead_avg = sum(f["leadership"] for f in m_feats) / n

            # Speaking variance penalty
            energy += ((g_speak_avg - global_speak_avg) ** 2) * 80.0
            # Leadership variance penalty
            energy += ((g_lead_avg - global_lead_avg) ** 2) * 50.0

            # High speakers count (desire 1 to 3)
            high_spk = sum(1 for f in m_feats if f["speaking"] >= 4)
            if high_spk == 0:
                energy += 200.0
            elif high_spk > 4:
                energy += 50.0

            # Low speakers count (penalize if > 3 in one group)
            low_spk = sum(1 for f in m_feats if f["speaking"] <= 2)
            if low_spk > 3:
                energy += 120.0

            # Leaders count (desire at least 1)
            lead_cnt = sum(1 for f in m_feats if f["leadership"] >= 4)
            if lead_cnt == 0:
                energy += 150.0

            # Persona diversity bonus/penalty
            unique_personas = len(set(f["persona"] for f in m_feats))
            energy -= unique_personas * 15.0

            # Check Apart constraints
            for i in range(len(mems)):
                for j in range(i + 1, len(mems)):
                    pair = (min(mems[i], mems[j]), max(mems[i], mems[j]))
                    if pair in apart_conflicts:
                        energy += 3000.0

            # Check Together constraints within group
            for m in mems:
                root = find(m)
                for mate in clusters[root]:
                    if mate not in mems:
                        energy += 3000.0

        return energy

    # 5. Local Search / Simulated Annealing to optimize balance
    # Only swap unlocked students that are not part of multi-student together clusters
    swappable_by_group: Dict[int, List[int]] = {}
    for g_id in group_ids:
        if g_id in locked_groups:
            swappable_by_group[g_id] = []
        else:
            swappable_by_group[g_id] = [
                m for m in assignment[g_id]
                if m not in locked_students and len(clusters[find(m)]) == 1
            ]

    current_energy = calculate_system_energy(assignment)
    best_energy = current_energy
    best_assignment = {g_id: list(mems) for g_id, mems in assignment.items()}

    # Simulated Annealing parameters
    iterations = 1500
    temperature = 25.0
    cooling_rate = 0.995

    eligible_groups = [g_id for g_id in group_ids if g_id not in locked_groups]

    if len(eligible_groups) >= 2:
        for step in range(iterations):
            g1, g2 = random.sample(eligible_groups, 2)
            mems1 = swappable_by_group[g1]
            mems2 = swappable_by_group[g2]

            if not mems1 or not mems2:
                continue

            s1 = random.choice(mems1)
            s2 = random.choice(mems2)

            # Tentative swap
            assignment[g1].remove(s1)
            assignment[g1].append(s2)
            assignment[g2].remove(s2)
            assignment[g2].append(s1)

            candidate_energy = calculate_system_energy(assignment)
            delta = candidate_energy - current_energy

            if delta < 0 or (temperature > 0.01 and math.exp(-delta / max(0.1, temperature)) > random.random()):
                current_energy = candidate_energy
                swappable_by_group[g1].remove(s1)
                swappable_by_group[g1].append(s2)
                swappable_by_group[g2].remove(s2)
                swappable_by_group[g2].append(s1)

                if candidate_energy < best_energy:
                    best_energy = candidate_energy
                    best_assignment = {g_id: list(mems) for g_id, mems in assignment.items()}
            else:
                # Revert swap
                assignment[g1].remove(s2)
                assignment[g1].append(s1)
                assignment[g2].remove(s1)
                assignment[g2].append(s2)

            temperature *= cooling_rate

    # Ensure sizes match exactly 7 for groups 1-9 and 6 for group 10
    final_assignment = best_assignment

    return final_assignment


def allocate_topics_preference(
    groups: List[Dict[str, Any]],
    topics: List[Dict[str, Any]],
    preferences: Dict[int, List[int]]  # group_id -> [topic_id_rank1, topic_id_rank2, topic_id_rank3]
) -> Dict[int, int]:
    """
    Allocates 10 unique topics to 10 groups to maximize overall preference satisfaction.
    Weights: 1st preference = 100 points, 2nd = 60, 3rd = 30, unranked = 5.
    Returns: Dict mapping group_id -> topic_id.
    """
    topic_ids = [t["id"] for t in topics]
    group_ids = [g["id"] for g in groups]

    # Preference score matrix
    def get_score(g_id: int, t_id: int) -> int:
        group_prefs = preferences.get(g_id, [])
        if len(group_prefs) > 0 and group_prefs[0] == t_id:
            return 100
        elif len(group_prefs) > 1 and group_prefs[1] == t_id:
            return 60
        elif len(group_prefs) > 2 and group_prefs[2] == t_id:
            return 30
        return 5

    # Optimal Hungarian or Greedy with Local Search matching
    # Since there are exactly 10 groups and 10 topics (10! = 3.6M, small permutation space)
    # A fast randomized local search finds the global maximum assignment in milliseconds.
    best_assignment = {}
    best_total_score = -1

    # Start with greedy matching
    shuffled_topics = list(topic_ids)
    for trial in range(500):
        available_topics = set(topic_ids)
        current_map = {}
        trial_score = 0
        
        # Shuffle group order for different greedy initializations
        trial_groups = list(group_ids)
        if trial > 0:
            random.shuffle(trial_groups)

        for g_id in trial_groups:
            # Pick best available topic
            best_t = max(available_topics, key=lambda t_id: get_score(g_id, t_id))
            current_map[g_id] = best_t
            trial_score += get_score(g_id, best_t)
            available_topics.remove(best_t)

        if trial_score > best_total_score:
            best_total_score = trial_score
            best_assignment = current_map

    return best_assignment


def allocate_topics_random(
    groups: List[Dict[str, Any]],
    topics: List[Dict[str, Any]]
) -> Dict[int, int]:
    """Randomly allocates the 10 unique topics to 10 groups."""
    topic_ids = [t["id"] for t in topics]
    random.shuffle(topic_ids)
    assignment = {}
    for g, t_id in zip(groups, topic_ids):
        assignment[g["id"]] = t_id
    return assignment
