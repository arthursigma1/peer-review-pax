# Stage 3 — Action and Commitment to Pillar Mapping

## Objective

Map every extracted action (ACT-*) and commitment (CMT-*) to the strategic pillar framework established in Stage 2. This mapping reveals where the company is actually deploying resources and making promises relative to where it says its priorities lie. Actions and commitments that do not map to any stated pillar are flagged as potentially revealing unstated priorities or strategic drift.

## Inputs

- Pillar map: `data/processed/stage_2_pillars.json` (PIL-* definitions)
- Actions: `data/processed/stage_1b_actions.json` (ACT-* elements)
- Commitments: `data/processed/stage_1c_commitments.json` (CMT-* elements)
- Source catalog: `data/processed/stage_0_sources.md`
- This prompt template

## Method

### Step 1: Action-to-Pillar Classification

For each ACT-* element, classify it into exactly one of:

| Classification | Criteria |
|----------------|----------|
| **Aligned** (to a specific PIL-*) | The action clearly and directly advances a stated strategic pillar. Assign the single most relevant `pillar_id`. |
| **Multi-pillar** | The action plausibly advances 2+ pillars. Assign primary and secondary `pillar_id` values with an explanation. |
| **Unaligned** | The action does not correspond to any identified pillar. This may indicate a shadow strategy, legacy commitment, or strategic drift. |
| **Ambiguous** | Insufficient information to determine alignment. State what additional evidence would resolve the ambiguity. |

**Classification rules:**
- When an action could map to multiple pillars, assign the primary pillar based on which strategic area the action most directly impacts.
- "Unaligned" is not a negative judgment; it is an analytical observation that warrants investigation.
- Do not force-fit actions into pillars. An honest "unaligned" classification is more valuable than a tenuous mapping.

### Step 2: Commitment-to-Pillar Classification

Apply the same classification framework to each CMT-* element. Additionally, for commitments:

1. **Update status:** Using action evidence from Stage 1B, refine the preliminary status assessment from Stage 1C:
   - If an ACT-* directly fulfills a CMT-*, update status to `fulfilled` and cite the action.
   - If an ACT-* contradicts a CMT-*, update status to `contradicted` and cite the action.
   - If a commitment's timeline has passed with no corresponding action, flag as `silently_abandoned`.
2. **Cross-reference with pillar priority:** Note whether the commitment relates to a high-priority or low-priority pillar, as this affects the significance of fulfillment or abandonment.

### Step 3: Resource Allocation Estimation

For each pillar, estimate the percentage of observable resource allocation based on:

1. **Capital allocation:** Aggregate capex, acquisition spend, and investment amounts mapped to each pillar.
2. **Organizational investment:** Headcount changes, leadership attention, and organizational structure decisions mapped to each pillar.
3. **Product investment:** Number and magnitude of product launches and feature development mapped to each pillar.

Express allocation as a percentage distribution that sums to 100% (including the "unaligned" category).

**Important caveats:**
- These are rough estimates based on publicly observable signals, not precise financial decompositions.
- State the basis for each estimate and its precision limitations.
- If quantified data is insufficient, provide a qualitative ranking (highest / high / medium / low / minimal) instead of percentages.

### Step 4: Commitment Fulfillment Summary

Produce a summary of commitment fulfillment across all pillars:

| Metric | Calculation |
|--------|-------------|
| Total commitments | Count of all CMT-* elements |
| Fulfilled | Count with status `fulfilled` |
| In progress | Count with status `in_progress` |
| Partially fulfilled | Count with status `partially_fulfilled` |
| Contradicted | Count with status `contradicted` |
| Silently abandoned | Count with status `silently_abandoned` |
| Cannot assess | Count with status `cannot_assess` |
| Fulfillment rate | (fulfilled + partially_fulfilled) / (total - cannot_assess - in_progress) |

Break this summary down per pillar for use in Stage 4 coherence scoring.

### Step 5: Unaligned Action Analysis

For each action classified as "unaligned":

1. **Significance assessment:** Is this a high-magnitude action that might represent a shadow strategy, or a low-magnitude action that is operationally routine?
2. **Pattern detection:** Do multiple unaligned actions cluster into a coherent theme that could represent an unstated strategic area?
3. **Legacy vs. drift:** Determine whether unaligned actions appear to be legacy commitments (winding down inherited activities) or new initiatives that signal emergent priorities.

