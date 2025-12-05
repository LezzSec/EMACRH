import mysql.connector
from mysql.connector import Error
import re
from datetime import datetime

class CharsetFixer:
    def __init__(self, host, user, password, database):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None

        # Dictionnaire de correction des caractères mal encodés
        # NOTE: clés dupliquées supprimées / corrigées + guillemets/apostrophes invalides fixés
        self.encoding_fixes = {
            # Caractères accentués courants (UTF-8 lu comme Latin-1)
            'Ã©': 'é', 'Ã¨': 'è', 'Ãª': 'ê', 'Ã«': 'ë',
            'Ã ': 'à', 'Ã¢': 'â', 'Ã¤': 'ä',
            'Ã®': 'î', 'Ã¯': 'ï',
            'Ã´': 'ô', 'Ã¶': 'ö',
            'Ã¹': 'ù', 'Ã»': 'û', 'Ã¼': 'ü',
            'Ã§': 'ç',
            'Ã±': 'ñ',

            # Majuscules accentuées
            'Ã‰': 'É', 'Ãˆ': 'È', 'ÃŠ': 'Ê', 'Ã‹': 'Ë',
            'Ã€': 'À', 'Ã‚': 'Â', 'Ã„': 'Ä',
            'ÃŽ': 'Î', 'Ã': 'Ï',
            'Ã”': 'Ô', 'Ã–': 'Ö',
            'Ã™': 'Ù', 'Ã›': 'Û', 'Ãœ': 'Ü',
            'Ã‡': 'Ç',
            'Ã‘': 'Ñ',

            # Caractères spéciaux Windows-1252 vers UTF-8
            'â€™': "'",
            'â€˜': "'",
            'â€œ': '"',
            'â€': '"',
            'â€“': '–',
            'â€”': '—',
            'â€¢': '•',
            'â€¦': '…',

            # Corrections spécifiques observées dans votre dump
            'Â®': '®',
            'Âº': 'º',
            'Â½': '½',
            'Â»': '»',
            'Â¿': '¿',
            'Â¯': '¯',
            'Â¡': '¡',

            # Suppression des caractères de remplacement
            '�': '',
        }

    def connect(self):
        """Établit la connexion à la base de données avec charset UTF-8"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                collation='utf8mb4_general_ci',
                use_unicode=True
            )
            if self.connection.is_connected():
                print("✓ Connexion à la base de données réussie")
                # Force UTF-8 pour la session
                cursor = self.connection.cursor()
                cursor.execute("SET NAMES utf8mb4")
                cursor.execute("SET CHARACTER SET utf8mb4")
                cursor.execute("SET character_set_connection=utf8mb4")
                cursor.close()
                return True
        except Error as e:
            print(f"✗ Erreur de connexion: {e}")
            return False

    def disconnect(self):
        """Ferme la connexion"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("✓ Connexion fermée")

    def backup_table(self, table_name):
        """Crée une sauvegarde de la table"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            backup_name = f"{table_name}_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            cursor.execute(f"CREATE TABLE {backup_name} LIKE {table_name}")
            cursor.execute(f"INSERT INTO {backup_name} SELECT * FROM {table_name}")
            self.connection.commit()

            print(f"✓ Sauvegarde créée: {backup_name}")
            return backup_name
        except Error as e:
            print(f"✗ Erreur lors de la sauvegarde: {e}")
            return None
        finally:
            if cursor is not None:
                cursor.close()

    def fix_text(self, text):
        """Corrige l'encodage d'un texte"""
        if not text or not isinstance(text, str):
            return text

        original = text
        fixed = text

        # Applique les corrections d'encodage
        for wrong, correct in self.encoding_fixes.items():
            fixed = fixed.replace(wrong, correct)

        # Détecte et corrige les séquences UTF-8 mal interprétées
        try:
            # Tente de détecter si c'est du Latin-1 mal encodé
            if fixed.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore') != fixed:
                fixed = fixed.encode('latin-1', errors='ignore').decode('utf-8', errors='ignore')
        except Exception:
            pass

        # Nettoie les espaces
        fixed = re.sub(r'\s+', ' ', fixed).strip()

        return fixed if fixed != original else text

    def detect_encoding_issues(self, table_name, columns):
        """Détecte les problèmes d'encodage dans une table"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)

            issues = []
            patterns = [
            r'Ã[\u0080-\u00BF]',
            r'â€',
            r'Â[®º½»¿¯¡]',
            r'[�?]{2,}',
            r'[®Ø¤*@]',          # AJOUT: caractères “moches” vus chez toi
        ]

            for column in columns:
                query = f"SELECT id, {column} FROM {table_name} WHERE {column} IS NOT NULL"
                cursor.execute(query)
                rows = cursor.fetchall()

                for row in rows:
                    text = row.get(column)
                    if text and isinstance(text, str):
                        for pattern in patterns:
                            if re.search(pattern, text):
                                issues.append({
                                    'table': table_name,
                                    'column': column,
                                    'id': row['id'],
                                    'original': text,
                                    'fixed': self.fix_text(text)
                                })
                                break

            return issues
        except Error as e:
            print(f"✗ Erreur lors de la détection: {e}")
            return []
        finally:
            if cursor is not None:
                cursor.close()

    def fix_table(self, table_name, columns):
        """Corrige l'encodage d'une table"""
        cursor = None
        update_cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            update_cursor = self.connection.cursor()

            fixed_count = 0

            for column in columns:
                query = f"SELECT id, {column} FROM {table_name} WHERE {column} IS NOT NULL"
                cursor.execute(query)
                rows = cursor.fetchall()

                for row in rows:
                    original = row.get(column)
                    if original and isinstance(original, str):
                        fixed = self.fix_text(original)

                        if fixed != original:
                            update_query = f"UPDATE {table_name} SET {column} = %s WHERE id = %s"
                            update_cursor.execute(update_query, (fixed, row['id']))
                            fixed_count += 1
                            print(f"  ✓ {table_name}.{column} (ID {row['id']}): '{original}' → '{fixed}'")

            self.connection.commit()
            return fixed_count
        except Error as e:
            print(f"✗ Erreur lors de la correction: {e}")
            self.connection.rollback()
            return 0
        finally:
            if update_cursor is not None:
                update_cursor.close()
            if cursor is not None:
                cursor.close()

    def check_table_charset(self, table_name):
        """Vérifie le charset d'une table"""
        cursor = None
        try:
            cursor = self.connection.cursor(dictionary=True)
            query = """
                SELECT TABLE_NAME, TABLE_COLLATION
                FROM information_schema.TABLES
                WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
            """
            cursor.execute(query, (self.database, table_name))
            result = cursor.fetchone()

            if result:
                print(f"\n📋 Table {table_name}:")
                print(f"   Collation: {result['TABLE_COLLATION']}")

                # Vérifie les colonnes
                cursor.execute("""
                    SELECT COLUMN_NAME, CHARACTER_SET_NAME, COLLATION_NAME
                    FROM information_schema.COLUMNS
                    WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
                    AND CHARACTER_SET_NAME IS NOT NULL
                """, (self.database, table_name))

                columns = cursor.fetchall()
                if columns:
                    print("   Colonnes texte:")
                    for col in columns:
                        print(f"     • {col['COLUMN_NAME']}: {col['CHARACTER_SET_NAME']} / {col['COLLATION_NAME']}")
        except Error as e:
            print(f"✗ Erreur: {e}")
        finally:
            if cursor is not None:
                cursor.close()

    def convert_table_to_utf8mb4(self, table_name):
        """Convertit une table en UTF-8"""
        cursor = None
        try:
            cursor = self.connection.cursor()
            print(f"\n🔄 Conversion de {table_name} en UTF-8...")

            cursor.execute(
                f"ALTER TABLE {table_name} "
                f"CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
            )

            self.connection.commit()
            print(f"✓ Table {table_name} convertie en UTF-8")
            return True
        except Error as e:
            print(f"✗ Erreur lors de la conversion: {e}")
            return False
        finally:
            if cursor is not None:
                cursor.close()

    def generate_report(self):
        """Génère un rapport sur les problèmes d'encodage"""
        print("\n" + "="*80)
        print("RAPPORT D'ENCODAGE")
        print("="*80)

        tables_to_check = {
            'personnel': ['nom', 'prenom', 'statut', 'numposte'],
            'services': ['nom_service', 'description'],
            'postes': ['poste_code'],
            'atelier': ['nom'],
            'contrat': ['type_contrat', 'categorie', 'emploi', 'nom_tuteur', 'prenom_tuteur'],
            'formation': ['intitule', 'organisme', 'statut', 'commentaire'],
            'declaration': ['type_declaration', 'motif']
        }

        total_issues = 0

        for table, columns in tables_to_check.items():
            self.check_table_charset(table)

            print(f"\n🔍 Analyse de {table}...")
            issues = self.detect_encoding_issues(table, columns)

            if issues:
                print(f"⚠ {len(issues)} problèmes détectés:")
                for issue in issues[:5]:
                    print(f"  • ID {issue['id']}, {issue['column']}: '{issue['original']}' → '{issue['fixed']}'")
                if len(issues) > 5:
                    print(f"  ... et {len(issues) - 5} autres")
                total_issues += len(issues)
            else:
                print("✓ Aucun problème détecté")

        print(f"\n📊 Total: {total_issues} problèmes d'encodage trouvés")
        print("="*80)

        return total_issues


