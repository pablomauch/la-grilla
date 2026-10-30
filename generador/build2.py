"""Banco v2 (difícil): Difícil / Muy difícil / Experto.

Uso: python3 build2.py [juegos_por_nivel]  -> games2.json
"""
import json, random, re, sys, unicodedata, os
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from authors2 import AUTHORS
from gridlib import build_grid, number_grid

def norm(s):
    s = s.upper().replace('Ñ', '\0')
    s = ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')
    s = s.replace('\0', 'Ñ')
    return re.sub('[^A-ZÑ]', '', s)

# Palabras viejas sin tilde que llevan hiato (para separar bien las sílabas)
HIATO = {w: w for w in []}
for acc in ("RÍO DÍA TÍO FRÍO MAÍZ RAÍZ PAÍS BAÚL ATAÚD SANDÍA ALEGRÍA POLICÍA MELODÍA BAHÍA ROCÍO VACÍO OÍR REÍR "
            "LIBRERÍA ARMONÍA UTOPÍA ALEGORÍA LAÚD TÍA GRÚA PÚA BÚHO LÍO PÍO CRÍO ROÍDO LEÍDO CAÍDO OÍDO ACTÚA "
            "PULPERÍA TOLDERÍA COFRADÍA ALGARABÍA OSADÍA FELONÍA LOZANÍA SEQUÍA HURÍ AMBROSÍA DRÍADA OLIMPÍADA "
            "ELEGÍA LOTERÍA ZODÍACO ATAVÍO NAVÍO VOCERÍO MEDIODÍA AUTOBIOGRAFÍA POESÍA TRAVESÍA TEORÍA ENERGÍA ACEQUÍA").split():
    HIATO[norm(acc)] = acc

EXCLUDE = {'GOURMET', 'SOMMELIER', 'BEIGE', 'FIORDO'}
FILES = ['h1.txt', 'h2.txt', 'h3.txt', 'h4.txt', 'h5.txt']
OLD = ['words1.txt', 'words2.txt', 'words3.txt', 'words4.txt']

def load():
    W = {}
    def add(word, clue, tier):
        k = norm(word)
        if len(k) < 3 or ' ' in word.strip() or k in EXCLUDE: return
        if tier < 1 or tier > 3: return
        if k in norm(clue) and len(k) > 3: return
        e = W.setdefault(k, {'k': k, 'acc': word.upper(), 'clues': {}})
        if any(c in 'ÁÉÍÓÚÜ' for c in word.upper()): e['acc'] = word.upper()
        e['clues'].setdefault(tier, [])
        if clue not in e['clues'][tier]: e['clues'][tier].append(clue)
    for fn in FILES:
        for line in open(os.path.join(HERE, fn), encoding='utf-8'):
            line = line.strip()
            if not line or line.count('|') != 2: continue
            w, c, t = line.split('|')
            add(w, c, int(t))
    for fn in OLD:
        p = os.path.join(HERE, fn)
        if not os.path.exists(p): continue
        for line in open(p, encoding='utf-8'):
            line = line.strip()
            if not line or line.count('|') != 2: continue
            w, c, d = line.split('|')
            if d.strip() == '3':
                add(w, c, 1)
    for k, e in W.items():
        if not any(c in 'ÁÉÍÓÚÜ' for c in e['acc']) and k in HIATO:
            e['acc'] = HIATO[k]
        e['tiers'] = sorted(e['clues'])
    return W

W = load()

# ---------------- sílabas (con tildes) ----------------
WEAK = set('IUÜ'); STRONG = set('AEOÁÉÍÓÚ'); VOW = WEAK | STRONG
INSEP = {'PR','PL','BR','BL','FR','FL','TR','DR','CR','CL','GR','GL','CH','LL','RR','KR'}

def syllables(acc):
    w = acc.upper()
    t = []; i = 0
    while i < len(w):
        if w[i:i+2] in ('CH', 'LL', 'RR'): t.append(w[i:i+2]); i += 2
        elif w[i:i+2] in ('QU', 'GU') and i+2 < len(w) and w[i+2] in 'EIÉÍ': t.append(w[i:i+2]); i += 2
        else: t.append(w[i]); i += 1
    kind = []
    for j, x in enumerate(t):
        if x in VOW: kind.append('V')
        elif x == 'Y' and (j == len(t)-1 or t[j+1] not in VOW): kind.append('V')
        else: kind.append('C')
    nuclei = []; j = 0
    while j < len(t):
        if kind[j] == 'V':
            s = j
            strong = 1 if t[j] in STRONG else 0
            while True:
                nxt = j+1
                if nxt < len(t) and kind[nxt] == 'V':
                    a, b = t[j], t[nxt]
                    if a == 'Y': break
                    if b in STRONG and (a in STRONG or strong): break
                    strong += 1 if b in STRONG else 0
                    j = nxt; continue
                break
            nuclei.append((s, j)); j += 1
        else: j += 1
    if len(nuclei) <= 1: return [norm(w)]
    cuts = []
    for g in range(len(nuclei)-1):
        e = nuclei[g][1]; s = nuclei[g+1][0]
        cons = [x for x in t[e+1:s]]
        n = len(cons)
        if n == 0: cut = s
        elif n == 1: cut = e+1
        elif n == 2: cut = e+1 if (cons[0]+cons[1]) in INSEP else e+2
        elif n == 3: cut = e+2 if (cons[1]+cons[2]) in INSEP else e+3
        else: cut = e+3
        cuts.append(cut)
    out = []; prev = 0
    for c in cuts: out.append(''.join(t[prev:c])); prev = c
    out.append(''.join(t[prev:]))
    return [norm(x) for x in out]

