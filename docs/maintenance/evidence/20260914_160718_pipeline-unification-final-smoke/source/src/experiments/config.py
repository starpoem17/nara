"""Model and item-group configuration for maintained inference."""
from copy import deepcopy


MODEL = "models/gemma-4-26B-A4B-it-NVFP4"

PLANS = {
    "ungrouped": [list(range(1, 25))],
    "groups7": [[1, 2, 3, 4, 5, 6, 7, 8], [9, 19], [10, 11, 12, 13, 14, 15, 16, 17, 18],
                [20], [21], [22, 23], [24]],
    "groups9": [[1, 2, 3, 4], [5, 6, 7, 8], [9, 19], [10, 11, 12, 13], [14, 15, 16, 17, 18],
                [20], [21], [22, 23], [24]],
    "groups12": [[1, 2, 3, 4], [5, 6, 7], [8], [9, 19], [10, 11, 12, 13], [14], [15, 16],
                 [17, 18], [20], [21], [22, 23], [24]],
}
PLANS = {name: [[f"v{i}" for i in group] for group in groups]
         for name, groups in PLANS.items()}


def configuration(table, schema, plan, hypothesis, *, briefing_rule=False):
    if briefing_rule and (plan != "groups12" or not hypothesis):
        raise ValueError("Briefing rule requires the twelve-group rule-based strategy")
    rule_items = ("v2", "v3", "v22") if briefing_rule else ("v2", "v3")
    keep = [key for key in table if not hypothesis or key not in rule_items]
    selected = {key: table[key] for key in keep}
    spec = deepcopy(schema)
    spec["properties"] = {key: spec["properties"][key] for key in keep}
    spec["required"] = keep
    groups = [[key for key in group if key in keep] for group in PLANS[plan]]
    assert all(groups) and sorted(key for group in groups for key in group) == sorted(keep)
    return selected, spec, groups
