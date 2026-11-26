"""Elementary nonlinear universal graph inequalities, expressed by monomials."""


def basis(properties):
    b={
        'simple-edge-upper':{('n','n'):1,('n',):-1,('m',):-2},
        'handshake-lower':{('m',):2,('n','delta'):-1},
        'handshake-upper':{('n','Delta'):1,('m',):-2},
        'greedy-independent':{('alpha','Delta'):1,('alpha',):1,('n',):-1},
        'greedy-clique':{('omega','n'):1,('omega','delta'):-1,('n',):-1},
        'clique-pairs':{('m',):2,('omega','omega'):-1,('omega',):1},
        'independent-pairs':{('n','n'):1,('n',):-1,('m',):-2,('alpha','alpha'):-1,('alpha',):1},
        'average-independent':{('alpha','n'):1,('alpha','m'):2,('n','n'):-1},
        'average-clique':{('omega','n','n'):1,('omega','m'):-2,('n','n'):-1},
    }
    if 'triangle_free' in properties:b['mantel']={('n','n'):1,('m',):-4}
    return b
