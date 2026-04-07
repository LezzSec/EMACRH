# -*- coding: utf-8 -*-
"""
Diagnostic de performance EMAC — emac_db
Lance : py -m scripts.diagnostic_performance  (depuis App/)
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from infrastructure.db.configbd import get_connection

# ── Couleurs ANSI ────────────────────────────────────────────────────────────
R  = "\033[91m"   # rouge
G  = "\033[92m"   # vert
Y  = "\033[93m"   # jaune
B  = "\033[94m"   # bleu
W  = "\033[97m"   # blanc
DIM = "\033[2m"   # grisé
RESET = "\033[0m"
BOLD  = "\033[1m"


def titre(texte):
    largeur = 68
    print(f"\n{BOLD}{B}{'─' * largeur}{RESET}")
    print(f"{BOLD}{B}  {texte}{RESET}")
    print(f"{BOLD}{B}{'─' * largeur}{RESET}")


def ok(msg):   print(f"  {G}✅ {msg}{RESET}")
def warn(msg): print(f"  {Y}⚠️  {msg}{RESET}")
def err(msg):  print(f"  {R}❌ {msg}{RESET}")
def info(msg): print(f"  {DIM}{msg}{RESET}")


def table(colonnes, lignes, color_fn=None):
    """Affiche un tableau ASCII simple."""
    if not lignes:
        info("(aucun résultat)")
        return
    largeurs = [max(len(str(c)), max((len(str(l[i])) for l in lignes), default=0))
                for i, c in enumerate(colonnes)]
    sep = "  " + "─" * (sum(largeurs) + 3 * len(colonnes) - 1)
    entete = "  " + "  ".join(str(c).ljust(largeurs[i]) for i, c in enumerate(colonnes))
    print(f"{DIM}{sep}{RESET}")
    print(f"{BOLD}{W}{entete}{RESET}")
    print(f"{DIM}{sep}{RESET}")
    for ligne in lignes:
        row_str = "  " + "  ".join(str(v if v is not None else "NULL").ljust(largeurs[i])
                                    for i, v in enumerate(ligne))
        couleur = color_fn(ligne) if color_fn else ""
        print(f"{couleur}{row_str}{RESET}")
    print(f"{DIM}{sep}{RESET}")


# ── Connexion ────────────────────────────────────────────────────────────────
try:
    conn = get_connection()
    cur  = conn.cursor()
except Exception as e:
    print(f"{R}Impossible de se connecter à la base : {e}{RESET}")
    sys.exit(1)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 1 — Index existants sur les tables critiques
# ─────────────────────────────────────────────────────────────────────────────
titre("SECTION 1 — Index existants sur les tables critiques")

cur.execute("""
    SELECT
        TABLE_NAME,
        INDEX_NAME,
        GROUP_CONCAT(COLUMN_NAME ORDER BY SEQ_IN_INDEX SEPARATOR ', ') AS colonnes,
        IF(NON_UNIQUE = 0, 'UNIQUE', 'Normal') AS type_index
    FROM information_schema.STATISTICS
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME IN ('personnel','polyvalence','contrat','historique',
                         'postes','utilisateurs','declaration','formation')
    GROUP BY TABLE_NAME, INDEX_NAME, NON_UNIQUE
    ORDER BY TABLE_NAME, INDEX_NAME