def main():
    """Fonction principale"""
    print("="*80)
    print("CORRECTION D'ENCODAGE UTF-8")
    print("="*80)

    # Configuration pour connexion locale
    config = {
        'host': 'localhost',
        'user': 'root',
        'password': 'emacViodos$13',  # Laissez vide si pas de mot de passe root
        'database': 'emac_db'
    }

    fixer = CharsetFixer(**config)

    if not fixer.connect():
        return

    try:
        # 1. Rapport initial
        print("\n📊 Analyse de l'encodage...")
        total_issues = fixer.generate_report()

        if total_issues == 0:
            print("\n✅ Aucun problème d'encodage détecté!")
            return

        # 2. Proposition de correction
        response = input(f"\n❓ {total_issues} problèmes détectés. Voulez-vous les corriger? (oui/non): ")

        if response.lower() not in ['oui', 'o', 'yes', 'y']:
            print("⏭ Correction annulée")
            return

        # 3. Sauvegarde
        print("\n💾 Création des sauvegardes...")
        tables_to_fix = {
            'personnel': ['nom', 'prenom', 'statut', 'numposte'],
            'services': ['nom_service', 'description'],
            'postes': ['poste_code'],
            'atelier': ['nom'],
            'contrat': ['type_contrat', 'categorie', 'emploi', 'nom_tuteur', 'prenom_tuteur'],
            'formation': ['intitule', 'organisme', 'statut', 'commentaire'],
            'declaration': ['type_declaration', 'motif']
        }

        for table in tables_to_fix.keys():
            fixer.backup_table(table)

        # 4. Correction
        print("\n🔧 Correction en cours...")
        total_fixed = 0

        for table, columns in tables_to_fix.items():
            print(f"\n📝 Correction de {table}...")
            fixed = fixer.fix_table(table, columns)
            total_fixed += fixed
            print(f"  ✓ {fixed} entrées corrigées")

        # 5. Option de conversion des tables
        response = input("\n❓ Voulez-vous aussi convertir les tables en UTF-8 natif? (oui/non): ")
        if response.lower() in ['oui', 'o', 'yes', 'y']:
            for table in tables_to_fix.keys():
                fixer.convert_table_to_utf8mb4(table)

        # 6. Rapport final
        print("\n📊 Vérification finale...")
        fixer.generate_report()

        print(f"\n✅ Correction terminée! {total_fixed} entrées corrigées")

    except Exception as e:
        print(f"\n✗ Erreur inattendue: {e}")
    finally:
        fixer.disconnect()


if __name__ == "__main__":
    main()
