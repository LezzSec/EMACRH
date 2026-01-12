# -*- coding: utf-8 -*-
"""
Démonstration du système de monitoring de performance.
Montre comment intégrer le monitoring dans le code EMAC.
"""

import sys
import os
import time

# Ajouter le chemin App au PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.utils.performance_monitor import (
    monitor_performance,
    monitor_query,
    monitor_dialog,
    monitor_login_time,
    measure_query_time,
    measure_dialog_time,
    PerformanceTimer,
    print_performance_report,
    export_performance_stats
)


# ===========================
# Exemple 1: Monitorer le login
# ===========================

@monitor_login_time
def authenticate_user(username, password):
    """Authentifie un utilisateur (exemple)"""
    print(f"  Authenticating {username}...")

    # Simuler requête DB (50-600ms)
    time.sleep(0.05 + (hash(username) % 550) / 1000)

    print(f"  ✅ User {username} authenticated")
    return {'id': 1, 'username': username, 'role': 'admin'}


# ===========================
# Exemple 2: Monitorer une requête DB
# ===========================

@monitor_query('Load Personnel')
def load_personnel():
    """Charge le personnel depuis la DB (exemple)"""
    print("  Loading personnel...")

    # Simuler requête (20-150ms)
    time.sleep(0.02 + (hash('personnel') % 130) / 1000)

    print("  ✅ Personnel loaded")
    return [{'id': i, 'nom': f'User{i}'} for i in range(100)]


# ===========================
# Exemple 3: Monitorer un dialog
# ===========================

@monitor_dialog('Personnel Dialog')
def open_personnel_dialog():
    """Ouvre le dialog de gestion personnel (exemple)"""
    print("  Opening personnel dialog...")

    # Simuler création dialog (100-400ms)
    time.sleep(0.1 + (hash('dialog') % 300) / 1000)

    print("  ✅ Dialog opened")


# ===========================
# Exemple 4: Context manager pour requêtes
# ===========================

def complex_query_example():
    """Exemple avec context manager"""
    print("Running complex query...")

    with measure_query_time('Load Polyvalence'):
        # Simuler requête complexe
        time.sleep(0.08)

    print("✅ Complex query completed")


# ===========================
# Exemple 5: Mesure manuelle
# ===========================

def manual_measurement_example():
    """Exemple de mesure manuelle avec PerformanceTimer"""
    print("Running manual measurement...")

    with PerformanceTimer('Export CSV', category='export'):
        # Simuler export (1-3s)
        time.sleep(1.5)

    print("✅ Export completed")


# ===========================
# Exemple 6: Opération lente (déclenchera alerte)
# ===========================

@monitor_query('Slow Query')
def slow_query():
    """Requête intentionnellement lente pour tester l'alerte"""
    print("  Running slow query...")

    # Simuler requête lente (> 100ms threshold)
    time.sleep(0.25)  # 250ms → alerte !

    print("  ✅ Slow query completed")


# ===========================
# Main
# ===========================

def main():
    print("\n" + "=" * 80)
    print("🔍 DÉMONSTRATION DU MONITORING DE PERFORMANCE")
    print("=" * 80)
    print()

    # Exemple 1: Login
    print("1️⃣ Test Login (threshold: 500ms)")
    print("-" * 80)
    authenticate_user('john.doe', 'password123')
    authenticate_user('jane.smith', 'password456')
    print()

    # Exemple 2: Requêtes DB
    print("2️⃣ Test Requêtes DB (threshold: 100ms)")
    print("-" * 80)
    load_personnel()
    load_personnel()  # 2ème fois pour voir la variation
    print()

    # Exemple 3: Dialogs
    print("3️⃣ Test Ouverture Dialog (threshold: 300ms)")
    print("-" * 80)
    open_personnel_dialog()
    print()

    # Exemple 4: Context manager
    print("4️⃣ Test Context Manager")
    print("-" * 80)
    complex_query_example()
    print()

    # Exemple 5: Mesure manuelle
    print("5️⃣ Test Mesure Manuelle (export)")
    print("-" * 80)
    manual_measurement_example()
    print()

    # Exemple 6: Opération lente (alerte)
    print("6️⃣ Test Opération Lente (doit alerter)")
    print("-" * 80)
    slow_query()
    print()

    # Rapport final
    print_performance_report()

    # Export CSV
    print("📊 Export des statistiques...")
    export_performance_stats('demo_performance_stats.csv')
    print()


if __name__ == '__main__':
    main()