# ---------------- pistas por nivel ----------------
PREF = {1: [1, 2], 2: [2, 3, 1], 3: [3, 2]}
def best_tier(k, L):
    for t in PREF[L]:
        if t in W[k]['clues']: return t
    return None

def clue(k, L, rng):
    t = best_tier(k, L)
    if L == 1 and 1 in W[k]['clues'] and 2 in W[k]['clues'] and rng.random() < .45: t = 2
    return rng.choice(W[k]['clues'][t])

def allowed(k, L):
    return best_tier(k, L) is not None

def pool(L, minlen=3, maxlen=99):
    return [k for k in W if minlen <= len(k) <= maxlen and allowed(k, L)]

# ---------------- claringrilla ----------------
def make_claringrillas(rng):
    combos = []
    for a, works in AUTHORS:
        for w in works: combos.append((a, w, norm(a), norm(w)))
    rng.shuffle(combos)
    cfg = {1: dict(keymin=11, keymax=16, wmin=5, wmax=9),
           2: dict(keymin=14, keymax=20, wmin=6, wmax=10),
           3: dict(keymin=16, keymax=24, wmin=6, wmax=11)}
    def cands(L):
        c = cfg[L]
        by_s = defaultdict(list); by_e = defaultdict(list)
        for k in pool(L, c['wmin'], c['wmax']):
            by_s[k[0]].append(k); by_e[(k[0], k[-1])].append(k)
        return by_s, by_e
    C = {L: cands(L) for L in (1, 2, 3)}
    def pick(lst, used, L):
        lst = [k for k in lst if k not in used]
        if not lst: return None
        # en niveles altos se prefieren pistas de nivel alto y palabras largas
        lst.sort(key=lambda k: (-best_tier(k, L) if L > 1 else 0, -len(k) if L == 3 else 0, rng.random()))
        top = lst[:max(3, len(lst)//3)]
        return rng.choice(top)
    def pack(a, w, answers, L, mode):
        sy = []
        for k in answers: sy += syllables(W[k]['acc'])
        sy.sort()
        return {'mode': mode, 'author': a, 'work': w,
                'rows': [{'a': k, 'c': clue(k, L, rng)} for k in answers], 'syl': sy}
    res = {1: [], 2: [], 3: []}
    used_combo = set()
    # 1) clásicas (iniciales = autor, finales = obra): las más difíciles
    for a, w, A, Wk in combos:
        if len(A) != len(Wk) or len(A) < 6: continue
        for L in (3, 2):
            by_s, by_e = C[L]
            used = set(); ans = []
            for i in range(len(A)):
                p = pick(by_e[(A[i], Wk[i])], used, L)
                if not p: break
                used.add(p); ans.append(p)
            if len(ans) == len(A):
                res[L].append(pack(a, w, ans, L, 'clasica')); used_combo.add((A, Wk)); break
    # 2) iniciales = autor + obra
    for a, w, A, Wk in combos:
        if (A, Wk) in used_combo: continue
        key = A + Wk; n = len(key)
        Ls = [L for L in (3, 2, 1) if cfg[L]['keymin'] <= n <= cfg[L]['keymax']]
        if not Ls: continue
        # repartir: el nivel con menos juegos primero
        Ls.sort(key=lambda L: len(res[L]))
        for L in Ls:
            by_s, _ = C[L]
            used = set(); ans = []
            for ch in key:
                p = pick(by_s[ch], used, L)
                if not p: break
                used.add(p); ans.append(p)
            if len(ans) == n:
                res[L].append(pack(a, w, ans, L, 'iniciales')); used_combo.add((A, Wk)); break
    for L in res: rng.shuffle(res[L])
    return res

# ---------------- crucigramas y autodefinidos ----------------
def grid_games(kind, N, rng):
    if kind == 'cw':
        cfg = {1: (13, 13, 26, 20, 11), 2: (13, 13, 28, 21, 12), 3: (15, 15, 34, 27, 13)}
    else:
        cfg = {1: (10, 10, 16, 11, 9), 2: (11, 11, 18, 13, 10), 3: (12, 12, 22, 15, 11)}
    out = {}
    for L, (R, Cc, target, minw, maxlen) in cfg.items():
        p = pool(L, 3, maxlen)
        lst = []; sigs = set()
        while len(lst) < N:
            sc, grid, cl, placed = build_grid(p, R, Cc, target, rng, autodef=(kind == 'ad'), tries=14, maxlen=maxlen)
            if len(placed) < minw: continue
            sig = tuple(sorted(x['w'] for x in placed))
            if sig in sigs: continue
            sigs.add(sig)
            words = []
            if kind == 'cw':
                num = number_grid(grid, placed)
                for x in placed:
                    words.append({'n': num[(x['r'], x['c'])], 'd': x['d'], 'r': x['r'], 'c': x['c'], 'a': x['w'], 'q': clue(x['w'], L, rng)})
                words.sort(key=lambda x: (x['d'], x['n']))
            else:
                for x in placed:
                    dr, dc = (0, 1) if x['d'] == 'A' else (1, 0)
                    words.append({'d': x['d'], 'r': x['r'], 'c': x['c'], 'cr': x['r']-dr, 'cc': x['c']-dc, 'a': x['w'], 'q': clue(x['w'], L, rng)})
            lst.append({'R': R, 'C': Cc, 'grid': [''.join(ch or '#' for ch in row) for row in grid], 'words': words})
            print(kind, L, len(lst), len(placed), file=sys.stderr, flush=True)
        out[L] = lst
    return out

# ---------------- sopa de letras con definiciones ----------------
ALPH = 'AAAAAABCCDDEEEEEEFGHIIIIIJLLLMMNNNÑOOOOOOPPQRRRRSSSSTTTTUUUVZ'
DIRS8 = [(0,1),(1,0),(1,1),(-1,1),(0,-1),(-1,0),(-1,-1),(1,-1)]
def make_sopas(N, rng):
    cfg = {1: (12, 12, 11), 2: (13, 13, 13), 3: (15, 15, 16)}
    out = {}
    for L, (R, Cc, nw) in cfg.items():
        p = pool(L, 4, R)
        lst = []
        while len(lst) < N:
            grid = [[None]*Cc for _ in range(R)]
            words = []
            for w in rng.sample(p, len(p)):
                if len(words) >= nw: break
                if any(w in x['a'] or x['a'] in w for x in words): continue
                opts = []
                for r in range(R):
                    for c in range(Cc):
                        for dr, dc in DIRS8:
                            er, ec = r+dr*(len(w)-1), c+dc*(len(w)-1)
                            if not (0 <= er < R and 0 <= ec < Cc): continue
                            ov = 0; ok = True
                            for k, ch in enumerate(w):
                                g = grid[r+dr*k][c+dc*k]
                                if g is not None and g != ch: ok = False; break
                                if g == ch: ov += 1
                            if ok and ov < len(w): opts.append((ov, rng.random(), r, c, dr, dc))
                if not opts: continue
                opts.sort(reverse=True)
                _, _, r, c, dr, dc = opts[0] if rng.random() < .6 else rng.choice(opts)
                for k, ch in enumerate(w): grid[r+dr*k][c+dc*k] = ch
                words.append({'a': w, 'r': r, 'c': c, 'dr': dr, 'dc': dc, 'q': clue(w, L, rng)})
            if len(words) < nw: continue
            # señuelos: comienzos de palabras de la lista sembrados en otros lugares
            for _ in range(nw * (1 + L)):
                w = rng.choice(words)['a']; frag = w[:rng.randint(3, min(5, len(w)-1))]
                r, c = rng.randrange(R), rng.randrange(Cc); dr, dc = rng.choice(DIRS8)
                cells = [(r+dr*k, c+dc*k) for k in range(len(frag))]
                if all(0 <= a < R and 0 <= b < Cc and grid[a][b] is None for a, b in cells):
                    for (a, b), ch in zip(cells, frag): grid[a][b] = ch
            for r in range(R):
                for c in range(Cc):
                    if grid[r][c] is None: grid[r][c] = rng.choice(ALPH)
            def count(w):
                n = 0
                for r in range(R):
                    for c in range(Cc):
                        if grid[r][c] != w[0]: continue
                        for dr, dc in DIRS8:
                            er, ec = r+dr*(len(w)-1), c+dc*(len(w)-1)
                            if 0 <= er < R and 0 <= ec < Cc and all(grid[r+dr*k][c+dc*k] == w[k] for k in range(len(w))): n += 1
                return n
            if any(count(x['a']) != 1 for x in words): continue
            lst.append({'R': R, 'C': Cc, 'grid': [''.join(row) for row in grid], 'words': words})
        print('sopa', L, len(lst), file=sys.stderr, flush=True)
        out[L] = lst
    return out

if __name__ == '__main__':
    N = int(sys.argv[1]) if len(sys.argv) > 1 else 60
    rng = random.Random(2026)
    from collections import Counter
    print('palabras', len(W), 'por nivel', {L: len(pool(L)) for L in (1, 2, 3)}, file=sys.stderr)
    cl = make_claringrillas(rng)
    print('claringrillas', {L: len(v) for L, v in cl.items()}, Counter(x['mode'] for v in cl.values() for x in v), file=sys.stderr, flush=True)
    data = {'claringrilla': cl, 'sopa': make_sopas(N, rng),
            'crucigrama': grid_games('cw', N, rng), 'autodefinido': grid_games('ad', N, rng)}
    json.dump(data, open(os.path.join(HERE, 'games2.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
