"""
Test des KPI cards pour vérifier le nouveau design
"""
import sys
from PyQt5.QtWidgets import QApplication, QDialog, QVBoxLayout, QHBoxLayout, QWidget, QLabel
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

def create_kpi_card(icon, title, value, subtitle, color, bg_color):
    """Crée une KPI card moderne avec layout vertical"""
    print(f"Création card: {title}")
    # Container widget pour contrôler la taille
    container = QWidget()
    container.setFixedSize(220, 110)
    print(f"Taille fixée à 220x110")
    container.setStyleSheet(f"""
        QWidget {{
            background: {bg_color};
            border-left: 4px solid {color};
            border-radius: 10px;
        }}
    """)

    # Layout vertical centré
    main_layout = QVBoxLayout(container)
    main_layout.setSpacing(4)
    main_layout.setContentsMargins(16, 12, 16, 12)

    # En-tête: icône + titre sur la même ligne
    header_layout = QHBoxLayout()
    header_layout.setSpacing(8)

    # Icône
    icon_label = QLabel(icon)
    icon_label.setFont(QFont("Segoe UI", 20))
    header_layout.addWidget(icon_label)

    # Titre
    title_label = QLabel(title)
    title_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
    title_label.setStyleSheet(f"color: {color};")
    title_label.setWordWrap(False)
    header_layout.addWidget(title_label)

    header_layout.addStretch()
    main_layout.addLayout(header_layout)

    main_layout.addSpacing(4)

    # Valeur principale - Grande et centrée
    value_label = QLabel(value)
    value_label.setObjectName("value_label")
    value_label.setFont(QFont("Segoe UI", 36, QFont.Bold))
    value_label.setStyleSheet(f"color: {color};")
    value_label.setAlignment(Qt.AlignCenter)
    main_layout.addWidget(value_label)

    main_layout.addSpacing(2)

    # Sous-titre centré
    if subtitle:
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet("color: #64748b; font-size: 9px;")
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)

    main_layout.addStretch()

    return container


class TestDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test KPI Cards - Nouveau Design")
        self.setGeometry(100, 100, 800, 200)

        layout = QVBoxLayout(self)

        # KPI Cards
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)
        kpi_layout.addStretch()

        card1 = create_kpi_card("📋", "Contrats Actifs", "42", "Total en cours", "#3b82f6", "#eff6ff")
        kpi_layout.addWidget(card1)

        card2 = create_kpi_card("⏰", "À Renouveler", "7", "Dans les 30 jours", "#f59e0b", "#fef3c7")
        kpi_layout.addWidget(card2)

        card3 = create_kpi_card("⚠️", "Expirés", "3", "Contrats terminés", "#dc2626", "#fef2f2")
        kpi_layout.addWidget(card3)

        kpi_layout.addStretch()

        layout.addLayout(kpi_layout)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = TestDialog()
    dialog.show()
    sys.exit(app.exec_())
