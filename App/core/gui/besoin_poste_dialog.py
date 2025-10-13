from PyQt5 import QtWidgets, QtCore, QtGui

class BesoinPosteDialog(QtWidgets.QDialog):
    def __init__(self, parent=None, titre_poste: str = ""):
        super().__init__(parent)
        self.setWindowTitle("Besoin du poste")
        self.setModal(True)
        self.resize(380, 160)

        label_titre = QtWidgets.QLabel("Intitulé du poste :")
        self.readonly_titre = QtWidgets.QLineEdit(titre_poste)
        self.readonly_titre.setReadOnly(True)

        label_besoin = QtWidgets.QLabel("Besoins pour ce poste (nombre) :")
        self.input_besoin = QtWidgets.QLineEdit()
        self.input_besoin.setPlaceholderText("Ex : 3")
        self.input_besoin.setValidator(QtGui.QIntValidator(0, 999, self))

        btn_cancel = QtWidgets.QPushButton("Annuler")
        btn_ok = QtWidgets.QPushButton("Valider")
        btn_ok.setDefault(True)
        btn_ok.clicked.connect(self._on_ok)
        btn_cancel.clicked.connect(self.reject)

        form = QtWidgets.QVBoxLayout(self)
        form.addWidget(label_titre)
        form.addWidget(self.readonly_titre)
        form.addSpacing(6)
        form.addWidget(label_besoin)
        form.addWidget(self.input_besoin)

        row_btn = QtWidgets.QHBoxLayout()
        row_btn.addStretch(1)
        row_btn.addWidget(btn_cancel)
        row_btn.addWidget(btn_ok)
        form.addLayout(row_btn)

    def _on_ok(self):
        # Besoin obligatoire en création
        txt = (self.input_besoin.text() or "").strip()
        if txt == "":
            QtWidgets.QMessageBox.warning(self, "Champ requis", "Merci de saisir un nombre (0 ou plus).")
            return
        self.accept()

    def get_besoin_int_or_none(self):
        txt = (self.input_besoin.text() or "").strip()
        if txt == "":
            return None
        return int(txt)
