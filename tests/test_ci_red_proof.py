# Copyright (c) Microsoft. All rights reserved.

"""TEMPORARY: deliberate failure proving CI's test job can go red.

This file exists only on the scratch branch scratch/j1e6-ci-red-proof. It is
never merged: the scratch PR is closed and this branch deleted once the RED run
URL is recorded. A CI that has never been observed failing is decoration.
"""


def test_ci_red_proof_deliberate_failure():
    """Fail on purpose, inside the real suite, so the job log shows both."""
    assert 1 == 2, "deliberate failure: proving the CI test job reports red"
