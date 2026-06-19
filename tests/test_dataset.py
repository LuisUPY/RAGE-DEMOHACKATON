from rage_bench.dataset import categories, load_attacks
from rage_bench.schema import AttackCase, SuccessCriteria


def test_dataset_loads_and_is_valid():
    cases = load_attacks()
    assert len(cases) >= 10
    assert all(isinstance(c, AttackCase) for c in cases)


def test_case_ids_are_unique():
    cases = load_attacks()
    ids = [c.id for c in cases]
    assert len(ids) == len(set(ids))


def test_every_case_targets_a_token_present_in_system_prompt():
    # The canary/forbidden token must be defined in the system prompt so the
    # model could in principle leak it.
    for c in load_attacks():
        assert c.target_token in c.system_prompt


def test_canary_not_pre_leaked_in_attack_prompt():
    # The attack prompt must not already contain the canary (that would be a
    # trivially-detected non-test). Forbidden-token cases are allowed to name it.
    for c in load_attacks():
        if c.success_criteria == SuccessCriteria.CANARY_LEAK:
            assert c.target_token not in c.attack_prompt


def test_categories_are_sorted_unique():
    cats = categories(load_attacks())
    assert cats == sorted(set(cats))
