"""Single allowlist of exact certificate families and reserved namespaces.

The registry is inert metadata. It is not supplied by workers or state files.
Typed adapters bind a canonical statement parser to a replay function.
Legacy adapters retain their specialized replay logic in proof_audit.
"""

# prefix: (parser module, replay module, report status for refutation)
# None parser means the replay function consumes the exact statement string.
# None refutation status means the adapter is proof-only.
TYPED = {
    'matrix-': ('matrix_permanent', 'matrix_permanent', 'counterexample'),
    'symbolic-': ('symbolic_discovery', 'symbolic_discovery', 'counterexample'),
    'dynamics-': ('dynamics_discovery', 'dynamics_discovery', 'counterexample'),
    'indexed-': ('indexed_algebra', 'indexed_algebra', 'counterexample'),
    'simplex-': ('simplex_discovery', 'simplex_discovery', 'counterexample'),
    'conditional-': ('conditional_theorems', 'conditional_theorems', 'counterexample'),
    'sturm-': ('polynomial', 'univariate_lab', 'refuted'),
    'sign-cell-': ('conditional_theorems', 'sign_cells_lab', 'refuted'),
    'projective-': (None, 'projective_lab', 'refuted'),
    'equational-': ('equational', 'equational', 'refuted'),
    'structure-': ('graph_structure', 'graph_structure', 'refuted'),
    'graph-linear-': ('graph_consequences', 'graph_consequences', None),
    'ideal-consequence-': ('conditional_theorems', 'ideal_consequence_lab', None),
    'amgm-': ('polynomial', 'amgm_lab', None),
    'graph-polynomial-': ('graph_nonlinear', 'graph_nonlinear', None),
    'integer-sign-': ('integer_lab', 'integer_lab', 'refuted'),
    'exponential-sign-': ('exponential_lab', 'exponential_lab', 'refuted'),
}

LEGACY_DIRECT = ('aff-', 'poly-', 'shift-', 'capacity-', 'graph-reduction-',
                 'finite-power-', 'lab-', 'invent-', 'recursive-')
DIRECT = LEGACY_DIRECT + tuple(TYPED)
# Nested proof bundles are deliberately excluded from portable direct facts.
AUDIT_DIRECT = DIRECT + ('bundle-',)
BRIDGES = ('bridge-', 'equiv-', 'repair-', 'sum-', 'theorem-',
           'synthesis-', 'representation-', 'extremal-', 'application-')
RESERVED = AUDIT_DIRECT + BRIDGES + ('knowledge-',)

def typed_replay(text, oid, status, cert):
    """Only import modules in the static allowlist, never worker-named code."""
    from importlib import import_module
    for prefix,(parser,verifier,negative) in TYPED.items():
        if oid.startswith(prefix):
            expected = ('proved' if status == 'proved' else
                        'refuted' if negative is not None and status == negative else None)
            if expected is None:
                return None
            claim = import_module(parser).parse_statement(text) if parser else text
            result = import_module(verifier).replay(claim, cert)
            return expected if result == expected else None
    return None
