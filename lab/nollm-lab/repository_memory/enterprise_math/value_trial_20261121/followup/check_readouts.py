"""Check the restricted fixed-probe claim in the source-only answer, in scalar Hamming distance."""
from itertools import combinations, combinations_with_replacement
import json


def pair(n, t, s):
    # Offset s*e2. For arbitrary a, Q(x(t)+a) has t-dependent part
    # 4*t*t + 2*((x(0)+a)·v)*t. Varying s mod 6 covers that coefficient
    # mod 12. The constant shifts both scalar alphabets independently of t.
    square = (t+s)**2 + 2*(n-t)**2 + 1 + t*t
    return square % 4, square % 6


def minima(n):
    pairs = list(combinations(range(n+1), 2))
    distances = [[sum(a != b for a,b in zip(pair(n,i,s),pair(n,j,s))) for i,j in pairs]
                 for s in range(6)]
    found = {}
    for length in range(1, 6):
        for offsets in combinations_with_replacement(range(6),length):
            distance = min(map(sum, zip(*(distances[s] for s in offsets))))
            for errors in (0, 1):
                if errors not in found and distance >= 2*errors + 1:
                    found[errors] = {'offset_multipliers_e2': offsets, 'min_scalar_distance': distance}
        if len(found) == 2:
            break
    return found


if __name__ == '__main__':
    print(json.dumps({n: minima(n) for n in range(1,6)}, indent=2))
