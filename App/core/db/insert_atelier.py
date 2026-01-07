# -*- coding: utf-8 -*-
"""
Script d'affectation des postes aux ateliers.
Utilise le pool de connexions centralisé.
"""

from core.db.configbd import DatabaseConnection

# 🔹 Liste des ateliers et leurs postes associés
affectations = {
    5: [506, 507, 510, 514, 515, 560, 912],  # Atelier 5
    14: [1401, 1402, 1404, 1405, 1412],  # Atelier 14
    11: [1100, 1121, 1103, 1101],  #  Atelier 11
    10: [1007, 1026], # Atelier 10
    8: [830, 930], # Atelier 8
    9: [942, 941, 940, 924, 923, 920, 906, 903, 902, 901, 900, 910] # Atelier 9
}

# ✅ Utilisation du context manager DatabaseConnection
with DatabaseConnection() as conn:
    cursor = conn.cursor()

    # 🔹 Création des ateliers s'ils n'existent pas encore
    for atelier_id in affectations.keys():
        cursor.execute("INSERT INTO atelier (id, nom) VALUES (%s, %s) ON DUPLICATE KEY UPDATE nom = nom",
                       (atelier_id, f"Atelier {atelier_id}"))
        print(f"✅ Atelier {atelier_id} ajouté/vérifié")

    # 🔹 Affectation des postes aux ateliers
    for atelier_id, postes in affectations.items():
        cursor.executemany("UPDATE postes SET atelier_id = %s WHERE id = %s",
                           [(atelier_id, poste) for poste in postes])
        print(f"🔄 {len(postes)} postes affectés à l'atelier {atelier_id}")

    # ✅ Plus besoin de conn.commit() - le context manager le fait automatiquement
    print("\n✅ Affectations mises à jour avec succès !\n")

    # 🔹 Vérification de l'affectation
    cursor.execute("""
        SELECT p.id, p.poste_code, a.nom
        FROM postes p
        LEFT JOIN atelier a ON p.atelier_id = a.id
        ORDER BY a.nom, p.id
    """)

    rows = cursor.fetchall()

    print("📌 Résumé des affectations :")
    for row in rows:
        print(f"Poste {row[0]:<4} | {row[1]:<20} -> {row[2]}")

    cursor.close()
# ✅ La connexion est automatiquement fermée et rendue au pool
