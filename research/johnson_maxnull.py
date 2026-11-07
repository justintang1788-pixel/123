"""挑出“最贴合顺序”本身会有过拟合：360 种顺序里挑最高的，随机数据也能挑出不低的数。
这里算：把各层随机循环平移后，同样在 360 种顺序里挑最高，这个“最高值”的分布。"""
from itertools import permutations
import sys
import numpy as np
from johnson_test import load_layers, johnson_states

window = int(sys.argv[1]) if len(sys.argv) > 1 else 12
H = load_layers(window)
cols = list(H.columns)
X = H.values
T, n = X.shape
valid = np.array(list(johnson_states(n).values()))
orders = [o for o in permutations(range(n)) if o[0] < o[-1]]


def best(X):
    m = 0
    for o in orders:
        Y = X[:, o]
        ok = (Y[:, None, :] == valid[None, :, :]).all(-1).any(-1)
        m = max(m, ok.mean())
    return m


obs = best(X)
rng = np.random.default_rng(1)
nul = []
for _ in range(int(sys.argv[2]) if len(sys.argv) > 2 else 200):
    Y = np.column_stack([np.roll(X[:, j], rng.integers(T)) for j in range(n)])
    nul.append(best(Y))
nul = np.array(nul)
print(f"窗口{window}：实际最贴合 {obs:.1%}；打乱后最贴合 平均 {nul.mean():.1%}，95分位 {np.quantile(nul,0.95):.1%}；p={(nul>=obs).mean():.3f}")