## Output Format

Produce a JSON file (`data/processed/stage_3_actions.json`) with the following schema:

```json
{
  "metadata": {
    "stage": "3",
    "company": "Block, Inc.",
    "mapping_date": "YYYY-MM-DD",
    "inputs": ["stage_2_pillars.json", "stage_1b_actions.json", "stage_1c_commitments.json"],
    "methodology": "Action and commitment classification to pillar framework per prompts/03_map_actions.md",
    "limitations": "..."
  },
  "action_mapping": {
    "PIL-001": {
      "pillar_name": "...",
      "aligned_actions": [
        {
          "action_id": "ACT-001",
          "rationale": "Brief explanation of why this action maps to this pillar",
          "magnitude": "high | medium | low"
        }
      ],
      "aligned_commitments": [
        {
          "commitment_id": "CMT-001",
          "status": "fulfilled | in_progress | partially_fulfilled | contradicted | silently_abandoned | cannot_assess",
          "status_evidence": "Evidence supporting the status determination",
          "rationale": "Brief explanation of why this commitment maps to this pillar"
        }
      ],
      "estimated_resource_allocation_pct": 35,
      "allocation_basis": "Description of how the percentage was estimated"
    }
  },
  "unaligned_actions": [
    {
      "action_id": "ACT-015",
      "description": "Brief description of the unaligned action",
      "magnitude": "high | medium | low",
      "analysis": "Assessment of significance — shadow strategy indicator, legacy commitment, or routine operational matter",
      "potential_theme": "If multiple unaligned actions cluster, name the emerging theme"
    }
  ],
  "ambiguous_mappings": [
    {
      "element_id": "ACT-007",
      "candidate_pillars": ["PIL-001", "PIL-003"],
      "resolution_needed": "Description of what additional evidence would resolve the ambiguity"
    }
  ],
  "commitment_tracker": {
    "total": 15,
    "fulfilled": 5,
    "in_progress": 4,
    "partially_fulfilled": 2,
    "contradicted": 1,
    "silently_abandoned": 2,
    "cannot_assess": 1,
    "fulfillment_rate": 0.70,
    "per_pillar": {
      "PIL-001": { "total": 5, "fulfilled": 3, "contradicted": 0, "silently_abandoned": 1 }
    }
  },
  "resource_allocation_summary": {
    "PIL-001": { "pct": 35, "basis": "..." },
    "PIL-002": { "pct": 30, "basis": "..." },
    "unaligned": { "pct": 5, "basis": "..." }
  }
}
```

## Limitations

- Action-to-pillar mapping requires interpretive judgment. Some actions legitimately serve multiple pillars, and the primary assignment is a simplification.
- Resource allocation percentages are estimates based on public data. Actual internal allocation may differ significantly from what is observable externally.
- Commitment status assessment depends on temporal coverage of sources. A commitment classified as "silently abandoned" may have been fulfilled in a period not covered by available sources.
- Actions with ambiguous strategic purpose may be misclassified in either direction (aligned when actually unrelated, or unaligned when actually strategic).

## Bias Awareness

1. **Mapping confirmation bias:** There is a natural tendency to map actions to pillars (finding alignment) rather than classifying them as unaligned. Apply a rigorous standard: alignment must be *clearly and directly* supported, not merely plausible.
2. **Company framing adoption:** When a company describes an action as supporting a particular strategy, the analyst may accept this framing uncritically. Evaluate whether the action's *actual effect* supports the pillar, not merely whether management *frames* it that way.
3. **Magnitude distortion in press releases:** Company-produced sources may overstate the magnitude and strategic significance of routine actions. Cross-reference with financial data for grounded magnitude assessment.
4. **Absence bias:** Actions the company does *not* take are analytically invisible but strategically important. A pillar with many stated commitments but no corresponding actions may signal drift more clearly than any single misaligned action.
5. **Temporal mismatch:** Actions taken in a given quarter may relate to commitments made in a prior period under different strategic conditions. Evaluate alignment based on the commitment's original context, not retroactively.