""")
rows = cur.fetchall()
table(["Table", "Index", "Colonnes", "Type"], rows)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 2 — Index manquants
# ─────────────────────────────────────────────────────────────────────────────
titre("SECTION 2 — Vérification des index critiques")

def check_index(table_name, colonnes_combo):
    """Vérifie si un index couvre exactement ces colonnes dans cet ordre."""
    placeholders = ','.join(['%s'] * len(colonnes_combo))
    cur.execute(f"""
        SELECT INDEX_NAME
        FROM information_schema.STATISTICS
        WHERE TABLE_SCHEMA = DATABASE()
          AND TABLE_NAME = %s
          AND COLUMN_NAME IN ({placeholders})
          AND SEQ_IN_INDEX <= %s
        GROUP BY INDEX_NAME
        HAVING COUNT(*) = %s
    """, (table_name, *colonnes_combo, len(colonnes_combo), len(colonnes_combo)))
    return cur.fetchone() is not None

checks = [
    ("contrat",    ["personnel_id", "actif"],
     "contrat(personnel_id, actif) — accélère get_paginated() à chaque page"),
    ("historique", ["utilisateur"],
     "historique(utilisateur) — filtre par user dans l'écran historique"),
    ("historique", ["table_name"],
     "historique(table_name) — filtre par module dans l'écran historique"),
    ("personnel",  ["statut"],
     "personnel(statut) — WHERE statut='ACTIF' sur toutes les listes"),
    ("polyvalence",["operateur_id", "prochaine_evaluation"],
     "polyvalence(operateur_id, prochaine_evaluation) — requêtes évaluations"),
]

tous_ok = True
for tbl, cols, desc in checks:
    if check_index(tbl, cols):
        ok(desc)
    else:
        err(desc)
        tous_ok = False

if tous_ok:
    print(f"\n  {G}{BOLD}Tous les index critiques sont présents.{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 3 — Volume et taille des tables
# ─────────────────────────────────────────────────────────────────────────────
titre("SECTION 3 — Volume et taille des tables")

cur.execute("""
    SELECT
        TABLE_NAME,
        TABLE_ROWS,
        ROUND(DATA_LENGTH  / 1024 / 1024, 2),
        ROUND(INDEX_LENGTH / 1024 / 1024, 2),
        ROUND((DATA_LENGTH + INDEX_LENGTH) / 1024 / 1024, 2)
    FROM information_schema.TABLES
    WHERE TABLE_SCHEMA = DATABASE()
      AND TABLE_NAME IN ('personnel','polyvalence','contrat','historique',
                         'postes','formation','declaration','documents','historique_polyvalence')
    ORDER BY (DATA_LENGTH + INDEX_LENGTH) DESC
""")
rows = cur.fetchall()

SEUILS = {
    "personnel":   5_000,
    "polyvalence": 50_000,
    "historique":  100_000,
    "contrat":     20_000,
}

def color_volume(ligne):
    tbl, nrows = ligne[0], ligne[1] or 0
    seuil = SEUILS.get(tbl)
    if seuil and nrows > seuil:
        return Y
    return ""

print(f"  {DIM}Seuils d'alerte : personnel>5k | polyvalence>50k | historique>100k | contrat>20k{RESET}")
table(["Table", "Lignes (est.)", "Données Mo", "Index Mo", "Total Mo"], rows, color_volume)

for tbl, nrows, *_ in rows:
    nrows = nrows or 0
    seuil = SEUILS.get(tbl)
    if seuil and nrows > seuil:
        if tbl == "historique":
            warn(f"{tbl} ({nrows:,} lignes) → archivage conseillé au-delà de 100k")
        elif tbl == "personnel":
            warn(f"{tbl} ({nrows:,} lignes) → pagination critique, vérifier get_paginated()")
        elif tbl == "polyvalence":
            warn(f"{tbl} ({nrows:,} lignes) → JOINs à surveiller, cache envisageable")
        else:
            warn(f"{tbl} ({nrows:,} lignes) → nettoyage des enregistrements inactifs conseillé")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 4 — EXPLAIN sur les requêtes critiques
# ─────────────────────────────────────────────────────────────────────────────
titre("SECTION 4 — EXPLAIN sur les requêtes critiques")

REQUETES = [
    (
        "get_paginated() — liste personnel (page 1, statut ACTIF)",
        """
        SELECT p.id, p.nom, p.prenom, p.matricule, UPPER(p.statut) AS statut,
               ct.type_contrat,
               COUNT(poly.id) AS nb_postes,
               SUM(CASE WHEN poly.niveau = 1 THEN 1 ELSE 0 END) AS n1,
               SUM(CASE WHEN poly.niveau = 2 THEN 1 ELSE 0 END) AS n2,
               SUM(CASE WHEN poly.niveau = 3 THEN 1 ELSE 0 END) AS n3,
               SUM(CASE WHEN poly.niveau = 4 THEN 1 ELSE 0 END) AS n4
        FROM personnel p
        LEFT JOIN polyvalence poly ON p.id = poly.operateur_id
        LEFT JOIN contrat ct ON ct.personnel_id = p.id AND ct.actif = 1
        WHERE p.statut = 'ACTIF'
        GROUP BY p.id, p.nom, p.prenom, p.matricule, p.numposte, p.statut, ct.type_contrat
        ORDER BY p.nom, p.prenom
        LIMIT 50 OFFSET 0
        """
    ),
    (
        "get_en_retard() — évaluations en retard",
        """
        SELECT p.id, pers.nom, pos.poste_code, p.niveau, p.prochaine_evaluation,
               DATEDIFF(CURDATE(), p.prochaine_evaluation) AS jours_retard
        FROM polyvalence p
        JOIN personnel pers ON p.operateur_id = pers.id
        JOIN postes pos ON p.poste_id = pos.id
        WHERE pers.statut = 'ACTIF'
          AND p.prochaine_evaluation < CURDATE()
        ORDER BY jours_retard DESC
        LIMIT 100
        """
    ),
    (
        "fetch_historique_paginated() — 30 derniers jours",
        """
        SELECT h.id, h.date_time, h.action, h.table_name, h.utilisateur,
               CONCAT(p.prenom, ' ', p.nom) AS op_name
        FROM historique h
        LEFT JOIN personnel p ON h.operateur_id = p.id
        WHERE h.date_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
        ORDER BY h.date_time DESC, h.id DESC
        LIMIT 100 OFFSET 0
        """
    ),
    (
        "COUNT personnel ACTIF — appelé à chaque changement de page",
        """
        SELECT COUNT(DISTINCT p.id) AS total
        FROM personnel p
        WHERE p.statut = 'ACTIF'
        """
    ),
]

COLS_EXPLAIN = ["id", "select_type", "table", "type", "key", "key_len", "rows", "Extra"]

def color_explain(ligne):
    # ligne[3] = type, ligne[7] = Extra
    type_val  = str(ligne[3] or "")
    extra_val = str(ligne[7] or "")
    if type_val == "ALL" and (ligne[2] or "") not in ("", None):
        return R   # scan complet = problème
    if "Using filesort" in extra_val or "Using temporary" in extra_val:
        return Y
    return G

problemes = []

def _parse_explain_with_desc(description, rows):
    """
    Extrait (id, select_type, table, type, key, key_len, rows, Extra)
    depuis un EXPLAIN, compatible MySQL (12 cols) et MariaDB (10 cols).
    """
    cols = [d[0].lower() for d in description]
    def col(name, default=None):
        return cols.index(name) if name in cols else None

    idx = {
        "id":          col("id",          0),
        "select_type": col("select_type", 1),
        "table":       col("table",       2),
        "type":        col("type",        3),
        "key":         col("key",         5),
        "key_len":     col("key_len",     6),
        "rows":        col("rows",        8),
        "extra":       col("extra",       9),
    }
    result = []
    for r in rows:
        result.append(tuple(
            r[v] if v is not None and v < len(r) else None
            for v in idx.values()
        ))
    return result

def _parse_explain(cur, rows):
    return _parse_explain_with_desc(cur.description, rows)


for label, sql in REQUETES:
    print(f"\n  {BOLD}{W}▶  {label}{RESET}")
    cur.execute("EXPLAIN " + sql)
    rows = cur.fetchall()
    desc = cur.description  # capturer avant tout autre execute
    lignes_fmt = _parse_explain_with_desc(desc, rows)
    table(COLS_EXPLAIN, lignes_fmt, color_explain)

    for ligne in lignes_fmt:
        type_val  = str(ligne[3] or "")
        extra_val = str(ligne[7] or "")
        tbl_name  = str(ligne[2] or "")
        if type_val == "ALL" and tbl_name:
            problemes.append(f"Scan complet (ALL) sur '{tbl_name}' dans : {label}")
        if "Using filesort" in extra_val:
            problemes.append(f"Tri en mémoire (filesort) dans : {label}")
        if "Using temporary" in extra_val:
            problemes.append(f"Table temporaire dans : {label}")

if problemes:
    print(f"\n  {R}{BOLD}Problèmes détectés :{RESET}")
    for p in problemes:
        err(p)
else:
    print(f"\n  {G}{BOLD}Aucun problème de plan d'exécution détecté.{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 5 — Comptages réels
# ─────────────────────────────────────────────────────────────────────────────
titre("SECTION 5 — Comptages réels")

comptages = [
    ("personnel ACTIF",           "SELECT COUNT(*) FROM personnel WHERE statut = 'ACTIF'"),
    ("personnel INACTIF",         "SELECT COUNT(*) FROM personnel WHERE statut = 'INACTIF'"),
    ("polyvalence (total)",       "SELECT COUNT(*) FROM polyvalence"),
    ("polyvalence en retard",     "SELECT COUNT(*) FROM polyvalence WHERE prochaine_evaluation < CURDATE()"),
    ("contrat actif",             "SELECT COUNT(*) FROM contrat WHERE actif = 1"),
    ("contrat inactif",           "SELECT COUNT(*) FROM contrat WHERE actif = 0"),
    ("historique (total)",        "SELECT COUNT(*) FROM historique"),
    ("historique (30 derniers j)","SELECT COUNT(*) FROM historique WHERE date_time >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)"),
    ("postes visibles",           "SELECT COUNT(*) FROM postes WHERE visible = 1"),
    ("formation (total)",         "SELECT COUNT(*) FROM formation"),
]

lignes = []
for label, sql in comptages:
    try:
        cur.execute(sql)
        val = cur.fetchone()[0]
    except Exception:
        val = "erreur"
    lignes.append((label, val))

table(["Entité", "Nombre"], lignes)


# ─────────────────────────────────────────────────────────────────────────────
# SECTION 6 — Correctifs si index manquants
# ─────────────────────────────────────────────────────────────────────────────
titre("SECTION 6 — Correctifs disponibles (si Section 2 signale un manquant)")

CORRECTIFS = [
    (
        "contrat(personnel_id, actif)",
        "contrat",
        ["personnel_id", "actif"],
        "ALTER TABLE contrat ADD INDEX idx_contrat_personnel_actif (personnel_id, actif);"
    ),
    (
        "historique(utilisateur)",
        "historique",
        ["utilisateur"],
        "ALTER TABLE historique ADD INDEX idx_historique_utilisateur (utilisateur);"
    ),
    (
        "historique(table_name)",
        "historique",
        ["table_name"],
        "ALTER TABLE historique ADD INDEX idx_historique_table_name (table_name);"
    ),
]

for desc, tbl, cols, sql in CORRECTIFS:
    if not check_index(tbl, cols):
        warn(f"Index manquant : {desc}")
        print(f"    {DIM}→ Commande SQL :{RESET}")
        print(f"    {Y}{sql}{RESET}")


# ─────────────────────────────────────────────────────────────────────────────
# FIN
# ─────────────────────────────────────────────────────────────────────────────
cur.close()
conn.close()

print(f"\n{BOLD}{G}{'─' * 68}{RESET}")
print(f"{BOLD}{G}  Diagnostic terminé.{RESET}")
print(f"{BOLD}{G}{'─' * 68}{RESET}\n")
