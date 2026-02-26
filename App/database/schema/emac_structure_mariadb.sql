/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.14-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: emac_db
-- ------------------------------------------------------
-- Server version	10.11.14-MariaDB-0+deb12u2

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `atelier`
--

DROP TABLE IF EXISTS `atelier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `atelier` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_atelier_nom` (`nom`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `atelier`
--

LOCK TABLES `atelier` WRITE;
/*!40000 ALTER TABLE `atelier` DISABLE KEYS */;
INSERT INTO `atelier` VALUES
(10,'Atelier 10'),
(11,'Atelier 11'),
(14,'Atelier 14'),
(5,'Atelier 5'),
(8,'Atelier 8'),
(9,'Atelier 9');
/*!40000 ALTER TABLE `atelier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `batch_operation_details`
--

DROP TABLE IF EXISTS `batch_operation_details`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `batch_operation_details` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `batch_id` int(11) NOT NULL COMMENT 'Référence vers batch_operations',
  `personnel_id` int(11) NOT NULL COMMENT 'Personnel concerné',
  `status` enum('SUCCES','ERREUR','IGNORE') DEFAULT 'SUCCES',
  `error_message` text DEFAULT NULL COMMENT 'Message d''erreur si échec',
  `record_id` int(11) DEFAULT NULL COMMENT 'ID de l''enregistrement créé (formation_id, absence_id, etc.)',
  `processed_at` datetime DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_detail_batch` (`batch_id`),
  KEY `idx_detail_personnel` (`personnel_id`),
  KEY `idx_detail_status` (`status`),
  CONSTRAINT `batch_operation_details_ibfk_1` FOREIGN KEY (`batch_id`) REFERENCES `batch_operations` (`id`) ON DELETE CASCADE,
  CONSTRAINT `batch_operation_details_ibfk_2` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Détails par personnel pour chaque opération batch';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `batch_operation_details`
--

LOCK TABLES `batch_operation_details` WRITE;
/*!40000 ALTER TABLE `batch_operation_details` DISABLE KEYS */;
INSERT INTO `batch_operation_details` VALUES
(4,5,417,'SUCCES',NULL,11,'2026-02-09 11:42:25'),
(5,5,416,'SUCCES',NULL,12,'2026-02-09 11:42:25'),
(6,6,417,'SUCCES',NULL,13,'2026-02-09 11:48:08'),
(7,6,416,'SUCCES',NULL,14,'2026-02-09 11:48:08'),
(8,7,417,'SUCCES',NULL,15,'2026-02-09 12:01:55'),
(9,7,416,'SUCCES',NULL,16,'2026-02-09 12:01:55'),
(10,8,417,'SUCCES',NULL,17,'2026-02-09 13:27:32'),
(11,8,416,'SUCCES',NULL,18,'2026-02-09 13:27:33');
/*!40000 ALTER TABLE `batch_operation_details` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `batch_operations`
--

DROP TABLE IF EXISTS `batch_operations`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `batch_operations` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operation_type` enum('ABSENCE','FORMATION','VISITE_MEDICALE','DOCUMENT') NOT NULL,
  `description` text DEFAULT NULL COMMENT 'Description de l''opération (ex: nom de la formation)',
  `nb_personnel` int(11) DEFAULT 0 COMMENT 'Nombre de personnel ciblé',
  `nb_success` int(11) DEFAULT 0 COMMENT 'Nombre de succès',
  `nb_errors` int(11) DEFAULT 0 COMMENT 'Nombre d''erreurs',
  `created_by` varchar(100) DEFAULT NULL COMMENT 'Utilisateur ayant lancé l''opération',
  `created_at` datetime DEFAULT current_timestamp(),
  `completed_at` datetime DEFAULT NULL COMMENT 'Date de fin de l''opération',
  `status` enum('EN_COURS','TERMINE','ERREUR','ANNULE') DEFAULT 'EN_COURS',
  PRIMARY KEY (`id`),
  KEY `idx_batch_status` (`status`),
  KEY `idx_batch_type` (`operation_type`),
  KEY `idx_batch_created` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Suivi des opérations en masse (assignation formations, absences, etc.)';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `batch_operations`
--

LOCK TABLES `batch_operations` WRITE;
/*!40000 ALTER TABLE `batch_operations` DISABLE KEYS */;
INSERT INTO `batch_operations` VALUES
(1,'FORMATION','Formation caces',3,0,0,NULL,'2026-02-06 11:06:27',NULL,'EN_COURS'),
(2,'FORMATION','Formation CACES',3,0,0,NULL,'2026-02-09 08:52:19',NULL,'EN_COURS'),
(3,'FORMATION','Formation CACES',3,0,0,NULL,'2026-02-09 08:52:30',NULL,'EN_COURS'),
(4,'FORMATION','Formation',3,3,0,NULL,'2026-02-09 08:57:45','2026-02-09 08:57:45','TERMINE'),
(5,'FORMATION','Formation CACES',2,2,0,NULL,'2026-02-09 11:42:25','2026-02-09 11:42:25','TERMINE'),
(6,'FORMATION','Formation sécurité',2,2,0,NULL,'2026-02-09 11:48:08','2026-02-09 11:48:08','TERMINE'),
(7,'FORMATION','Formation TEST',2,2,0,NULL,'2026-02-09 12:01:55','2026-02-09 12:01:55','TERMINE'),
(8,'FORMATION','Formation',2,2,0,NULL,'2026-02-09 13:27:32','2026-02-09 13:27:33','TERMINE');
/*!40000 ALTER TABLE `batch_operations` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories_documents`
--

DROP TABLE IF EXISTS `categories_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories_documents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  `couleur` varchar(7) DEFAULT '#3b82f6',
  `exige_date_expiration` tinyint(1) DEFAULT 0,
  `ordre_affichage` int(11) DEFAULT 0,
  `date_creation` timestamp NULL DEFAULT current_timestamp(),
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_categorie_nom` (`nom`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories_documents`
--

LOCK TABLES `categories_documents` WRITE;
/*!40000 ALTER TABLE `categories_documents` DISABLE KEYS */;
INSERT INTO `categories_documents` VALUES
(1,'Contrats de travail','Contrats CDI, CDD, avenants','#10b981',1,1,'2025-11-28 10:45:14','2025-11-28 10:45:14'),
(2,'Certificats médicaux','Visites m├®dicales, aptitudes, RQTH','#ef4444',1,2,'2025-11-28 10:45:14','2026-01-14 08:47:23'),
(3,'Diplômes et formations','Dipl├┤mes, certificats de formation, habilitations','#8b5cf6',0,3,'2025-11-28 10:45:14','2026-01-14 08:47:23'),
(4,'Autorisations de travail','Titres de s├®jour, autorisations de travail pour ├®trangers','#f59e0b',1,4,'2025-11-28 10:45:14','2025-11-28 10:45:14'),
(5,'Pièces d\'identité','CNI, passeport, permis de conduire','#06b6d4',1,5,'2025-11-28 10:45:14','2026-01-14 08:47:23'),
(6,'Attestations diverses','Attestations employeur, certificats de travail','#6366f1',0,6,'2025-11-28 10:45:14','2025-11-28 10:45:14'),
(7,'Documents administratifs','Fiches de paie, relev├®s, justificatifs','#64748b',0,7,'2025-11-28 10:45:14','2025-11-28 10:45:14'),
(8,'Autres','Documents non class├®s','#9ca3af',0,99,'2025-11-28 10:45:14','2025-11-28 10:45:14');
/*!40000 ALTER TABLE `categories_documents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `competences_catalogue`
--

DROP TABLE IF EXISTS `competences_catalogue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `competences_catalogue` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(50) NOT NULL,
  `libelle` varchar(255) NOT NULL,
  `description` text DEFAULT NULL,
  `categorie` varchar(100) DEFAULT NULL,
  `duree_validite_mois` int(11) DEFAULT NULL,
  `actif` tinyint(1) DEFAULT 1,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_competence_code` (`code`),
  KEY `idx_competence_categorie` (`categorie`),
  KEY `idx_competence_actif` (`actif`)
) ENGINE=InnoDB AUTO_INCREMENT=7 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `competences_catalogue`
--

LOCK TABLES `competences_catalogue` WRITE;
/*!40000 ALTER TABLE `competences_catalogue` DISABLE KEYS */;
INSERT INTO `competences_catalogue` VALUES
(1,'MGT_LEADER','Leadership d\'équipe',NULL,'Managérial',NULL,1,'2026-02-02 14:12:56','2026-02-02 14:12:56'),
(2,'MGT_EVAL','Conduite d\'entretiens',NULL,'Managérial',NULL,1,'2026-02-02 14:12:56','2026-02-02 14:12:56'),
(3,'SEC_INCENDIE','Équipier de première intervention',NULL,'Sécurité',24,1,'2026-02-02 14:12:56','2026-02-02 14:12:56'),
(4,'SEC_SST','Sauveteur Secouriste du Travail',NULL,'Sécurité',24,1,'2026-02-02 14:12:56','2026-02-02 14:12:56'),
(5,'HAB_ELEC','Habilitation électrique',NULL,'Habilitation',36,1,'2026-02-02 14:12:56','2026-02-02 14:12:56'),
(6,'HAB_CACES','CACES cariste',NULL,'Habilitation',60,1,'2026-02-02 14:12:56','2026-02-02 14:12:56');
/*!40000 ALTER TABLE `competences_catalogue` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contrat`
--

DROP TABLE IF EXISTS `contrat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `contrat` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `personnel_id` int(11) NOT NULL,
  `type_contrat` enum('Stagiaire','Apprentissage','Intérimaire','Mise à disposition GE','Etranger hors UE','Temps partiel','CDI','CDD','CIFRE','Avenant contrat') NOT NULL,
  `type_cdd` enum('Remplacement','Accroissement','Saisonnier','Usage') DEFAULT NULL COMMENT 'Type de CDD (si type_contrat = CDD)',
  `motif` text DEFAULT NULL COMMENT 'Motif du contrat ou du CDD',
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `date_sortie` date DEFAULT NULL COMMENT 'Date de sortie effective',
  `date_embauche_cdi` date DEFAULT NULL COMMENT 'Date embauche CDI (passage CDD -> CDI)',
  `motif_sortie` varchar(100) DEFAULT NULL COMMENT 'Motif de sortie',
  `etp` decimal(3,2) DEFAULT 1.00 COMMENT 'Équivalent Temps Plein',
  `categorie` enum('Ouvrier','Ouvrier qualifié','Employé','Agent de maîtrise','Cadre') DEFAULT NULL,
  `typologie_statut_horaire` enum('Cadre forfait jour','Cadre décompte horaire','Non-cadre','Temps partiel') DEFAULT NULL,
  `echelon` varchar(50) DEFAULT NULL,
  `niveau` varchar(20) DEFAULT NULL COMMENT 'Niveau dans la grille',
  `coefficient` int(11) DEFAULT NULL COMMENT 'Coefficient salarial',
  `emploi` varchar(100) DEFAULT NULL,
  `salaire` decimal(10,2) DEFAULT NULL,
  `salaire_annuel` decimal(12,2) DEFAULT NULL COMMENT 'Salaire brut annuel',
  `type_prime` varchar(100) DEFAULT NULL COMMENT 'Type de prime',
  `prime_mensuelle` decimal(10,2) DEFAULT NULL COMMENT 'Montant prime mensuel brut',
  `prime_annuelle` decimal(12,2) DEFAULT NULL COMMENT 'Total prime annuel brut',
  `actif` tinyint(1) DEFAULT 1,
  `nom_tuteur` varchar(100) DEFAULT NULL,
  `prenom_tuteur` varchar(100) DEFAULT NULL,
  `ecole` varchar(255) DEFAULT NULL,
  `nom_ett` varchar(255) DEFAULT NULL,
  `adresse_ett` text DEFAULT NULL,
  `nom_ge` varchar(255) DEFAULT NULL,
  `adresse_ge` text DEFAULT NULL,
  `date_autorisation_travail` date DEFAULT NULL,
  `date_demande_autorisation` date DEFAULT NULL,
  `type_titre_autorisation` varchar(255) DEFAULT NULL,
  `numero_autorisation_travail` varchar(50) DEFAULT NULL,
  `date_limite_autorisation` date DEFAULT NULL,
  `date_creation` timestamp NULL DEFAULT current_timestamp(),
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_personnel` (`personnel_id`),
  KEY `idx_type_contrat` (`type_contrat`),
  KEY `idx_actif` (`actif`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_contrat_dates_actif` (`date_debut`,`date_fin`,`actif`),
  CONSTRAINT `fk_contrat_personnel` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contrat`
--

LOCK TABLES `contrat` WRITE;
/*!40000 ALTER TABLE `contrat` DISABLE KEYS */;
INSERT INTO `contrat` VALUES
(6,2,'CDD',NULL,NULL,'2026-02-09','2026-08-08',NULL,NULL,NULL,1.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2026-02-09 15:19:01','2026-02-09 15:19:01'),
(7,2,'CDD',NULL,NULL,'2026-02-09','2026-08-08',NULL,NULL,NULL,1.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2026-02-09 15:20:08','2026-02-09 15:20:08'),
(8,2,'CDD',NULL,NULL,'2026-02-09','2026-08-08',NULL,NULL,NULL,1.00,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,0,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,'2026-02-09 15:30:32','2026-02-09 15:30:32');
/*!40000 ALTER TABLE `contrat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `declaration`
--

DROP TABLE IF EXISTS `declaration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `declaration` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `type_declaration` enum('CongePaye','RTT','SansSolde','Maladie','AccidentTravail','AccidentTrajet','ArretTravail','CongeNaissance','Formation','Autorisation','Autre') NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `motif` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  CONSTRAINT `fk_absences_conges_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `declaration`
--

LOCK TABLES `declaration` WRITE;
/*!40000 ALTER TABLE `declaration` DISABLE KEYS */;
/*!40000 ALTER TABLE `declaration` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `demande_absence`
--

DROP TABLE IF EXISTS `demande_absence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `demande_absence` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `personnel_id` int(11) NOT NULL,
  `type_absence_id` int(11) NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `demi_journee_debut` enum('MATIN','APRES_MIDI','JOURNEE') DEFAULT 'JOURNEE',
  `demi_journee_fin` enum('MATIN','APRES_MIDI','JOURNEE') DEFAULT 'JOURNEE',
  `nb_jours` decimal(4,2) NOT NULL COMMENT 'Nombre de jours ouvrés',
  `motif` text DEFAULT NULL,
  `statut` enum('EN_ATTENTE','VALIDEE','REFUSEE','ANNULEE') DEFAULT 'EN_ATTENTE',
  `validateur_id` int(11) DEFAULT NULL COMMENT 'ID du personnel qui a validé/refusé',
  `date_validation` datetime DEFAULT NULL,
  `commentaire_validation` text DEFAULT NULL,
  `date_creation` timestamp NULL DEFAULT current_timestamp(),
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `type_absence_id` (`type_absence_id`),
  KEY `validateur_id` (`validateur_id`),
  KEY `idx_personnel` (`personnel_id`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_statut` (`statut`),
  CONSTRAINT `demande_absence_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `demande_absence_ibfk_2` FOREIGN KEY (`type_absence_id`) REFERENCES `type_absence` (`id`),
  CONSTRAINT `demande_absence_ibfk_3` FOREIGN KEY (`validateur_id`) REFERENCES `personnel` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `demande_absence`
--

LOCK TABLES `demande_absence` WRITE;
/*!40000 ALTER TABLE `demande_absence` DISABLE KEYS */;
/*!40000 ALTER TABLE `demande_absence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `document_event_rules`
--

DROP TABLE IF EXISTS `document_event_rules`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `document_event_rules` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `event_name` varchar(100) NOT NULL COMMENT 'Nom de l''événement (ex: personnel.created, contrat.renewed)',
  `template_id` int(11) NOT NULL COMMENT 'FK vers documents_templates',
  `execution_mode` enum('AUTO','PROPOSED','SILENT') DEFAULT 'PROPOSED' COMMENT 'AUTO=génère automatiquement, PROPOSED=affiche dialog, SILENT=log seulement',
  `condition_json` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL COMMENT 'Conditions additionnelles en JSON (ex: {"niveau": 3})' CHECK (json_valid(`condition_json`)),
  `priority` int(11) DEFAULT 0 COMMENT 'Ordre de traitement (0 = premier)',
  `actif` tinyint(1) DEFAULT 1 COMMENT 'Règle active ou désactivée',
  `description` text DEFAULT NULL COMMENT 'Description de la règle',
  `date_creation` timestamp NULL DEFAULT current_timestamp(),
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_event_template` (`event_name`,`template_id`),
  KEY `template_id` (`template_id`),
  KEY `idx_event_name` (`event_name`),
  KEY `idx_actif` (`actif`),
  CONSTRAINT `document_event_rules_ibfk_1` FOREIGN KEY (`template_id`) REFERENCES `documents_templates` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `document_event_rules`
--

LOCK TABLES `document_event_rules` WRITE;
/*!40000 ALTER TABLE `document_event_rules` DISABLE KEYS */;
INSERT INTO `document_event_rules` VALUES
(1,'personnel.created',1,'PROPOSED',NULL,1,1,'Document pour nouvel opérateur: Consignes generales','2026-01-27 07:57:58','2026-01-27 07:57:58'),
(2,'personnel.created',2,'PROPOSED',NULL,2,1,'Document pour nouvel opérateur: Formation initiale - Activite melangeage','2026-01-27 07:57:58','2026-01-27 07:57:58'),
(4,'polyvalence.niveau_3_reached',3,'PROPOSED','{\"niveau\": 3}',1,1,'Questionnaire niveau 3: Questionnaire Qualite EMAC','2026-01-27 07:58:13','2026-01-27 07:58:13'),
(5,'polyvalence.created',4,'PROPOSED','{\"postes\": [\"506\", \"923\", \"1401\", \"1101\", \"907\", \"901\"]}',1,1,'Formation poste: Melangeur Interne','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(6,'polyvalence.created',5,'PROPOSED','{\"postes\": [\"507\", \"509\", \"510\", \"1402\", \"1404\", \"940\", \"924\", \"902\", \"920\"]}',2,1,'Formation poste: Melangeur a cylindre','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(7,'polyvalence.created',6,'PROPOSED','{\"postes\": [\"515\"]}',3,1,'Formation poste: Extrusion a chaud','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(8,'polyvalence.created',7,'PROPOSED','{\"postes\": [\"830\", \"516\", \"912\", \"930\"]}',4,1,'Formation poste: Extrusion - Pompe a engrenage','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(9,'polyvalence.created',8,'PROPOSED','{\"postes\": [\"526\", \"560\", \"511\", \"1121\", \"1103\"]}',5,1,'Formation poste: Granulatrice - Broyeur','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(10,'polyvalence.created',9,'PROPOSED','{\"postes\": [\"514\", \"1406\", \"942\", \"1405\"]}',6,1,'Formation poste: Conditionnement','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(11,'polyvalence.created',10,'PROPOSED','{\"postes\": [\"903\", \"941\"]}',7,1,'Formation poste: Calandre 3 cylindres','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(12,'polyvalence.created',11,'PROPOSED','{\"postes\": [\"900\", \"1412\", \"910\", \"1100\"]}',8,1,'Formation poste: Preparation - Pesee','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(13,'polyvalence.created',12,'PROPOSED','{\"postes\": [\"904\", \"905\", \"906\"]}',9,1,'Formation poste: Refroidisseur, Decoupe, Bobinage','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(14,'polyvalence.created',13,'PROPOSED','{\"postes\": [\"1007\"]}',10,1,'Formation poste: Moulage','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(15,'polyvalence.created',14,'PROPOSED','{\"postes\": [\"1007\"]}',11,1,'Formation poste: Ponceuse - Decoupe','2026-01-27 07:58:23','2026-01-27 07:58:23'),
(16,'polyvalence.created',15,'PROPOSED','{\"postes\": [\"1007\"]}',12,1,'Formation poste: Controleur delegue','2026-01-27 07:58:23','2026-01-27 07:58:23');
/*!40000 ALTER TABLE `document_event_rules` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `documents`
--

DROP TABLE IF EXISTS `documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `documents` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `personnel_id` int(11) NOT NULL,
  `categorie_id` int(11) NOT NULL,
  `formation_id` int(11) DEFAULT NULL,
  `contrat_id` int(11) DEFAULT NULL,
  `declaration_id` int(11) DEFAULT NULL,
  `nom_fichier` varchar(255) NOT NULL,
  `nom_affichage` varchar(255) NOT NULL,
  `chemin_fichier` varchar(500) NOT NULL,
  `type_mime` varchar(100) DEFAULT NULL,
  `taille_octets` bigint(20) DEFAULT 0,
  `date_upload` timestamp NULL DEFAULT current_timestamp(),
  `date_expiration` date DEFAULT NULL,
  `statut` enum('actif','expire','archive') DEFAULT 'actif',
  `notes` text DEFAULT NULL,
  `uploaded_by` varchar(100) DEFAULT NULL,
  `date_creation` timestamp NULL DEFAULT current_timestamp(),
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`personnel_id`),
  KEY `idx_categorie` (`categorie_id`),
  KEY `idx_statut` (`statut`),
  KEY `idx_expiration` (`date_expiration`),
  KEY `idx_documents_formation` (`formation_id`),
  KEY `idx_documents_contrat` (`contrat_id`),
  KEY `idx_documents_declaration` (`declaration_id`),
  CONSTRAINT `fk_documents_categorie` FOREIGN KEY (`categorie_id`) REFERENCES `categories_documents` (`id`),
  CONSTRAINT `fk_documents_contrat` FOREIGN KEY (`contrat_id`) REFERENCES `contrat` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_documents_declaration` FOREIGN KEY (`declaration_id`) REFERENCES `declaration` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_documents_formation` FOREIGN KEY (`formation_id`) REFERENCES `formation` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_documents_personnel` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `documents`
--

LOCK TABLES `documents` WRITE;
/*!40000 ALTER TABLE `documents` DISABLE KEYS */;
INSERT INTO `documents` VALUES
(13,417,3,NULL,NULL,NULL,'AVD EQ 08 31 plan de surveillance 901.pdf','Attestation - Formation TEST','operateurs\\Andouche Ekaitz\\formations\\AVD EQ 08 31 plan de surveillance 901.pdf','application/pdf',529340,'2026-02-09 11:01:55',NULL,'actif','Document associé à la formation du 2026-01-11','Système','2026-02-09 11:01:55','2026-02-09 11:01:55'),
(14,416,3,NULL,NULL,NULL,'AVD EQ 08 31 plan de surveillance 901.pdf','Attestation - Formation TEST','operateurs\\Lahirigoyen Thomas\\formations\\AVD EQ 08 31 plan de surveillance 901.pdf','application/pdf',529340,'2026-02-09 11:01:55',NULL,'actif','Document associé à la formation du 2026-01-11','Système','2026-02-09 11:01:55','2026-02-09 11:01:55'),
(15,417,3,17,NULL,NULL,'AVD INQ 06 02 et INQ 08 76.pdf','Attestation - Formation','operateurs\\Andouche Ekaitz\\formations\\AVD INQ 06 02 et INQ 08 76.pdf','application/pdf',983197,'2026-02-09 12:27:32',NULL,'actif','Document associé à la formation du 2026-01-11','Système','2026-02-09 12:27:32','2026-02-09 12:27:32'),
(16,416,3,18,NULL,NULL,'AVD INQ 06 02 et INQ 08 76.pdf','Attestation - Formation','operateurs\\Lahirigoyen Thomas\\formations\\AVD INQ 06 02 et INQ 08 76.pdf','application/pdf',983197,'2026-02-09 12:27:32',NULL,'actif','Document associé à la formation du 2026-01-11','Système','2026-02-09 12:27:32','2026-02-09 12:27:33');
/*!40000 ALTER TABLE `documents` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tg_documents_check_expiration_bi` BEFORE INSERT ON `documents` FOR EACH ROW BEGIN
    IF NEW.date_expiration IS NOT NULL AND NEW.date_expiration < CURDATE() THEN
        SET NEW.statut = 'expire';
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tg_documents_check_expiration_bu` BEFORE UPDATE ON `documents` FOR EACH ROW BEGIN
    IF NEW.date_expiration IS NOT NULL AND NEW.date_expiration < CURDATE() THEN
        SET NEW.statut = 'expire';
    ELSEIF NEW.date_expiration IS NULL OR NEW.date_expiration >= CURDATE() THEN
        IF OLD.statut = 'expire' THEN
            SET NEW.statut = 'actif';
        END IF;
    END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `documents_templates`
--

DROP TABLE IF EXISTS `documents_templates`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `documents_templates` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) NOT NULL,
  `fichier_source` varchar(500) NOT NULL,
  `contexte` enum('NOUVEL_OPERATEUR','NIVEAU_3','POSTE') NOT NULL,
  `postes_associes` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`postes_associes`)),
  `champ_operateur` varchar(10) DEFAULT NULL,
  `champ_auditeur` varchar(10) DEFAULT NULL,
  `champ_date` varchar(10) DEFAULT NULL,
  `obligatoire` tinyint(1) DEFAULT 0,
  `description` text DEFAULT NULL,
  `ordre_affichage` int(11) DEFAULT 0,
  `actif` tinyint(1) DEFAULT 1,
  `date_creation` timestamp NULL DEFAULT current_timestamp(),
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_contexte` (`contexte`),
  KEY `idx_actif` (`actif`)
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `documents_templates`
--

LOCK TABLES `documents_templates` WRITE;
/*!40000 ALTER TABLE `documents_templates` DISABLE KEYS */;
INSERT INTO `documents_templates` VALUES
(1,'Consignes generales','Consignes generales.xlsm','NOUVEL_OPERATEUR',NULL,'D7','J7',NULL,1,'Document de consignes generales de securite',1,1,'2026-01-15 14:22:25','2026-01-15 14:22:25'),
(2,'Formation initiale - Activite melangeage','EQ 07 02 12 rev3 Formation initiale_activite melangeage.xls','NOUVEL_OPERATEUR',NULL,'D7','J7',NULL,1,'Formulaire de formation initiale',2,1,'2026-01-15 14:22:25','2026-01-15 14:22:25'),
(3,'Questionnaire Qualite EMAC','EQ 07 02 16 rev1 Questionnaire Qualite EMAC.docx','NIVEAU_3',NULL,NULL,NULL,NULL,1,'Questionnaire qualite pour niveau 3',1,1,'2026-01-15 14:22:25','2026-01-15 14:22:25'),
(4,'Melangeur Interne','Melangeur Interne 506-923-1401-1101-907-901.xlsm','POSTE','[\"506\", \"923\", \"1401\", \"1101\", \"907\", \"901\"]','C7','I7',NULL,1,'Formation poste Melangeur Interne',1,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(5,'Melangeur a cylindre','Melangeur a cylindre 507-509-510-1402-1404-940-924-902-920.xlsm','POSTE','[\"507\", \"509\", \"510\", \"1402\", \"1404\", \"940\", \"924\", \"902\", \"920\"]','C7','I7',NULL,1,'Formation poste Melangeur a cylindre',2,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(6,'Extrusion a chaud','Extrusion a chaud 515.xlsm','POSTE','[\"515\"]','C7','I7',NULL,1,'Formation poste Extrusion a chaud',3,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(7,'Extrusion - Pompe a engrenage','Extrusion -Pompe a engrenage 830-516-912-930.xlsm','POSTE','[\"830\", \"516\", \"912\", \"930\"]','C7','I7',NULL,1,'Formation poste Extrusion - Pompe a engrenage',4,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(8,'Granulatrice - Broyeur','Granulatrice - Broyeur 526-560-511-1121-1103.xlsm','POSTE','[\"526\", \"560\", \"511\", \"1121\", \"1103\"]','C7','I7',NULL,1,'Formation poste Granulatrice - Broyeur',5,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(9,'Conditionnement','Conditionnement 514-1406-942-1405.xlsm','POSTE','[\"514\", \"1406\", \"942\", \"1405\"]','C7','I7',NULL,1,'Formation poste Conditionnement',6,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(10,'Calandre 3 cylindres','Calandre 3 cylindres 903-941.xlsm','POSTE','[\"903\", \"941\"]','C7','I7',NULL,1,'Formation poste Calandre 3 cylindres',7,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(11,'Preparation - Pesee','Preparation -Pesee 900-1412-910-1100.xlsm','POSTE','[\"900\", \"1412\", \"910\", \"1100\"]','C7','I7',NULL,1,'Formation poste Preparation - Pesee',8,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(12,'Refroidisseur, Decoupe, Bobinage','Refroidisseur, Decoupe, Bobinage 904-905-906.xlsm','POSTE','[\"904\", \"905\", \"906\"]','C7','I7',NULL,1,'Formation poste Refroidisseur, Decoupe, Bobinage',9,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(13,'Moulage','Moulage.xlsm','POSTE','[\"1007\"]','C7','I7',NULL,1,'Formation poste Moulage',10,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(14,'Ponceuse - Decoupe','Ponceuse -Decoupe.xlsm','POSTE','[\"1007\"]','C7','I7',NULL,1,'Formation poste Ponceuse - Decoupe',11,1,'2026-01-15 14:22:41','2026-01-15 14:22:41'),
(15,'Controleur delegue','Controleur delegue.xlsm','POSTE','[\"1007\"]','C7','I7',NULL,1,'Formation poste Controleur delegue',12,1,'2026-01-15 14:22:41','2026-01-15 14:22:41');
/*!40000 ALTER TABLE `documents_templates` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `features`
--

DROP TABLE IF EXISTS `features`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `features` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `key_code` varchar(100) NOT NULL COMMENT 'Clé unique ex: rh.personnel.edit',
  `label` varchar(255) NOT NULL COMMENT 'Libellé affiché ex: Modifier Personnel',
  `module` varchar(50) NOT NULL COMMENT 'Groupe/module ex: RH, Production, Admin',
  `description` text DEFAULT NULL COMMENT 'Description détaillée',
  `display_order` int(11) DEFAULT 0 COMMENT 'Ordre d''affichage dans l''UI',
  `is_active` tinyint(1) DEFAULT 1 COMMENT 'Feature activée/désactivée globalement',
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `key_code` (`key_code`),
  KEY `idx_module` (`module`),
  KEY `idx_active` (`is_active`)
) ENGINE=InnoDB AUTO_INCREMENT=56 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Catalogue des features/permissions disponibles dans l''application';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `features`
--

LOCK TABLES `features` WRITE;
/*!40000 ALTER TABLE `features` DISABLE KEYS */;
INSERT INTO `features` VALUES
(1,'rh.view','Accès module RH','RH','Accès à l\'onglet/menu RH',10,1,'2026-01-27 12:20:16'),
(2,'rh.personnel.view','Voir Personnel','RH','Consulter la liste du personnel',11,1,'2026-01-27 12:20:16'),
(3,'rh.personnel.create','Ajouter Personnel','RH','Créer un nouvel employé',12,1,'2026-01-27 12:20:16'),
(4,'rh.personnel.edit','Modifier Personnel','RH','Modifier les informations d\'un employé',13,1,'2026-01-27 12:20:16'),
(5,'rh.personnel.delete','Supprimer Personnel','RH','Supprimer/désactiver un employé',14,1,'2026-01-27 12:20:16'),
(6,'rh.contrats.view','Voir Contrats','RH','Consulter les contrats',20,1,'2026-01-27 12:20:16'),
(7,'rh.contrats.edit','Modifier Contrats','RH','Créer et modifier les contrats',21,1,'2026-01-27 12:20:16'),
(8,'rh.contrats.delete','Supprimer Contrats','RH','Supprimer des contrats',22,1,'2026-01-27 12:20:16'),
(9,'rh.documents.view','Voir Documents RH','RH','Consulter les documents RH',30,1,'2026-01-27 12:20:16'),
(10,'rh.documents.edit','Gérer Documents RH','RH','Ajouter/modifier des documents RH',31,1,'2026-01-27 12:20:16'),
(11,'rh.documents.print','Imprimer Documents','RH','Générer et imprimer des documents',32,1,'2026-01-27 12:20:16'),
(12,'rh.templates.view','Voir Templates','RH','Consulter les modèles de documents',33,1,'2026-01-27 12:20:16'),
(13,'rh.templates.edit','Gérer Templates','RH','Créer/modifier des modèles de documents',34,1,'2026-01-27 12:20:16'),
(14,'production.view','Accès module Production','Production','Accès à l\'onglet/menu Production',100,1,'2026-01-27 12:20:28'),
(15,'production.evaluations.view','Voir Évaluations','Production','Consulter les évaluations',110,1,'2026-01-27 12:20:28'),
(16,'production.evaluations.edit','Modifier Évaluations','Production','Planifier et modifier les évaluations',111,1,'2026-01-27 12:20:28'),
(17,'production.polyvalence.view','Voir Polyvalence','Production','Consulter la matrice de polyvalence',120,1,'2026-01-27 12:20:28'),
(18,'production.polyvalence.edit','Modifier Polyvalence','Production','Modifier les niveaux de compétence',121,1,'2026-01-27 12:20:28'),
(19,'production.postes.view','Voir Postes','Production','Consulter la liste des postes',130,1,'2026-01-27 12:20:28'),
(20,'production.postes.edit','Gérer Postes','Production','Créer/modifier/supprimer des postes',131,1,'2026-01-27 12:20:28'),
(21,'production.grilles.view','Voir Grilles','Production','Consulter les grilles de compétences',140,1,'2026-01-27 12:20:28'),
(22,'production.grilles.export','Exporter Grilles','Production','Exporter les grilles en Excel/PDF',141,1,'2026-01-27 12:20:28'),
(23,'planning.view','Accès Planning','Planning','Voir le planning et les absences',200,1,'2026-01-27 12:20:51'),
(24,'planning.absences.view','Voir Absences','Planning','Consulter les absences du personnel',210,1,'2026-01-27 12:20:51'),
(25,'planning.absences.edit','Gérer Absences','Planning','Créer et modifier les absences',211,1,'2026-01-27 12:20:51'),
(26,'admin.view','Accès Administration','Admin','Accès au menu administration',300,1,'2026-01-27 12:21:05'),
(27,'admin.users.view','Voir Utilisateurs','Admin','Consulter la liste des utilisateurs',310,1,'2026-01-27 12:21:05'),
(28,'admin.users.create','Créer Utilisateurs','Admin','Créer de nouveaux utilisateurs',311,1,'2026-01-27 12:21:05'),
(29,'admin.users.edit','Modifier Utilisateurs','Admin','Modifier les utilisateurs existants',312,1,'2026-01-27 12:21:05'),
(30,'admin.users.delete','Supprimer Utilisateurs','Admin','Supprimer des utilisateurs',313,1,'2026-01-27 12:21:05'),
(31,'admin.permissions','Gérer Permissions','Admin','Accéder à l\'éditeur de permissions',320,1,'2026-01-27 12:21:05'),
(32,'admin.roles.edit','Gérer Rôles','Admin','Modifier les permissions des rôles',321,1,'2026-01-27 12:21:05'),
(33,'admin.historique.view','Voir Historique','Admin','Consulter les logs d\'activité',330,1,'2026-01-27 12:21:05'),
(34,'admin.historique.export','Exporter Historique','Admin','Exporter les logs',331,1,'2026-01-27 12:21:05'),
(44,'rh.bulk_operations','Opérations en masse','RH','Accès aux opérations en masse',0,1,'2026-01-28 10:35:07'),
(45,'rh.bulk_operations.formations','Formations en masse','RH','Assignation formations en masse',0,1,'2026-01-28 10:35:07'),
(46,'rh.bulk_operations.absences','Absences en masse','RH','Assignation absences en masse',0,1,'2026-01-28 10:35:07'),
(47,'rh.bulk_operations.medical','Visites médicales en masse','RH','Assignation visites médicales en masse',0,1,'2026-01-28 10:35:07'),
(48,'rh.competences.view','Voir les compétences','RH',NULL,0,1,'2026-02-02 14:13:07'),
(49,'rh.competences.edit','Modifier les compétences','RH',NULL,0,1,'2026-02-02 14:13:07'),
(50,'rh.competences.delete','Supprimer les compétences','RH',NULL,0,1,'2026-02-02 14:13:07'),
(51,'rh.competences.catalogue','Gérer le catalogue de compétences','RH',NULL,0,1,'2026-02-02 14:13:07'),
(52,'rh.formations.view','Voir Formations','RH','Consulter les formations du personnel',40,1,'2026-02-03 07:54:27'),
(53,'rh.formations.edit','Gérer Formations','RH','Ajouter et modifier les formations',41,1,'2026-02-03 07:54:27'),
(54,'rh.formations.delete','Supprimer Formations','RH','Supprimer des formations',42,1,'2026-02-03 07:54:27');
/*!40000 ALTER TABLE `features` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formation`
--

DROP TABLE IF EXISTS `formation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `formation` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `intitule` varchar(255) NOT NULL,
  `organisme` varchar(255) DEFAULT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `duree_heures` decimal(6,2) DEFAULT NULL,
  `statut` enum('Planifiée','En cours','Terminée','Annulée') DEFAULT 'Planifiée',
  `certificat_obtenu` tinyint(1) DEFAULT 0,
  `cout` decimal(10,2) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `date_creation` timestamp NULL DEFAULT current_timestamp(),
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `document_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_statut` (`statut`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_formation_operateur_dates` (`operateur_id`,`date_debut`,`date_fin`),
  KEY `fk_formation_document` (`document_id`),
  CONSTRAINT `fk_formation_document` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_formation_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formation`
--

LOCK TABLES `formation` WRITE;
/*!40000 ALTER TABLE `formation` DISABLE KEYS */;
INSERT INTO `formation` VALUES
(17,417,'Formation','AFPA','2026-01-11','2026-02-04',8.00,'Terminée',1,NULL,NULL,'2026-02-09 12:27:32','2026-02-09 12:27:32',NULL),
(18,416,'Formation','AFPA','2026-01-11','2026-02-04',8.00,'Terminée',1,NULL,NULL,'2026-02-09 12:27:32','2026-02-09 12:27:32',NULL),
(19,2,'Test Formation Sécurité','AFPA','2026-03-11','2026-03-13',16.00,'Planifiée',0,NULL,NULL,'2026-02-09 15:19:01','2026-02-09 15:19:01',NULL),
(20,2,'Test Formation Sécurité','AFPA','2026-03-11','2026-03-13',20.00,'En cours',0,NULL,NULL,'2026-02-09 15:20:08','2026-02-09 15:20:08',NULL),
(21,2,'Test Formation Sécurité','AFPA','2026-03-11','2026-03-13',20.00,'En cours',0,NULL,NULL,'2026-02-09 15:30:32','2026-02-09 15:30:32',NULL);
/*!40000 ALTER TABLE `formation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historique`
--

DROP TABLE IF EXISTS `historique`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `historique` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date_time` datetime NOT NULL,
  `action` varchar(255) NOT NULL,
  `operateur_id` int(11) DEFAULT NULL,
  `poste_id` int(11) DEFAULT NULL,
  `description` text DEFAULT NULL,
  `utilisateur` varchar(100) DEFAULT NULL,
  `table_name` varchar(100) DEFAULT NULL,
  `record_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `operateur_id` (`operateur_id`),
  KEY `poste_id` (`poste_id`),
  KEY `idx_historique_operateur` (`operateur_id`),
  KEY `idx_historique_poste` (`poste_id`),
  KEY `idx_historique_date` (`date_time`),
  KEY `idx_historique_action_date` (`action`,`date_time`),
  CONSTRAINT `historique_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `historique_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=441 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historique`
--

LOCK TABLES `historique` WRITE;
/*!40000 ALTER TABLE `historique` DISABLE KEYS */;
INSERT INTO `historique` VALUES
(12,'2025-11-27 14:37:15','INSERT',1,1,'{\"operateur\": \"TEST MANUEL\", \"poste\": \"TEST\", \"niveau\": 3, \"type\": \"test\"}',NULL,NULL,NULL),
(13,'2025-11-27 15:50:03','INSERT',2,5,'{\"operateur\": \"Aguerre Stephane\", \"poste\": \"0515\", \"niveau\": 3, \"type\": \"ajout\"}',NULL,NULL,NULL),
(14,'2025-11-27 15:55:23','INSERT',2,5,'{\"operateur\": \"Aguerre Stephane\", \"poste\": \"0515\", \"niveau\": 4, \"type\": \"ajout\"}',NULL,NULL,NULL),
(15,'2025-11-28 08:48:47','INSERT',2,5,'{\"operateur\": \"Aguerre Stephane\", \"poste\": \"0515\", \"niveau\": 3, \"type\": \"ajout\"}',NULL,NULL,NULL),
(18,'2025-12-01 14:26:47','UPDATE',3,5,'{\"operateur\": \"Bagdasariani Eduardi\", \"poste\": \"0515\", \"changes\": {\"niveau\": {\"old\": 3, \"new\": 4}}, \"type\": \"modification\"}',NULL,NULL,NULL),
(19,'2025-12-01 14:27:21','INSERT',3,5,'{\"operateur\": \"Bagdasariani Eduardi\", \"poste\": \"0515\", \"niveau\": 3, \"type\": \"ajout\"}',NULL,NULL,NULL),
(24,'2025-12-02 11:34:30','INSERT',2,5,'{\"operateur\": \"Aguerre Stephane\", \"poste\": \"0515\", \"niveau\": 4, \"type\": \"ajout\"}',NULL,NULL,NULL),
(25,'2025-12-02 11:34:53','INSERT',2,5,'{\"operateur\": \"Aguerre Stephane\", \"poste\": \"0515\", \"niveau\": 3, \"type\": \"ajout\"}',NULL,NULL,NULL),
(27,'2025-12-05 12:32:51','INSERT',12,30,'{\"operateur\": \"Cazenave Jean\", \"poste\": \"1402\", \"niveau\": 4, \"type\": \"ajout\"}',NULL,NULL,NULL),
(28,'2025-12-05 12:32:57','INSERT',12,32,'{\"operateur\": \"Cazenave Jean\", \"poste\": \"1406\", \"niveau\": 4, \"type\": \"ajout\"}',NULL,NULL,NULL),
(29,'2025-12-05 12:34:19','INSERT',395,NULL,'{\"operateur\": \"Robert CAMMARATTA\", \"type\": \"creation_operateur\", \"details\": \"Création de l\'opérateur Robert CAMMARATTA (matricule: M000102)\", \"matricule\": \"M000102\"}',NULL,NULL,NULL),
(30,'2025-12-05 12:35:30','INSERT',395,30,'{\"operateur\": \"CAMMARATTA Robert\", \"poste\": \"1402\", \"niveau\": 1, \"type\": \"ajout\"}',NULL,NULL,NULL),
(31,'2025-12-05 12:37:24','INSERT',396,NULL,'{\"operateur\": \"Didier MASY\", \"type\": \"creation_operateur\", \"details\": \"Création de l\'opérateur Didier MASY (matricule: M000103)\", \"matricule\": \"M000103\"}',NULL,NULL,NULL),
(32,'2025-12-05 12:37:25','INSERT',396,30,'{\"operateur\": \"Didier MASY\", \"poste\": \"1402\", \"type\": \"planification_evaluation\", \"prochaine_evaluation\": \"2026-01-04\", \"details\": \"Planification évaluation pour le 2026-01-04\"}',NULL,NULL,NULL),
(33,'2025-12-05 15:00:17','UPDATE',100,32,'{\"operateur\": \"Laurent Alain\", \"poste\": \"1406\", \"changes\": {\"niveau\": {\"old\": 1, \"new\": 3}}, \"type\": \"modification\"}',NULL,NULL,NULL),
(34,'2025-12-05 15:03:13','INSERT',28,29,'{\"operateur\": \"Luquet Francois\", \"poste\": \"1401\", \"niveau\": 4, \"type\": \"ajout\"}',NULL,NULL,NULL),
(35,'2025-12-05 15:08:19','INSERT',41,33,'{\"operateur\": \"Poissonnet Jean Louis\", \"poste\": \"1412\", \"niveau\": 3, \"type\": \"ajout\"}',NULL,NULL,NULL),
(36,'2025-12-05 15:11:51','UPDATE',76,31,'{\"operateur\": \"Varin Fabien\", \"poste\": \"1404\", \"changes\": {\"niveau\": {\"old\": 2, \"new\": 3}}, \"type\": \"modification\"}',NULL,NULL,NULL),
(37,'2025-12-05 15:14:04','INSERT',397,NULL,'{\"operateur\": \"Jon Vives\", \"type\": \"creation_operateur\", \"details\": \"Création de l\'opérateur Jon Vives (matricule: M000104)\", \"matricule\": \"M000104\"}',NULL,NULL,NULL),
(38,'2025-12-05 15:14:04','INSERT',397,32,'{\"operateur\": \"Jon Vives\", \"poste\": \"1406\", \"type\": \"planification_evaluation\", \"prochaine_evaluation\": \"2026-01-04\", \"details\": \"Planification évaluation pour le 2026-01-04\"}',NULL,NULL,NULL),
(39,'2025-12-05 15:31:14','INSERT',398,NULL,'{\"operateur\": \"Pierre Latchere\", \"type\": \"creation_operateur\", \"details\": \"Création de l\'opérateur Pierre Latchere (matricule: M000105)\", \"matricule\": \"M000105\"}',NULL,NULL,NULL),
(40,'2025-12-05 15:31:14','INSERT',398,26,'{\"operateur\": \"Pierre Latchere\", \"poste\": \"1101\", \"type\": \"planification_evaluation\", \"prochaine_evaluation\": \"2025-12-24\", \"details\": \"Planification évaluation pour le 2025-12-24\"}',NULL,NULL,NULL),
(41,'2025-12-05 16:05:54','INSERT',398,25,'{\"operateur\": \"Latchere Pierre\", \"poste\": \"1100\", \"niveau\": 1, \"type\": \"ajout\"}',NULL,NULL,NULL),
(42,'2025-12-05 16:06:06','DELETE',398,26,'{\"operateur\": \"Latchere Pierre\", \"poste\": \"1101\", \"niveau\": 1, \"type\": \"suppression\"}',NULL,NULL,NULL),
(201,'2026-01-20 14:34:09','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(202,'2026-01-20 14:37:24','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(204,'2026-01-21 10:53:49','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(205,'2026-01-21 10:55:06','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(206,'2026-01-22 11:52:00','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(207,'2026-01-22 14:07:34','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(208,'2026-01-22 14:09:43','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(209,'2026-01-22 14:46:59','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(210,'2026-01-22 14:54:43','INSERT',408,NULL,'{\"operateur\": \"Lothaire Cliquennois\", \"type\": \"creation_operateur\", \"details\": \"Création de l\'opérateur Lothaire Cliquennois (Date d\'entrée: 12/11/2025) (matricule: M000110, poste: Production)\", \"matricule\": \"M000110\", \"numposte\": \"Production\"}',NULL,NULL,NULL),
(211,'2026-01-22 14:54:43','INSERT',408,1,'{\"operateur\": \"Lothaire Cliquennois\", \"poste\": \"0506\", \"niveau\": \"Niveau 1 - Débutant\", \"type\": \"planification_evaluation\", \"prochaine_evaluation\": \"2026-01-23\", \"details\": \"Planification évaluation pour le 2026-01-23 (Niveau 1 - Débutant)\"}',NULL,NULL,NULL),
(212,'2026-01-22 14:57:18','INSERT',408,31,'{\"operateur\": \"Cliquennois Lothaire\", \"poste\": \"1404\", \"niveau\": 1, \"type\": \"ajout\"}',NULL,NULL,NULL),
(213,'2026-01-22 14:59:01','DELETE',408,1,'{\"operateur\": \"Cliquennois Lothaire\", \"poste\": \"0506\", \"niveau\": 1, \"type\": \"suppression\"}',NULL,NULL,NULL),
(214,'2026-01-23 08:24:14','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(215,'2026-01-23 09:42:59','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(216,'2026-01-26 08:33:32','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(217,'2026-01-26 10:25:12','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(218,'2026-01-26 15:02:05','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(219,'2026-01-27 09:54:10','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(220,'2026-01-27 13:23:49','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(221,'2026-01-27 13:24:15','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur gprod','gprod','utilisateurs',2),
(222,'2026-01-27 13:24:25','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(223,'2026-01-27 13:25:34','MODIFICATION_FEATURES_ROLE',NULL,NULL,'Modification des features du rôle ID 2 (15 features)','admin','role_features',2),
(224,'2026-01-27 13:25:45','MODIFICATION_FEATURES_ROLE',NULL,NULL,'Modification des features du rôle ID 2 (16 features)','admin','role_features',2),
(225,'2026-01-27 13:25:55','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(226,'2026-01-27 13:25:55','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(227,'2026-01-27 13:28:28','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur GPROD (rôle: gestion_production)','GPROD','utilisateurs',2),
(228,'2026-01-27 13:37:25','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(229,'2026-01-27 13:39:42','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(230,'2026-01-27 13:39:52','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur gprod','gprod','utilisateurs',2),
(231,'2026-01-27 13:40:02','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(232,'2026-01-27 13:40:13','MODIFICATION_FEATURES_ROLE',NULL,NULL,'Modification des features du rôle ID 2 (17 features)','admin','role_features',2),
(233,'2026-01-27 13:47:10','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur GPROD (rôle: gestion_production)','GPROD','utilisateurs',2),
(234,'2026-01-27 13:52:57','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(235,'2026-01-27 14:06:53','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(236,'2026-01-27 14:07:04','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(237,'2026-01-27 14:07:18','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur gprod','gprod','utilisateurs',2),
(238,'2026-01-27 14:07:29','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(239,'2026-01-27 14:33:22','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(240,'2026-01-27 14:34:15','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(243,'2026-01-27 15:00:24','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(244,'2026-01-27 15:54:10','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(245,'2026-01-27 16:06:19','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(246,'2026-01-27 16:09:29','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(247,'2026-01-27 16:41:58','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(248,'2026-01-28 08:32:04','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(249,'2026-01-28 08:45:56','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(250,'2026-01-28 08:52:57','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(251,'2026-01-28 10:53:36','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(252,'2026-01-28 11:07:30','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(253,'2026-01-28 11:18:46','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(254,'2026-01-28 11:38:02','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(255,'2026-01-28 14:54:52','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(256,'2026-01-28 14:59:01','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(257,'2026-01-28 15:07:17','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(258,'2026-01-28 15:09:07','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(259,'2026-01-28 15:09:30','MODIFICATION_FEATURES_ROLE',NULL,NULL,'Modification des features du rôle ID 1 (38 features)','admin','role_features',1),
(260,'2026-01-28 15:09:54','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(261,'2026-01-28 15:10:19','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(262,'2026-01-28 15:11:50','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(263,'2026-01-28 15:18:13','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(264,'2026-01-28 15:20:23','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(265,'2026-01-29 08:42:44','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(266,'2026-01-29 08:49:08','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(267,'2026-01-29 09:13:01','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(268,'2026-01-29 09:16:56','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(269,'2026-01-29 10:33:05','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(270,'2026-01-29 11:20:39','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(271,'2026-01-29 11:24:36','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(272,'2026-01-29 11:32:48','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(273,'2026-01-29 14:06:58','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(274,'2026-01-30 08:52:39','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(275,'2026-01-30 08:57:50','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(276,'2026-01-30 09:18:09','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(277,'2026-01-30 09:49:42','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(278,'2026-01-30 09:52:08','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(279,'2026-01-30 09:55:49','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(280,'2026-01-30 10:52:42','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(281,'2026-01-30 10:57:25','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(282,'2026-01-30 10:57:35','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(283,'2026-01-30 10:57:46','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur gprod','gprod','utilisateurs',2),
(284,'2026-02-02 10:54:45','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(285,'2026-02-02 13:43:33','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(286,'2026-02-02 15:16:52','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(287,'2026-02-02 15:21:14','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(288,'2026-02-03 07:58:54','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(289,'2026-02-03 08:03:38','INSERT',410,NULL,'{\"operateur\": \"Gela Sidamonidze\", \"type\": \"creation_operateur\", \"details\": \"Création de l\'opérateur Gela Sidamonidze (Date d\'entrée: 02/02/2026) (matricule: M000111, poste: Production)\", \"matricule\": \"M000111\", \"numposte\": \"Production\"}',NULL,NULL,NULL),
(290,'2026-02-03 08:03:38','INSERT',410,30,'{\"operateur\": \"Gela Sidamonidze\", \"poste\": \"1402\", \"niveau\": \"Niveau 1 - Débutant\", \"type\": \"planification_evaluation\", \"prochaine_evaluation\": \"2026-03-05\", \"details\": \"Planification évaluation pour le 2026-03-05 (Niveau 1 - Débutant)\"}',NULL,NULL,NULL),
(291,'2026-02-03 08:10:21','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(292,'2026-02-03 08:19:01','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(293,'2026-02-03 08:47:44','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(296,'2026-02-03 08:51:24','MODIFICATION_FEATURES_ROLE',NULL,NULL,'Modification des features du rôle ID 1 (42 features)','admin','role_features',1),
(297,'2026-02-03 08:55:03','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(298,'2026-02-03 09:00:17','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(299,'2026-02-03 09:01:04','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(300,'2026-02-03 09:01:14','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(301,'2026-02-03 09:18:56','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur gprod','gprod','utilisateurs',2),
(302,'2026-02-03 09:19:07','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(303,'2026-02-03 09:31:56','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(304,'2026-02-03 10:44:44','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(305,'2026-02-03 10:48:55','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(306,'2026-02-03 10:53:12','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(307,'2026-02-03 10:56:40','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(310,'2026-02-03 11:11:11','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(311,'2026-02-03 11:52:17','CREATION_FORMATION',NULL,NULL,'Formation \'Formation SST - Test\' ajoutée pour opérateur 412',NULL,'formation',5),
(312,'2026-02-03 11:52:17','SUPPRESSION_FORMATION',NULL,NULL,'Formation \'Formation SST - Test\' supprimée',NULL,'formation',5),
(313,'2026-02-03 11:52:41','CREATION_FORMATION',NULL,NULL,'Formation \'Formation SST - Test\' ajoutée pour opérateur 412',NULL,'formation',6),
(314,'2026-02-03 11:52:41','SUPPRESSION_FORMATION',NULL,NULL,'Formation \'Formation SST - Test\' supprimée',NULL,'formation',6),
(315,'2026-02-03 13:37:56','CREATION_FORMATION',NULL,NULL,'Formation \'Formation SST - Test\' ajoutée pour opérateur 412',NULL,'formation',7),
(316,'2026-02-03 13:37:56','SUPPRESSION_FORMATION',NULL,NULL,'Formation \'Formation SST - Test\' supprimée',NULL,'formation',7),
(317,'2026-02-03 13:40:13','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(318,'2026-02-03 13:42:46','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(319,'2026-02-03 14:06:45','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(320,'2026-02-04 09:17:14','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(321,'2026-02-04 13:55:33','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(322,'2026-02-04 14:01:13','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(323,'2026-02-04 14:20:02','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(324,'2026-02-04 14:50:14','LOGOUT_TIMEOUT',NULL,NULL,'Déconnexion automatique par timeout (30min inactivité)','admin','utilisateurs',1),
(325,'2026-02-04 14:50:14','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(326,'2026-02-04 15:53:58','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(327,'2026-02-05 08:54:10','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(328,'2026-02-05 09:01:21','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(329,'2026-02-05 09:05:47','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(330,'2026-02-05 09:05:58','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(331,'2026-02-05 09:09:03','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(332,'2026-02-05 09:10:40','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(333,'2026-02-05 09:10:50','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur gprod','gprod','utilisateurs',2),
(334,'2026-02-05 09:10:50','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(335,'2026-02-05 09:14:29','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(336,'2026-02-05 09:27:03','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(337,'2026-02-05 09:28:18','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(338,'2026-02-05 09:28:53','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(339,'2026-02-05 09:29:20','CREATION_UTILISATEUR',NULL,NULL,'Création de l\'utilisateur test','admin','utilisateurs',4),
(340,'2026-02-05 09:29:30','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(341,'2026-02-05 09:29:40','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur test (rôle: gestion_rh)','test','utilisateurs',4),
(342,'2026-02-05 09:32:07','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur test (rôle: gestion_rh)','test','utilisateurs',4),
(343,'2026-02-05 10:20:43','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(344,'2026-02-05 10:29:05','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(345,'2026-02-05 10:47:15','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(346,'2026-02-05 10:49:05','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(347,'2026-02-05 10:52:55','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(348,'2026-02-05 11:11:59','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(349,'2026-02-05 11:12:30','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(350,'2026-02-05 11:14:57','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(351,'2026-02-05 11:20:01','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(352,'2026-02-05 11:24:53','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(353,'2026-02-05 11:29:07','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(354,'2026-02-05 11:36:57','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(355,'2026-02-05 11:44:45','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(356,'2026-02-05 11:54:36','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(357,'2026-02-05 12:00:08','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(358,'2026-02-05 13:09:21','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(359,'2026-02-05 13:14:32','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(360,'2026-02-05 13:19:00','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(361,'2026-02-05 13:22:41','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(362,'2026-02-05 13:26:41','UPDATE',205,NULL,'{\"operateur\": \"Michel Althabe\", \"old_statut\": \"ACTIF\", \"new_statut\": \"INACTIF\", \"type\": \"changement_statut\"}','admin','personnel',205),
(363,'2026-02-05 13:27:18','UPDATE',316,NULL,'{\"operateur\": \"Lionel Duchamp\", \"old_statut\": \"ACTIF\", \"new_statut\": \"INACTIF\", \"type\": \"changement_statut\"}','admin','personnel',316),
(364,'2026-02-05 13:38:07','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(365,'2026-02-05 13:46:35','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(366,'2026-02-05 13:59:23','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(368,'2026-02-05 14:29:18','LOGOUT_TIMEOUT',NULL,NULL,'Déconnexion automatique par timeout (30min inactivité)','admin','utilisateurs',1),
(369,'2026-02-05 14:29:18','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(370,'2026-02-05 14:39:20','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(371,'2026-02-05 14:40:10','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(372,'2026-02-05 14:40:20','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(373,'2026-02-05 14:40:31','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur gprod','gprod','utilisateurs',2),
(374,'2026-02-05 14:40:41','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(375,'2026-02-05 14:41:09','MODIFICATION_FEATURES_ROLE',NULL,NULL,'Modification des features du rôle ID 2 (15 features)','admin','role_features',2),
(376,'2026-02-05 14:41:19','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(377,'2026-02-05 14:41:29','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(378,'2026-02-05 14:44:27','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(379,'2026-02-05 16:34:28','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(380,'2026-02-05 16:41:02','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur gprod (rôle: gestion_production)','gprod','utilisateurs',2),
(381,'2026-02-05 16:52:18','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur gprod','gprod','utilisateurs',2),
(382,'2026-02-05 16:52:29','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(383,'2026-02-06 08:36:29','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(384,'2026-02-06 08:40:42','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(385,'2026-02-06 08:43:07','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(388,'2026-02-06 08:49:21','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(389,'2026-02-06 09:01:26','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(390,'2026-02-06 09:26:24','LOGOUT_TIMEOUT',NULL,NULL,'Déconnexion automatique par timeout (30min inactivité)','admin','utilisateurs',1),
(391,'2026-02-06 09:26:24','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(392,'2026-02-06 10:03:24','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(393,'2026-02-06 10:28:22','LOGOUT_TIMEOUT',NULL,NULL,'Déconnexion automatique par timeout (30min inactivité)','admin','utilisateurs',1),
(394,'2026-02-06 10:28:22','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(395,'2026-02-06 10:55:58','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(396,'2026-02-06 11:01:33','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(397,'2026-02-06 11:05:22','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(398,'2026-02-06 11:31:30','LOGOUT_TIMEOUT',NULL,NULL,'Déconnexion automatique par timeout (30min inactivité)','admin','utilisateurs',1),
(399,'2026-02-06 11:31:30','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(400,'2026-02-06 11:35:20','LOGOUT_TIMEOUT',NULL,NULL,'Déconnexion automatique par timeout (30min inactivité)','admin','utilisateurs',1),
(401,'2026-02-06 11:35:20','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(402,'2026-02-09 08:50:52','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(403,'2026-02-09 08:55:22','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(404,'2026-02-09 08:57:45','FORMATION_BATCH',NULL,NULL,'Formation \'Formation\' assignée à 3 personnes (0 erreurs)','admin','formation',NULL),
(405,'2026-02-09 09:07:42','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(406,'2026-02-09 09:20:48','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(407,'2026-02-09 09:22:47','INSERT',416,NULL,'{\"operateur\": \"Thomas Lahirigoyen\", \"type\": \"creation_operateur\", \"details\": \"Création de l\'opérateur Thomas Lahirigoyen (Date d\'entrée: 15/01/2026) (matricule: M000112, poste: Production)\", \"matricule\": \"M000112\", \"numposte\": \"Production\", \"source\": \"Gestion opérateur\"}','admin',NULL,NULL),
(408,'2026-02-09 09:22:47','INSERT',416,1,'{\"operateur\": \"Thomas Lahirigoyen\", \"poste\": \"0506\", \"niveau\": \"Niveau 1 - Débutant\", \"type\": \"planification_evaluation\", \"prochaine_evaluation\": \"2026-03-11\", \"details\": \"Planification évaluation pour le 2026-03-11 (Niveau 1 - Débutant)\", \"source\": \"Gestion opérateur\"}','admin',NULL,NULL),
(409,'2026-02-09 10:18:52','LOGOUT_TIMEOUT',NULL,NULL,'Déconnexion automatique par timeout (30min inactivité)','admin','utilisateurs',1),
(410,'2026-02-09 10:18:52','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(411,'2026-02-09 11:32:00','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(412,'2026-02-09 11:32:19','INSERT',417,NULL,'{\"operateur\": \"Ekaitz Andouche\", \"type\": \"creation_operateur\", \"details\": \"Création de l\'opérateur Ekaitz Andouche (Date d\'entrée: 09/02/2026)\", \"source\": \"Gestion opérateur\"}','admin',NULL,NULL),
(413,'2026-02-09 11:41:28','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(414,'2026-02-09 11:42:25','FORMATION_BATCH',NULL,NULL,'Formation \'Formation CACES\' assignée à 2 personnes (0 erreurs)','admin','formation',NULL),
(415,'2026-02-09 11:48:08','FORMATION_BATCH',NULL,NULL,'Formation \'Formation sécurité\' assignée à 2 personnes (0 erreurs)','admin','formation',NULL),
(416,'2026-02-09 12:00:50','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(417,'2026-02-09 12:01:55','FORMATION_BATCH',NULL,NULL,'Formation \'Formation TEST\' assignée à 2 personnes (0 erreurs)','admin','formation',NULL),
(418,'2026-02-09 12:30:47','LOGOUT_TIMEOUT',NULL,NULL,'Déconnexion automatique par timeout (30min inactivité)','admin','utilisateurs',1),
(419,'2026-02-09 12:30:47','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(420,'2026-02-09 13:26:26','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(421,'2026-02-09 13:27:33','FORMATION_BATCH',NULL,NULL,'Formation \'Formation\' assignée à 2 personnes (0 erreurs)','admin','formation',NULL),
(422,'2026-02-09 14:21:26','LOGOUT_TIMEOUT',NULL,NULL,'Déconnexion automatique par timeout (30min inactivité)','admin','utilisateurs',1),
(423,'2026-02-09 14:21:26','DECONNEXION',NULL,NULL,'Déconnexion de l\'utilisateur admin','admin','utilisateurs',1),
(424,'2026-02-09 16:19:01','CONTRAT_CREATION',NULL,NULL,'Enregistrement créé dans contrat | Details: {\'operateur_id\': 2, \'type_contrat\': \'CDD\', \'date_debut\': datetime.date(2026, 2, 9), \'date_fin\': datetime.date(2027, 2, 9), \'actif\': 1}',NULL,'contrat',6),
(425,'2026-02-09 16:19:01','CONTRAT_UPDATE',NULL,NULL,'Enregistrement 6 modifié | Details: {\'actif\': 0, \'date_fin\': datetime.date(2026, 8, 8)}',NULL,'contrat',6),
(426,'2026-02-09 16:19:01','FORMATION_CREATION',NULL,NULL,'Enregistrement créé dans formation | Details: {\'operateur_id\': 2, \'intitule\': \'Test Formation Sécurité\', \'organisme\': \'AFPA\', \'date_debut\': datetime.date(2026, 3, 11), \'date_fin\': datetime.date(2026, 3, 13), \'duree_heures\': 16.0, \'statut\': \'Planifiée\'}',NULL,'formation',19),
(427,'2026-02-09 16:20:08','CONTRAT_CREATION',NULL,NULL,'Enregistrement créé dans contrat | Details: {\'operateur_id\': 2, \'type_contrat\': \'CDD\', \'date_debut\': datetime.date(2026, 2, 9), \'date_fin\': datetime.date(2027, 2, 9), \'actif\': 1}',NULL,'contrat',7),
(428,'2026-02-09 16:20:08','CONTRAT_UPDATE',NULL,NULL,'Enregistrement 7 modifié | Details: {\'actif\': 0, \'date_fin\': datetime.date(2026, 8, 8)}',NULL,'contrat',7),
(429,'2026-02-09 16:20:08','FORMATION_CREATION',NULL,NULL,'Enregistrement créé dans formation | Details: {\'operateur_id\': 2, \'intitule\': \'Test Formation Sécurité\', \'organisme\': \'AFPA\', \'date_debut\': datetime.date(2026, 3, 11), \'date_fin\': datetime.date(2026, 3, 13), \'duree_heures\': 16.0, \'statut\': \'Planifiée\'}',NULL,'formation',20),
(430,'2026-02-09 16:20:08','FORMATION_UPDATE',NULL,NULL,'Enregistrement 20 modifié | Details: {\"statut\": \"En cours\", \"duree_heures\": 20.0}',NULL,'formation',20),
(431,'2026-02-09 16:30:32','CONTRAT_CREATION',2,NULL,'Enregistrement créé dans contrat | Details: {\'operateur_id\': 2, \'type_contrat\': \'CDD\', \'date_debut\': datetime.date(2026, 2, 9), \'date_fin\': datetime.date(2027, 2, 9), \'actif\': 1}',NULL,'contrat',8),
(432,'2026-02-09 16:30:32','CONTRAT_UPDATE',2,NULL,'Enregistrement 8 modifié | Details: {\'actif\': 0, \'date_fin\': datetime.date(2026, 8, 8)}',NULL,'contrat',8),
(433,'2026-02-09 16:30:32','FORMATION_CREATION',2,NULL,'Enregistrement créé dans formation | Details: {\'operateur_id\': 2, \'intitule\': \'Test Formation Sécurité\', \'organisme\': \'AFPA\', \'date_debut\': datetime.date(2026, 3, 11), \'date_fin\': datetime.date(2026, 3, 13), \'duree_heures\': 16.0, \'statut\': \'Planifiée\'}',NULL,'formation',21),
(434,'2026-02-09 16:30:32','FORMATION_UPDATE',2,NULL,'Enregistrement 21 modifié | Details: {\"statut\": \"En cours\", \"duree_heures\": 20.0}',NULL,'formation',21),
(435,'2026-02-11 10:05:27','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(436,'2026-02-11 10:09:06','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(437,'2026-02-11 14:13:19','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(438,'2026-02-11 14:16:44','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(439,'2026-02-11 14:20:14','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1),
(440,'2026-02-11 14:34:35','CONNEXION',NULL,NULL,'Connexion de l\'utilisateur admin (rôle: admin)','admin','utilisateurs',1);
/*!40000 ALTER TABLE `historique` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historique_polyvalence`
--

DROP TABLE IF EXISTS `historique_polyvalence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `historique_polyvalence` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date_action` datetime NOT NULL DEFAULT current_timestamp(),
  `action_type` enum('AJOUT','MODIFICATION','SUPPRESSION','IMPORT_MANUEL') NOT NULL,
  `operateur_id` int(11) NOT NULL,
  `poste_id` int(11) NOT NULL,
  `polyvalence_id` int(11) DEFAULT NULL,
  `ancien_niveau` int(11) DEFAULT NULL,
  `ancienne_date_evaluation` date DEFAULT NULL,
  `ancienne_prochaine_evaluation` date DEFAULT NULL,
  `ancien_statut` varchar(50) DEFAULT NULL,
  `nouveau_niveau` int(11) DEFAULT NULL,
  `nouvelle_date_evaluation` date DEFAULT NULL,
  `nouvelle_prochaine_evaluation` date DEFAULT NULL,
  `nouveau_statut` varchar(50) DEFAULT NULL,
  `utilisateur` varchar(100) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `source` varchar(100) NOT NULL DEFAULT 'SYSTEM',
  `import_batch_id` varchar(50) DEFAULT NULL,
  `metadata_json` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_poste` (`poste_id`),
  KEY `idx_date` (`date_action`),
  KEY `idx_action` (`action_type`),
  KEY `idx_batch` (`import_batch_id`),
  KEY `polyvalence_id` (`polyvalence_id`),
  CONSTRAINT `historique_polyvalence_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `historique_polyvalence_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `historique_polyvalence_ibfk_3` FOREIGN KEY (`polyvalence_id`) REFERENCES `polyvalence` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=25 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historique_polyvalence`
--

LOCK TABLES `historique_polyvalence` WRITE;
/*!40000 ALTER TABLE `historique_polyvalence` DISABLE KEYS */;
INSERT INTO `historique_polyvalence` VALUES
(8,'2025-12-03 17:33:32','AJOUT',1,1,NULL,NULL,NULL,NULL,NULL,1,'2025-12-03','2035-12-01',NULL,'Test GUI',NULL,'GUI_TEST',NULL,NULL),
(13,'2025-12-04 15:29:15','IMPORT_MANUEL',399,1,NULL,1,NULL,NULL,NULL,3,NULL,NULL,NULL,NULL,'Ancienne polyvalence archivée lors de modification depuis la grille','SYSTEM',NULL,NULL),
(14,'2025-12-04 15:36:30','IMPORT_MANUEL',399,1,NULL,3,NULL,NULL,NULL,4,NULL,NULL,NULL,NULL,'Ancienne polyvalence archivée lors de modification depuis la grille','SYSTEM',NULL,NULL),
(15,'2025-12-04 15:41:53','IMPORT_MANUEL',399,1,NULL,4,NULL,NULL,NULL,3,NULL,NULL,NULL,NULL,'Ancienne polyvalence archivée lors de modification depuis la grille','SYSTEM',NULL,NULL),
(18,'2025-12-05 14:59:29','IMPORT_MANUEL',100,32,NULL,1,'2025-10-15',NULL,NULL,3,NULL,NULL,NULL,NULL,'Ancienne polyvalence archivée lors de modification depuis la grille','SYSTEM',NULL,NULL),
(19,'2025-12-05 15:11:03','IMPORT_MANUEL',76,31,NULL,2,'2025-09-16',NULL,NULL,3,NULL,NULL,NULL,NULL,'Ancienne polyvalence archivée lors de modification depuis la grille','SYSTEM',NULL,NULL),
(20,'2026-01-09 09:11:26','IMPORT_MANUEL',7,2,NULL,4,'2020-11-02',NULL,NULL,3,NULL,NULL,NULL,NULL,'Ancienne polyvalence archivée lors de modification depuis la grille','SYSTEM',NULL,NULL),
(21,'2026-01-09 09:12:42','IMPORT_MANUEL',7,2,NULL,3,'2026-01-09',NULL,NULL,4,NULL,NULL,NULL,NULL,'Ancienne polyvalence archivée lors de modification depuis la grille','SYSTEM',NULL,NULL),
(22,'2026-01-16 10:45:38','IMPORT_MANUEL',29,30,NULL,2,'2026-01-16',NULL,NULL,1,NULL,NULL,NULL,NULL,'Ancienne polyvalence archivée lors de modification depuis la grille','SYSTEM',NULL,NULL),
(23,'2026-01-16 10:49:43','IMPORT_MANUEL',396,30,NULL,1,NULL,NULL,NULL,2,NULL,NULL,NULL,NULL,'Ancienne polyvalence archivée lors de modification depuis la grille','SYSTEM',NULL,NULL);
/*!40000 ALTER TABLE `historique_polyvalence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jours_feries`
--

DROP TABLE IF EXISTS `jours_feries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `jours_feries` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date_ferie` date NOT NULL,
  `libelle` varchar(100) NOT NULL,
  `fixe` tinyint(1) DEFAULT 1 COMMENT 'TRUE si date fixe chaque année',
  PRIMARY KEY (`id`),
  UNIQUE KEY `date_ferie` (`date_ferie`),
  KEY `idx_date` (`date_ferie`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `jours_feries`
--

LOCK TABLES `jours_feries` WRITE;
/*!40000 ALTER TABLE `jours_feries` DISABLE KEYS */;
INSERT INTO `jours_feries` VALUES
(1,'2025-01-01','Jour de l\'An',1),
(2,'2025-04-21','Lundi de Pâques',0),
(3,'2025-05-01','Fête du Travail',1),
(4,'2025-05-08','Victoire 1945',1),
(5,'2025-05-29','Ascension',0),
(6,'2025-06-09','Lundi de Pentecôte',0),
(7,'2025-07-14','Fête Nationale',1),
(8,'2025-08-15','Assomption',1),
(9,'2025-11-01','Toussaint',1),
(10,'2025-11-11','Armistice 1918',1),
(11,'2025-12-25','Noël',1);
/*!40000 ALTER TABLE `jours_feries` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `logs_connexion`
--

DROP TABLE IF EXISTS `logs_connexion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `logs_connexion` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `utilisateur_id` int(11) NOT NULL,
  `date_connexion` datetime NOT NULL,
  `date_deconnexion` datetime DEFAULT NULL,
  `ip_address` varchar(45) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `utilisateur_id` (`utilisateur_id`),
  CONSTRAINT `logs_connexion_ibfk_1` FOREIGN KEY (`utilisateur_id`) REFERENCES `utilisateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=312 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `logs_connexion`
--

LOCK TABLES `logs_connexion` WRITE;
/*!40000 ALTER TABLE `logs_connexion` DISABLE KEYS */;
INSERT INTO `logs_connexion` VALUES
(1,1,'2025-12-23 10:21:24','2025-12-23 10:21:56',NULL),
(2,1,'2025-12-23 10:29:12',NULL,NULL),
(3,1,'2025-12-23 10:39:37',NULL,NULL),
(4,1,'2025-12-23 15:14:04',NULL,NULL),
(5,1,'2025-12-23 16:06:18',NULL,NULL),
(6,1,'2025-12-23 16:09:13',NULL,NULL),
(7,1,'2025-12-23 16:23:51',NULL,NULL),
(8,1,'2025-12-23 16:34:47',NULL,NULL),
(9,1,'2025-12-24 09:23:31',NULL,NULL),
(10,1,'2026-01-05 11:25:12',NULL,NULL),
(11,1,'2026-01-06 13:34:18',NULL,NULL),
(12,1,'2026-01-06 13:42:06',NULL,NULL),
(13,1,'2026-01-07 09:33:44',NULL,NULL),
(14,1,'2026-01-07 09:35:53',NULL,NULL),
(15,1,'2026-01-07 09:50:03',NULL,NULL),
(16,1,'2026-01-07 10:03:02',NULL,NULL),
(17,1,'2026-01-07 10:05:08',NULL,NULL),
(18,1,'2026-01-07 12:07:49',NULL,NULL),
(19,1,'2026-01-07 12:10:23',NULL,NULL),
(20,1,'2026-01-08 15:51:01',NULL,NULL),
(21,1,'2026-01-09 09:09:08',NULL,NULL),
(22,1,'2026-01-09 09:13:05',NULL,NULL),
(23,1,'2026-01-12 08:40:42',NULL,NULL),
(24,1,'2026-01-12 08:50:48',NULL,NULL),
(25,1,'2026-01-12 09:05:42',NULL,NULL),
(26,1,'2026-01-12 09:08:03',NULL,NULL),
(27,1,'2026-01-12 09:09:11',NULL,NULL),
(28,1,'2026-01-12 09:15:16',NULL,NULL),
(29,1,'2026-01-12 09:16:45',NULL,NULL),
(30,1,'2026-01-12 09:17:29',NULL,NULL),
(31,1,'2026-01-12 09:21:24',NULL,NULL),
(32,1,'2026-01-12 09:23:29',NULL,NULL),
(33,1,'2026-01-12 09:31:16',NULL,NULL),
(34,1,'2026-01-12 09:55:48',NULL,NULL),
(35,1,'2026-01-12 10:07:34',NULL,NULL),
(36,1,'2026-01-12 10:10:29',NULL,NULL),
(37,1,'2026-01-12 10:18:56',NULL,NULL),
(38,1,'2026-01-12 10:24:01',NULL,NULL),
(39,1,'2026-01-12 10:25:29',NULL,NULL),
(40,1,'2026-01-12 10:26:49',NULL,NULL),
(41,1,'2026-01-12 10:46:19',NULL,NULL),
(42,1,'2026-01-12 15:34:41',NULL,NULL),
(43,1,'2026-01-13 09:07:16',NULL,NULL),
(44,1,'2026-01-13 09:29:25',NULL,NULL),
(45,1,'2026-01-13 09:59:07',NULL,NULL),
(46,1,'2026-01-13 10:01:59',NULL,NULL),
(47,1,'2026-01-13 10:04:20',NULL,NULL),
(48,1,'2026-01-13 10:07:14',NULL,NULL),
(49,1,'2026-01-13 10:08:00',NULL,NULL),
(50,1,'2026-01-13 10:40:57',NULL,NULL),
(51,1,'2026-01-13 10:43:28',NULL,NULL),
(52,1,'2026-01-13 10:53:45',NULL,NULL),
(53,1,'2026-01-13 10:55:10',NULL,NULL),
(54,1,'2026-01-13 10:59:04','2026-01-13 11:05:36',NULL),
(55,2,'2026-01-13 11:05:42',NULL,NULL),
(56,1,'2026-01-13 12:38:27',NULL,NULL),
(57,1,'2026-01-13 14:24:52',NULL,NULL),
(58,1,'2026-01-13 14:39:58',NULL,NULL),
(59,1,'2026-01-13 14:44:17',NULL,NULL),
(60,1,'2026-01-13 14:54:55',NULL,NULL),
(61,1,'2026-01-13 15:15:24',NULL,NULL),
(62,1,'2026-01-13 15:24:33',NULL,NULL),
(63,1,'2026-01-13 16:00:52',NULL,NULL),
(64,1,'2026-01-13 16:07:04',NULL,NULL),
(65,1,'2026-01-13 16:39:12',NULL,NULL),
(66,1,'2026-01-13 16:43:48',NULL,NULL),
(67,1,'2026-01-14 08:54:42',NULL,NULL),
(68,1,'2026-01-14 09:18:52',NULL,NULL),
(69,1,'2026-01-14 09:30:09',NULL,NULL),
(70,1,'2026-01-14 09:35:24',NULL,NULL),
(71,1,'2026-01-14 09:46:56',NULL,NULL),
(72,1,'2026-01-14 09:50:40',NULL,NULL),
(73,1,'2026-01-14 10:45:34',NULL,NULL),
(74,1,'2026-01-14 10:46:42',NULL,NULL),
(75,1,'2026-01-14 10:47:11',NULL,NULL),
(76,1,'2026-01-14 13:52:33','2026-01-14 13:54:09',NULL),
(77,2,'2026-01-14 13:54:16',NULL,NULL),
(78,2,'2026-01-14 14:37:01',NULL,NULL),
(79,2,'2026-01-14 14:40:02','2026-01-14 14:43:29',NULL),
(80,1,'2026-01-14 14:43:34',NULL,NULL),
(81,1,'2026-01-14 14:47:04',NULL,NULL),
(82,2,'2026-01-14 14:53:48',NULL,NULL),
(83,2,'2026-01-14 14:56:43',NULL,NULL),
(84,2,'2026-01-14 14:57:18',NULL,NULL),
(85,2,'2026-01-14 15:02:23',NULL,NULL),
(86,2,'2026-01-14 15:06:41',NULL,NULL),
(87,2,'2026-01-14 16:03:14',NULL,NULL),
(88,2,'2026-01-15 08:46:14',NULL,NULL),
(89,2,'2026-01-15 09:13:36',NULL,NULL),
(90,2,'2026-01-15 10:25:09',NULL,NULL),
(91,1,'2026-01-15 16:43:40',NULL,NULL),
(92,1,'2026-01-16 10:28:04',NULL,NULL),
(93,2,'2026-01-16 10:38:45',NULL,NULL),
(94,1,'2026-01-16 10:51:41',NULL,NULL),
(95,2,'2026-01-16 10:53:42',NULL,NULL),
(96,2,'2026-01-16 11:00:39',NULL,NULL),
(97,2,'2026-01-16 11:38:10',NULL,NULL),
(98,2,'2026-01-16 11:40:21',NULL,NULL),
(99,2,'2026-01-16 11:43:48',NULL,NULL),
(100,1,'2026-01-16 11:44:05',NULL,NULL),
(101,1,'2026-01-16 11:51:40',NULL,NULL),
(102,1,'2026-01-16 11:59:48',NULL,NULL),
(103,1,'2026-01-16 12:03:21',NULL,NULL),
(104,2,'2026-01-19 08:02:44',NULL,NULL),
(105,2,'2026-01-19 08:25:23',NULL,NULL),
(106,1,'2026-01-19 09:08:32',NULL,NULL),
(107,1,'2026-01-19 09:49:00',NULL,NULL),
(108,1,'2026-01-19 10:13:47',NULL,NULL),
(109,1,'2026-01-19 10:36:53',NULL,NULL),
(110,1,'2026-01-19 14:03:33',NULL,NULL),
(111,1,'2026-01-19 14:04:00',NULL,NULL),
(112,1,'2026-01-19 14:06:57',NULL,NULL),
(113,1,'2026-01-19 14:09:03',NULL,NULL),
(114,1,'2026-01-19 14:17:11',NULL,NULL),
(115,1,'2026-01-19 14:27:46',NULL,NULL),
(116,1,'2026-01-19 14:37:38',NULL,NULL),
(117,1,'2026-01-19 14:41:46',NULL,NULL),
(118,1,'2026-01-19 14:50:07',NULL,NULL),
(119,1,'2026-01-20 08:46:40',NULL,NULL),
(120,1,'2026-01-20 08:48:24',NULL,NULL),
(121,1,'2026-01-20 08:51:30',NULL,NULL),
(122,1,'2026-01-20 09:37:12',NULL,NULL),
(123,1,'2026-01-20 09:40:15',NULL,NULL),
(124,1,'2026-01-20 09:43:17',NULL,NULL),
(125,1,'2026-01-20 10:04:59',NULL,NULL),
(126,1,'2026-01-20 10:07:52',NULL,NULL),
(127,1,'2026-01-20 10:09:56',NULL,NULL),
(128,1,'2026-01-20 10:10:27',NULL,NULL),
(129,1,'2026-01-20 10:11:54',NULL,NULL),
(130,1,'2026-01-20 10:14:59',NULL,NULL),
(131,1,'2026-01-20 10:27:47',NULL,NULL),
(132,1,'2026-01-20 10:29:20','2026-01-20 10:34:43',NULL),
(133,2,'2026-01-20 10:34:50','2026-01-20 10:34:58',NULL),
(134,1,'2026-01-20 10:35:22','2026-01-20 10:36:32',NULL),
(135,1,'2026-01-20 10:37:00','2026-01-20 10:37:10',NULL),
(137,1,'2026-01-20 10:37:56',NULL,NULL),
(138,1,'2026-01-20 11:30:04',NULL,NULL),
(139,1,'2026-01-20 14:01:26',NULL,NULL),
(140,2,'2026-01-20 14:02:24',NULL,NULL),
(141,1,'2026-01-20 14:03:26',NULL,NULL),
(142,1,'2026-01-20 14:04:59',NULL,NULL),
(143,1,'2026-01-20 14:10:59',NULL,NULL),
(144,1,'2026-01-20 14:27:22',NULL,NULL),
(145,1,'2026-01-20 14:30:16',NULL,NULL),
(146,1,'2026-01-20 14:33:09',NULL,NULL),
(147,1,'2026-01-20 14:34:26',NULL,NULL),
(148,1,'2026-01-20 14:36:31',NULL,NULL),
(149,1,'2026-01-20 14:39:47',NULL,NULL),
(150,2,'2026-01-21 10:55:30',NULL,NULL),
(151,2,'2026-01-21 10:56:47',NULL,NULL),
(152,1,'2026-01-22 11:54:27',NULL,NULL),
(153,1,'2026-01-22 11:54:49',NULL,NULL),
(154,1,'2026-01-22 14:10:00',NULL,NULL),
(155,1,'2026-01-22 14:12:10',NULL,NULL),
(156,2,'2026-01-22 14:48:41',NULL,NULL),
(157,1,'2026-01-23 08:26:43',NULL,NULL),
(158,1,'2026-01-23 09:45:28',NULL,NULL),
(159,1,'2026-01-26 08:36:12',NULL,NULL),
(160,1,'2026-01-26 10:27:49',NULL,NULL),
(161,1,'2026-01-26 15:04:43',NULL,NULL),
(162,1,'2026-01-27 09:56:50',NULL,NULL),
(163,2,'2026-01-27 13:26:30','2026-01-27 13:26:59',NULL),
(164,1,'2026-01-27 13:27:04','2026-01-27 13:28:30',NULL),
(165,2,'2026-01-27 13:28:38',NULL,NULL),
(166,2,'2026-01-27 13:30:16',NULL,NULL),
(167,2,'2026-01-27 13:40:07',NULL,NULL),
(168,2,'2026-01-27 13:42:23','2026-01-27 13:42:31',NULL),
(169,1,'2026-01-27 13:42:37',NULL,NULL),
(170,2,'2026-01-27 13:48:58',NULL,NULL),
(171,1,'2026-01-27 13:55:38','2026-01-27 14:09:38',NULL),
(172,2,'2026-01-27 14:09:43','2026-01-27 14:10:02',NULL),
(173,1,'2026-01-27 14:10:14',NULL,NULL),
(174,1,'2026-01-27 14:36:04',NULL,NULL),
(175,1,'2026-01-27 14:36:55',NULL,NULL),
(176,1,'2026-01-27 15:03:08',NULL,NULL),
(177,1,'2026-01-27 15:37:26',NULL,NULL),
(178,1,'2026-01-27 15:56:53',NULL,NULL),
(179,1,'2026-01-27 16:08:07',NULL,NULL),
(180,1,'2026-01-27 16:11:17',NULL,NULL),
(181,1,'2026-01-27 16:41:52',NULL,NULL),
(182,1,'2026-01-27 16:44:41',NULL,NULL),
(183,1,'2026-01-27 16:53:09',NULL,NULL),
(184,1,'2026-01-28 08:34:47',NULL,NULL),
(185,1,'2026-01-28 08:48:40',NULL,NULL),
(186,1,'2026-01-28 08:55:40',NULL,NULL),
(187,1,'2026-01-28 10:56:21',NULL,NULL),
(188,1,'2026-01-28 11:10:13',NULL,NULL),
(189,1,'2026-01-28 11:21:29',NULL,NULL),
(190,1,'2026-01-28 11:40:45',NULL,NULL),
(191,1,'2026-01-28 11:55:33',NULL,NULL),
(192,1,'2026-01-28 14:57:37',NULL,NULL),
(193,1,'2026-01-28 15:01:45',NULL,NULL),
(194,1,'2026-01-28 15:10:01',NULL,NULL),
(195,1,'2026-01-28 15:11:49',NULL,NULL),
(196,1,'2026-01-28 15:12:36',NULL,NULL),
(197,1,'2026-01-28 15:13:06',NULL,NULL),
(198,1,'2026-01-28 15:14:36',NULL,NULL),
(199,1,'2026-01-28 15:20:58',NULL,NULL),
(200,1,'2026-01-28 15:23:06',NULL,NULL),
(201,1,'2026-01-29 08:45:31',NULL,NULL),
(202,1,'2026-01-29 08:51:53',NULL,NULL),
(203,1,'2026-01-29 09:15:47',NULL,NULL),
(204,1,'2026-01-29 09:19:44',NULL,NULL),
(205,1,'2026-01-29 10:35:51',NULL,NULL),
(206,1,'2026-01-29 11:23:25',NULL,NULL),
(207,1,'2026-01-29 11:27:24',NULL,NULL),
(208,1,'2026-01-29 11:35:37',NULL,NULL),
(209,1,'2026-01-29 14:09:43',NULL,NULL),
(210,1,'2026-01-30 08:55:27',NULL,NULL),
(211,1,'2026-01-30 09:00:38',NULL,NULL),
(212,1,'2026-01-30 09:20:56',NULL,NULL),
(213,1,'2026-01-30 09:52:29',NULL,NULL),
(214,1,'2026-01-30 09:54:57',NULL,NULL),
(215,1,'2026-01-30 09:58:38',NULL,NULL),
(216,1,'2026-01-30 10:55:30','2026-01-30 11:00:18',NULL),
(217,2,'2026-01-30 11:00:23','2026-01-30 11:00:32',NULL),
(218,1,'2026-02-02 10:57:46',NULL,'PC-NR/10.201.201.31'),
(219,1,'2026-02-02 13:46:30',NULL,'PC-NR/10.201.201.31'),
(220,1,'2026-02-02 15:19:48',NULL,'PC-NR/10.201.201.31'),
(221,1,'2026-02-02 15:24:11',NULL,'PC-NR/10.201.201.31'),
(222,2,'2026-02-03 08:00:49',NULL,NULL),
(223,2,'2026-02-03 08:12:16',NULL,NULL),
(224,2,'2026-02-03 08:20:55',NULL,NULL),
(225,1,'2026-02-03 08:50:47',NULL,'PC-NR/10.201.201.31'),
(226,1,'2026-02-03 08:58:07',NULL,'PC-NR/10.201.201.31'),
(227,1,'2026-02-03 09:03:18','2026-02-03 09:04:09','PC-NR/10.201.201.31'),
(228,2,'2026-02-03 09:04:14','2026-02-03 09:22:02','PC-NR/10.201.201.31'),
(229,1,'2026-02-03 09:22:05',NULL,'PC-NR/10.201.201.31'),
(230,1,'2026-02-03 09:34:57',NULL,'PC-NR/10.201.201.31'),
(231,1,'2026-02-03 10:47:47',NULL,'PC-NR/10.201.201.31'),
(232,1,'2026-02-03 10:51:56',NULL,'PC-NR/10.201.201.31'),
(233,1,'2026-02-03 10:56:17',NULL,'PC-NR/10.201.201.31'),
(234,1,'2026-02-03 10:59:41',NULL,'PC-NR/10.201.201.31'),
(235,1,'2026-02-03 11:14:16',NULL,'PC-NR/10.201.201.31'),
(236,1,'2026-02-03 13:43:14',NULL,'PC-NR/10.201.201.31'),
(237,1,'2026-02-03 13:45:48',NULL,'PC-NR/10.201.201.31'),
(238,1,'2026-02-03 14:09:45',NULL,'PC-NR/10.201.201.31'),
(239,1,'2026-02-04 09:20:18',NULL,'PC-NR/10.201.201.31'),
(240,1,'2026-02-04 13:58:37',NULL,'PC-NR/10.201.201.31'),
(241,1,'2026-02-04 14:04:17',NULL,'PC-NR/10.201.201.31'),
(242,1,'2026-02-04 14:23:06','2026-02-04 14:53:22','PC-NR/10.201.201.31'),
(243,1,'2026-02-04 15:57:03',NULL,'PC-NR/10.201.201.31'),
(244,1,'2026-02-05 08:57:20',NULL,'PC-NR/10.201.201.31'),
(245,1,'2026-02-05 09:04:32','2026-02-05 09:08:58','PC-NR/10.201.201.31'),
(246,2,'2026-02-05 09:09:04',NULL,'PC-NR/10.201.201.31'),
(247,2,'2026-02-05 09:12:11',NULL,'PC-NR/10.201.201.31'),
(248,2,'2026-02-05 09:13:49','2026-02-05 09:13:56','PC-NR/10.201.201.31'),
(249,1,'2026-02-05 09:14:01',NULL,'PC-NR/10.201.201.31'),
(250,1,'2026-02-05 09:17:35',NULL,'PC-NR/10.201.201.31'),
(251,1,'2026-02-05 09:30:08','2026-02-05 09:31:29','PC-NR/10.201.201.31'),
(252,1,'2026-02-05 09:32:02','2026-02-05 09:32:37','PC-NR/10.201.201.31'),
(253,4,'2026-02-05 09:32:47',NULL,'PC-NR/10.201.201.31'),
(254,1,'2026-02-05 09:35:04',NULL,'PC-NR/10.201.201.31'),
(255,4,'2026-02-05 09:35:14',NULL,'PC-NR/10.201.201.31'),
(256,1,'2026-02-05 10:23:50',NULL,'PC-NR/10.201.201.31'),
(257,1,'2026-02-05 10:32:11',NULL,'PC-NR/10.201.201.31'),
(258,1,'2026-02-05 10:50:21',NULL,'PC-NR/10.201.201.31'),
(259,1,'2026-02-05 10:52:12',NULL,'PC-NR/10.201.201.31'),
(260,1,'2026-02-05 10:56:01',NULL,'PC-NR/10.201.201.31'),
(261,1,'2026-02-05 11:15:05',NULL,'PC-NR/10.201.201.31'),
(262,1,'2026-02-05 11:15:37',NULL,'PC-NR/10.201.201.31'),
(263,1,'2026-02-05 11:18:03',NULL,'PC-NR/10.201.201.31'),
(264,1,'2026-02-05 11:23:08',NULL,'PC-NR/10.201.201.31'),
(265,1,'2026-02-05 11:27:59',NULL,'PC-NR/10.201.201.31'),
(266,1,'2026-02-05 11:32:13',NULL,'PC-NR/10.201.201.31'),
(267,1,'2026-02-05 11:40:04',NULL,'PC-NR/10.201.201.31'),
(268,1,'2026-02-05 11:47:54',NULL,'PC-NR/10.201.201.31'),
(269,1,'2026-02-05 11:57:43',NULL,'PC-NR/10.201.201.31'),
(270,1,'2026-02-05 12:03:15',NULL,'PC-NR/10.201.201.31'),
(271,1,'2026-02-05 13:12:28',NULL,'PC-NR/10.201.201.31'),
(272,1,'2026-02-05 13:17:40',NULL,'PC-NR/10.201.201.31'),
(273,1,'2026-02-05 13:22:07',NULL,'PC-NR/10.201.201.31'),
(274,1,'2026-02-05 13:25:50',NULL,'PC-NR/10.201.201.31'),
(275,1,'2026-02-05 13:41:14',NULL,'PC-NR/10.201.201.31'),
(276,1,'2026-02-05 13:49:40',NULL,'PC-NR/10.201.201.31'),
(277,1,'2026-02-05 14:02:29','2026-02-05 14:32:30','PC-NR/10.201.201.31'),
(278,1,'2026-02-05 14:42:27','2026-02-05 14:43:21','PC-NR/10.201.201.31'),
(279,2,'2026-02-05 14:43:26','2026-02-05 14:43:39','PC-NR/10.201.201.31'),
(280,1,'2026-02-05 14:43:43','2026-02-05 14:44:29','PC-NR/10.201.201.31'),
(281,2,'2026-02-05 14:44:33',NULL,'PC-NR/10.201.201.31'),
(282,2,'2026-02-05 14:47:11',NULL,'PC-NR/10.201.201.31'),
(283,1,'2026-02-05 14:47:35',NULL,'PC-NR/10.201.201.31'),
(284,1,'2026-02-05 16:37:35',NULL,'PC-NR/10.201.201.31'),
(285,2,'2026-02-05 16:44:10','2026-02-05 16:55:30','PC-NR/10.201.201.31'),
(286,1,'2026-02-05 16:55:34',NULL,'PC-NR/10.201.201.31'),
(287,1,'2026-02-06 08:39:44',NULL,'PC-NR/10.201.201.31'),
(288,1,'2026-02-06 08:43:53',NULL,'PC-NR/10.201.201.31'),
(289,1,'2026-02-06 08:46:16',NULL,'PC-NR/10.201.201.31'),
(290,1,'2026-02-06 08:52:33',NULL,'PC-NR/10.201.201.31'),
(291,1,'2026-02-06 09:04:35','2026-02-06 09:29:39','PC-NR/10.201.201.31'),
(292,1,'2026-02-06 10:06:33','2026-02-06 10:31:37','PC-NR/10.201.201.31'),
(293,1,'2026-02-06 10:59:08',NULL,'PC-NR/10.201.201.31'),
(294,1,'2026-02-06 11:04:43','2026-02-06 11:34:45','PC-NR/10.201.201.31'),
(295,1,'2026-02-06 11:08:32','2026-02-06 11:38:35','PC-NR/10.201.201.31'),
(296,1,'2026-02-09 08:54:14',NULL,'PC-NR/10.201.201.30'),
(297,1,'2026-02-09 08:58:40',NULL,'PC-NR/10.201.201.30'),
(298,1,'2026-02-09 09:11:01',NULL,'PC-NR/10.201.201.30'),
(299,1,'2026-02-09 09:24:12','2026-02-09 10:22:16','PC-NR/10.201.201.30'),
(300,1,'2026-02-09 11:35:21',NULL,'PC-NR/10.201.201.30'),
(301,1,'2026-02-09 11:44:47',NULL,'PC-NR/10.201.201.30'),
(302,1,'2026-02-09 12:04:09','2026-02-09 12:34:11','PC-NR/10.201.201.30'),
(303,1,'2026-02-09 13:29:46','2026-02-09 14:24:50','PC-NR/10.201.201.30'),
(304,1,'2026-02-11 10:08:53',NULL,'PC-NR/10.201.201.30'),
(305,1,'2026-02-11 10:12:33',NULL,'PC-NR/10.201.201.30'),
(306,1,'2026-02-11 10:15:10',NULL,'PC-NR/10.201.201.30'),
(307,1,'2026-02-11 13:57:57',NULL,'PC-NR/10.201.201.30'),
(308,1,'2026-02-11 14:16:46',NULL,'PC-NR/10.201.201.30'),
(309,1,'2026-02-11 14:20:11',NULL,'PC-NR/10.201.201.30'),
(310,1,'2026-02-11 14:23:40',NULL,'PC-NR/10.201.201.30'),
(311,1,'2026-02-11 14:38:03',NULL,'PC-NR/10.201.201.30');
/*!40000 ALTER TABLE `logs_connexion` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medical`
--

DROP TABLE IF EXISTS `medical`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `medical` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `type_suivi_vip` enum('SIA','SIR','SI') DEFAULT NULL,
  `periodicite_vip_mois` int(11) DEFAULT 24,
  `date_electrocardiogramme` date DEFAULT NULL,
  `maladie_pro` tinyint(1) DEFAULT 0,
  `taux_professionnel` decimal(5,2) DEFAULT NULL,
  `besoins_adaptation` text DEFAULT NULL,
  `demande_reconnaissance_atmp_en_cours` tinyint(1) DEFAULT 0,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_medical_operateur` (`operateur_id`),
  CONSTRAINT `fk_medical_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medical`
--

LOCK TABLES `medical` WRITE;
/*!40000 ALTER TABLE `medical` DISABLE KEYS */;
/*!40000 ALTER TABLE `medical` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medical_accident_travail`
--

DROP TABLE IF EXISTS `medical_accident_travail`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `medical_accident_travail` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `date_accident` date NOT NULL,
  `heure_accident` time DEFAULT NULL,
  `jour_semaine` enum('Lundi','Mardi','Mercredi','Jeudi','Vendredi','Samedi','Dimanche') DEFAULT NULL,
  `horaires` varchar(50) DEFAULT NULL,
  `circonstances` text DEFAULT NULL,
  `siege_lesions` varchar(255) DEFAULT NULL,
  `nature_lesions` varchar(255) DEFAULT NULL,
  `avec_arret` tinyint(1) DEFAULT 0,
  `date_reconnaissance_at` date DEFAULT NULL,
  `date_debut_arret` date DEFAULT NULL,
  `date_fin_arret_initial` date DEFAULT NULL,
  `date_fin_prolongation` date DEFAULT NULL,
  `nb_jours_absence` int(11) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_at_operateur` (`operateur_id`),
  KEY `idx_at_date` (`date_accident`),
  KEY `idx_at_avec_arret` (`avec_arret`),
  CONSTRAINT `fk_at_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medical_accident_travail`
--

LOCK TABLES `medical_accident_travail` WRITE;
/*!40000 ALTER TABLE `medical_accident_travail` DISABLE KEYS */;
/*!40000 ALTER TABLE `medical_accident_travail` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medical_maladie_pro`
--

DROP TABLE IF EXISTS `medical_maladie_pro`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `medical_maladie_pro` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `date_reconnaissance` date NOT NULL,
  `numero_tableau` varchar(20) DEFAULT NULL,
  `designation` varchar(255) DEFAULT NULL,
  `taux_ipp` decimal(5,2) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_mp_operateur` (`operateur_id`),
  KEY `idx_mp_date` (`date_reconnaissance`),
  CONSTRAINT `fk_mp_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medical_maladie_pro`
--

LOCK TABLES `medical_maladie_pro` WRITE;
/*!40000 ALTER TABLE `medical_maladie_pro` DISABLE KEYS */;
/*!40000 ALTER TABLE `medical_maladie_pro` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medical_prolongation_arret`
--

DROP TABLE IF EXISTS `medical_prolongation_arret`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `medical_prolongation_arret` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `accident_id` int(11) NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `numero_prolongation` int(11) DEFAULT 1,
  `commentaire` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_prolongation_accident` (`accident_id`),
  CONSTRAINT `fk_prolongation_accident` FOREIGN KEY (`accident_id`) REFERENCES `medical_accident_travail` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medical_prolongation_arret`
--

LOCK TABLES `medical_prolongation_arret` WRITE;
/*!40000 ALTER TABLE `medical_prolongation_arret` DISABLE KEYS */;
/*!40000 ALTER TABLE `medical_prolongation_arret` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `medical_visite`
--

DROP TABLE IF EXISTS `medical_visite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `medical_visite` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `date_visite` date NOT NULL,
  `type_visite` enum('Embauche','Périodique','Reprise','À la demande','Pré-reprise') DEFAULT 'Périodique',
  `resultat` enum('Apte','Apte avec restrictions','Inapte temporaire','Inapte définitif') DEFAULT NULL,
  `restrictions` text DEFAULT NULL,
  `medecin` varchar(255) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `prochaine_visite` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_visite_operateur` (`operateur_id`),
  KEY `idx_visite_date` (`date_visite`),
  KEY `idx_visite_prochaine` (`prochaine_visite`),
  CONSTRAINT `fk_visite_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `medical_visite`
--

LOCK TABLES `medical_visite` WRITE;
/*!40000 ALTER TABLE `medical_visite` DISABLE KEYS */;
/*!40000 ALTER TABLE `medical_visite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `permissions`
--

DROP TABLE IF EXISTS `permissions`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `permissions` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role_id` int(11) NOT NULL,
  `module` varchar(100) NOT NULL,
  `lecture` tinyint(1) DEFAULT 1,
  `ecriture` tinyint(1) DEFAULT 0,
  `suppression` tinyint(1) DEFAULT 0,
  PRIMARY KEY (`id`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `permissions_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=31 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permissions`
--

LOCK TABLES `permissions` WRITE;
/*!40000 ALTER TABLE `permissions` DISABLE KEYS */;
INSERT INTO `permissions` VALUES
(1,1,'personnel',1,1,1),
(2,1,'evaluations',1,1,1),
(3,1,'polyvalence',1,1,1),
(4,1,'contrats',1,1,1),
(5,1,'documents_rh',1,1,1),
(6,1,'planning',1,1,1),
(7,1,'postes',1,1,1),
(8,1,'historique',1,1,1),
(9,1,'grilles',1,1,1),
(10,1,'gestion_utilisateurs',1,1,1),
(11,2,'personnel',1,1,1),
(12,2,'evaluations',1,1,1),
(13,2,'polyvalence',1,1,1),
(14,2,'contrats',1,0,0),
(15,2,'documents_rh',0,0,0),
(16,2,'planning',1,0,0),
(17,2,'postes',1,1,1),
(18,2,'historique',1,0,0),
(19,2,'grilles',1,1,1),
(20,2,'gestion_utilisateurs',0,0,0),
(21,3,'personnel',1,1,1),
(22,3,'evaluations',0,0,0),
(23,3,'polyvalence',1,0,0),
(24,3,'contrats',1,1,1),
(25,3,'documents_rh',1,1,1),
(26,3,'planning',0,0,0),
(27,3,'postes',1,0,0),
(28,3,'historique',1,0,0),
(29,3,'grilles',0,0,0),
(30,3,'gestion_utilisateurs',0,0,0);
/*!40000 ALTER TABLE `permissions` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `permissions_utilisateur`
--

DROP TABLE IF EXISTS `permissions_utilisateur`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `permissions_utilisateur` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `utilisateur_id` int(11) NOT NULL,
  `module` varchar(100) NOT NULL,
  `lecture` tinyint(1) DEFAULT NULL COMMENT 'NULL=hérite du rôle, 0=refusé, 1=autorisé',
  `ecriture` tinyint(1) DEFAULT NULL COMMENT 'NULL=hérite du rôle, 0=refusé, 1=autorisé',
  `suppression` tinyint(1) DEFAULT NULL COMMENT 'NULL=hérite du rôle, 0=refusé, 1=autorisé',
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `modifie_par` int(11) DEFAULT NULL COMMENT 'ID de l''admin qui a fait la modification',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_module` (`utilisateur_id`,`module`),
  KEY `modifie_par` (`modifie_par`),
  KEY `idx_utilisateur` (`utilisateur_id`),
  CONSTRAINT `permissions_utilisateur_ibfk_1` FOREIGN KEY (`utilisateur_id`) REFERENCES `utilisateurs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `permissions_utilisateur_ibfk_2` FOREIGN KEY (`modifie_par`) REFERENCES `utilisateurs` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Overrides de permissions par utilisateur. Les valeurs NULL héritent du rôle.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `permissions_utilisateur`
--

LOCK TABLES `permissions_utilisateur` WRITE;
/*!40000 ALTER TABLE `permissions_utilisateur` DISABLE KEYS */;
/*!40000 ALTER TABLE `permissions_utilisateur` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel`
--

DROP TABLE IF EXISTS `personnel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) DEFAULT NULL,
  `prenom` varchar(255) DEFAULT NULL,
  `statut` varchar(255) DEFAULT NULL,
  `service_id` int(11) DEFAULT NULL,
  `numposte` varchar(100) DEFAULT NULL,
  `matricule` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_matricule` (`matricule`),
  UNIQUE KEY `uc_personnel` (`nom`,`prenom`),
  UNIQUE KEY `idx_personnel_matricule_unique` (`matricule`),
  KEY `idx_personnel_statut` (`statut`),
  KEY `idx_personnel_matricule` (`matricule`),
  KEY `idx_personnel_nom_prenom` (`nom`,`prenom`)
) ENGINE=InnoDB AUTO_INCREMENT=418 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel`
--

LOCK TABLES `personnel` WRITE;
/*!40000 ALTER TABLE `personnel` DISABLE KEYS */;
INSERT INTO `personnel` VALUES
(1,'Acedo','Sebastien','INACTIF',NULL,'Production','M000001'),
(2,'Aguerre','Stephane','ACTIF',NULL,'Production','M000002'),
(3,'Bagdasariani','Eduardi','ACTIF',1,'Production','M000003'),
(4,'Beheregaray','Jean Michel','INACTIF',1,'200','M000004'),
(5,'Bengochea','Emmanuel','ACTIF',1,'Production','M000005'),
(6,'Bidondo','Anthony','ACTIF',1,'Production','M000006'),
(7,'Bidondo','Mickael Alexandre','ACTIF',NULL,'Production','M000007'),
(8,'Bidondo','Pierre','ACTIF',1,'247','M000008'),
(9,'Brankaer','Alexandre','ACTIF',1,'Production','M000009'),
(10,'Campane','Jean Francois','ACTIF',NULL,'Production','M000010'),
(11,'Carricaburu','Alain','INACTIF',NULL,'Production','M000011'),
(12,'Cazenave','Jean','ACTIF',1,'Production','M000012'),
(13,'Cordani','Jean-Marie Joseph','ACTIF',NULL,'Production','M000013'),
(14,'Correia Dos Santos','Jorge Manuel','ACTIF',NULL,'Production','M000014'),
(15,'Costa','Daniel','ACTIF',1,'342','M000015'),
(16,'Couchinave','Eric','ACTIF',NULL,'Production','M000016'),
(17,'Courties','Doryan','ACTIF',9,'Production','M000017'),
(18,'Da Costa','Sergio','ACTIF',NULL,'Production','M000018'),
(19,'Davies','Edouard','INACTIF',1,'Production','M000019'),
(20,'Delgado','Cedric','ACTIF',9,'Production','M000020'),
(21,'Devaux','David','INACTIF',1,'Production','M000021'),
(22,'Dos Santos','Charly','ACTIF',1,'Production 1404','M000022'),
(23,'Etcheverry','Frederic','ACTIF',9,'Production','M000023'),
(24,'Fernandez','Thomas','ACTIF',1,'Production','M000024'),
(25,'Gonot','Damien','ACTIF',1,'Production','M000025'),
(26,'Gouvinhas','Alexandre','ACTIF',1,'Production','M000026'),
(27,'Guimon','Alain','ACTIF',1,'Leader','M000027'),
(28,'Luquet','Francois','ACTIF',NULL,'Production','M000028'),
(29,'Marcadieu','Cedric','ACTIF',NULL,'Production','M000029'),
(30,'Marta','Frederic','ACTIF',NULL,'Production','M000030'),
(31,'Merciris','Theo','INACTIF',NULL,'Production','M000031'),
(32,'Milage','Alban','ACTIF',1,'Production','M000032'),
(33,'Molus','Sonia','ACTIF',1,'Production','M000033'),
(34,'Montois','Xabi','ACTIF',1,'Production','M000034'),
(35,'Moriat','Andre','INACTIF',NULL,'Production','M000035'),
(36,'Moustrous','Herve','ACTIF',1,'Production','M000036'),
(37,'Orduna','Pierre','ACTIF',1,'Production','M000037'),
(38,'Oyhenart','Nicolas','ACTIF',1,'Production','M000038'),
(39,'Perez','Xavier','ACTIF',1,'Production','M000039'),
(40,'Pochelu','Andre Maurice','ACTIF',1,'Production','M000040'),
(41,'Poissonnet','Jean Louis','ACTIF',NULL,'Production','M000041'),
(42,'Poutou','Eldon Tresor','ACTIF',NULL,'Production','M000042'),
(43,'Rice','Matthew','ACTIF',1,'Production','M000043'),
(44,'Sallette','Frederic','ACTIF',NULL,'Production','M000044'),
(45,'Saralegui','Eric','ACTIF',1,'Production','M000045'),
(46,'Servant','Mikaël','ACTIF',NULL,'Production','M000046'),
(47,'Sicre','Pierre','ACTIF',1,'342','M000047'),
(48,'Tradere','Jonathan','ACTIF',9,'Production','M000048'),
(49,'Unanua','Dominique','ACTIF',1,'Production','M000049'),
(50,'Urrutia','Laurent','ACTIF',1,'Production','M000050'),
(51,'Vasseur','Joffrey','ACTIF',1,'Production','M000051'),
(52,'Verge','Olivier','ACTIF',1,'Production','M000052'),
(76,'Varin','Fabien','INACTIF',NULL,'Production','M000076'),
(99,'Etcheverria','Joaquim','INACTIF',1,'Production','M000099'),
(100,'Laurent','Alain','ACTIF',NULL,'Production','M000100'),
(107,'Amat','Romain Florian','INACTIF',NULL,NULL,NULL),
(108,'Peraro','Mickael Eric Michel','ACTIF',9,'Production',NULL),
(111,'Arnal','Jean Marie','ACTIF',NULL,NULL,NULL),
(112,'Bailly','Xavier Marc Jean','ACTIF',9,'Production',NULL),
(114,'Bercaits','Francois Marie','ACTIF',9,'Production',NULL),
(116,'Berho','Inaki','ACTIF',9,'Production',NULL),
(118,'Berrogain','Jean Baptiste','ACTIF',9,'242',NULL),
(120,'Berthe','Ophelie Jeanne Suzanne','ACTIF',9,'Production',NULL),
(124,'Bouldoires','Mathieu','ACTIF',10,'R&D',NULL),
(126,'Camy','Alain','ACTIF',9,'Production',NULL),
(128,'Castex','Laurent Christian','ACTIF',9,'Production',NULL),
(136,'Daguerre','Patrick Jean Claude','ACTIF',9,'233',NULL),
(138,'Daubas','Georges Michel','ACTIF',9,'Production',NULL),
(142,'Duhalde','Pierre Sauveur','ACTIF',9,'Production',NULL),
(144,'Errecart','Serge','ACTIF',9,'Production',NULL),
(148,'Fernandes','Marie Francoise','ACTIF',13,'Laboratoire',NULL),
(150,'Godfrin','David','ACTIF',9,'226',NULL),
(152,'Gouvert','Caroline Catherine Josephine','ACTIF',9,'222',NULL),
(154,'Heugas','Jeremy','ACTIF',NULL,'243/241',NULL),
(155,'Iglesias','Ludovic Malik','ACTIF',9,'Production',NULL),
(157,'Iturria','Loic','ACTIF',11,'Maintenance',NULL),
(159,'Jimenez','Andre','ACTIF',9,'264',NULL),
(161,'Joumah','Hassan','ACTIF',9,'240',NULL),
(163,'Kern','Bernard','ACTIF',9,'Production',NULL),
(165,'Lac Peyras','Pascale','ACTIF',9,'241',NULL),
(167,'Lagourgue','Didier Guillermo','ACTIF',9,'Production',NULL),
(169,'Larraburu','Pascale','ACTIF',13,'Laboratoire',NULL),
(171,'Lordon','Jeanbaptiste','ACTIF',9,'Production',NULL),
(173,'Maffrand','Alexis','ACTIF',9,'Production',NULL),
(175,'Marques','Pauline Marie Elodie','ACTIF',9,'Production',NULL),
(177,'Mendribil','Alain','ACTIF',9,'Production',NULL),
(179,'Olivier','Alban Roger','ACTIF',9,'207',NULL),
(181,'Recalt','Herve','ACTIF',9,'220',NULL),
(183,'Recalt','Jean Paul','ACTIF',9,'222',NULL),
(185,'Reina','Frederic','ACTIF',9,'257',NULL),
(187,'Sallaberry','Jean Michel','ACTIF',9,'211',NULL),
(189,'Sarda','Manon Marie','ACTIF',12,'Admin',NULL),
(191,'Sebilo','Allan Georges Gerard','ACTIF',9,'Production',NULL),
(193,'Simon','Thomas Thierry Didier','ACTIF',9,'Production',NULL),
(195,'Soubiran','Veronique Sophie','ACTIF',13,'Laboratoire',NULL),
(197,'Sublime','Cyril Georges Andre','ACTIF',9,'208',NULL),
(199,'Tardy','Jean Marie','ACTIF',9,'Production',NULL),
(203,'Verge','Remy','ACTIF',9,'Production',NULL),
(205,'Althabe','Michel','INACTIF',9,'205',NULL),
(207,'Arhancetebehere','Didier','ACTIF',9,'218',NULL),
(209,'Arrouge','Thomas','ACTIF',11,'Maitenance',NULL),
(211,'Bergez','Franck','ACTIF',9,'228',NULL),
(213,'Charman','Maxime Daniel','ACTIF',9,'214',NULL),
(215,'Couchiniave','Sonia','ACTIF',9,'202',NULL),
(219,'Gauchet','Steve Jean Rene','ACTIF',9,'206',NULL),
(221,'Gaudin','Alexandra','ACTIF',9,'243',NULL),
(223,'Gerony','Carole','ACTIF',9,'229',NULL),
(225,'Gesse','Marie Claire','ACTIF',9,'230',NULL),
(227,'Guiresse','Brigitte','ACTIF',9,'203',NULL),
(229,'Epelva','François','ACTIF',9,'Production',NULL),
(231,'Picot','Frederic','ACTIF',9,'Production',NULL),
(233,'Dos Santos','Elisa','ACTIF',12,'Admin',NULL),
(235,'Moureu','Marie Laure','ACTIF',9,'201',NULL),
(237,'Lepolard','Aurélien Michel','ACTIF',NULL,NULL,NULL),
(238,'Poli','Xabi Saint Martin','ACTIF',9,'Production',NULL),
(240,'Denecker','Charlotte','ACTIF',12,'Admin',NULL),
(242,'Heguiabehere','Alexandre','ACTIF',9,'Production',NULL),
(244,'Remon','Florian','ACTIF',9,'Production',NULL),
(246,'Barat','Romain','ACTIF',12,'Admin',NULL),
(248,'Dutter','Muriel','ACTIF',13,'Labo',NULL),
(250,'Berreterot','Julien','ACTIF',9,'Production',NULL),
(252,'Capuret','Anthony','ACTIF',9,'Production',NULL),
(254,'Rabineau','Nicolas','ACTIF',12,'Admin',NULL),
(256,'Deslandes','Laurent','ACTIF',9,'Production',NULL),
(258,'Erbin','Julien','ACTIF',9,'Production',NULL),
(260,'Lepolard','Baptiste','ACTIF',9,'Production',NULL),
(262,'Aren','Pierre','ACTIF',9,'Production',NULL),
(264,'Lauga','Frédéric','ACTIF',9,'Production',NULL),
(266,'Campane','Lionel','ACTIF',9,'Production',NULL),
(268,'Dumollard','Thierry','ACTIF',9,'Production',NULL),
(270,'Jelassi','Joël Jean','ACTIF',11,'Maintenance',NULL),
(272,'Dumurlourteau','Vincent','ACTIF',9,'Production',NULL),
(274,'Ramonteuchiros','Ludovic','ACTIF',9,'Production',NULL),
(276,'Havy','Floriant','ACTIF',9,'Production',NULL),
(278,'Deverite','Jonathan','ACTIF',9,'Production',NULL),
(280,'Larroque','Guillaume','ACTIF',11,'Maintenance',NULL),
(282,'Peyrou','Maxime','ACTIF',9,'Production',NULL),
(284,'Lascoumes','Marie','ACTIF',12,'Admin',NULL),
(286,'Salmon','Quentin','ACTIF',9,'Production',NULL),
(288,'El Hamouchi','Mohamed','ACTIF',13,'Laboratoire',NULL),
(290,'Chammam','Marwa','ACTIF',12,'Administratif',NULL),
(292,'Rebiere','Théo Romain','ACTIF',10,'R&D',NULL),
(294,'Dennemont','Valentin','ACTIF',9,'Production',NULL),
(296,'Courties','Paul Marc','ACTIF',9,'Production',NULL),
(302,'Gonzalez Merg','Paulo Cristiano','ACTIF',9,'Production',NULL),
(304,'Loureiro','Michel','ACTIF',9,'Production',NULL),
(308,'Fernandez','Yohan','ACTIF',9,'Production',NULL),
(310,'Pelegrinelli','Damien','ACTIF',9,'Production',NULL),
(314,'Courties','Clérik','ACTIF',9,'Production',NULL),
(316,'Duchamp','Lionel','INACTIF',9,'Production',NULL),
(318,'Saiz Fernandez','Kévin','ACTIF',9,'Production',NULL),
(320,'Etcheverry','Fabien','ACTIF',9,'Production',NULL),
(322,'Tardy','Maxime','ACTIF',9,'Production',NULL),
(326,'Bergeron','Marie-Noëlle','ACTIF',13,'Laboratoire',NULL),
(328,'Munoz Teres','Vanessa','ACTIF',16,'Qualite',NULL),
(330,'Da Costaramos','Sergio','ACTIF',9,'Production',NULL),
(332,'Chardin','Kévin','ACTIF',NULL,NULL,NULL),
(335,'Loustalot','Marlène','ACTIF',14,'Cariste-Hse',NULL),
(337,'Brana','Jeanpaul','ACTIF',9,'Production',NULL),
(339,'Etcheberriborde','Julie','ACTIF',12,'Admin',NULL),
(341,'Da Costa Silva','Sonia','ACTIF',NULL,NULL,NULL),
(342,'Mosqueda','Martin','ACTIF',NULL,NULL,NULL),
(343,'Gelard','Alain','ACTIF',NULL,NULL,NULL),
(344,'Idiart','Céline','ACTIF',12,'Administratif',NULL),
(348,'Etcheverry','Adrien','ACTIF',NULL,NULL,NULL),
(349,'Michaut','Bettan','ACTIF',11,'Maintenance',NULL),
(357,'Thiery','Adrien','ACTIF',14,'Agent Hse - Cariste',NULL),
(359,'Revidiego','Isabelle','ACTIF',14,'Agent Hse',NULL),
(361,'Sauve','Amaïa','ACTIF',9,'Production',NULL),
(363,'Lajournade','Antoine','ACTIF',15,'Methode',NULL),
(365,'Banquet','Marine','ACTIF',16,'Qualite',NULL),
(367,'Fretay','Sabrina','ACTIF',14,'Hse',NULL),
(369,'Colas','Martin','ACTIF',12,'Admin',NULL),
(395,'CAMMARATTA','Robert','INACTIF',NULL,'Production','M000102'),
(396,'MASY','Didier','ACTIF',NULL,'Production','M000103'),
(397,'Vives','Jon','INACTIF',NULL,'Production','M000104'),
(398,'Latchere','Pierre','ACTIF',NULL,'Production','M000105'),
(399,'Gross','Luka','ACTIF',NULL,'Production','M000106'),
(402,'Sawicz','Jakub','ACTIF',NULL,'Production','M000107'),
(405,'Leplat','Frédéric','ACTIF',NULL,'Production','M000109'),
(408,'Cliquennois','Lothaire','INACTIF',NULL,'Production','M000110'),
(410,'Sidamonidze','Gela','ACTIF',NULL,'Production','M000111'),
(416,'Lahirigoyen','Thomas','ACTIF',NULL,'Production','M000112'),
(417,'Andouche','Ekaitz','ACTIF',NULL,NULL,NULL);
/*!40000 ALTER TABLE `personnel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_competences`
--

DROP TABLE IF EXISTS `personnel_competences`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_competences` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `personnel_id` int(11) NOT NULL,
  `competence_id` int(11) NOT NULL,
  `date_acquisition` date NOT NULL,
  `date_expiration` date DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `document_id` int(11) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personnel_competence` (`personnel_id`,`competence_id`),
  KEY `idx_personnel_id` (`personnel_id`),
  KEY `idx_competence_id` (`competence_id`),
  KEY `idx_date_expiration` (`date_expiration`),
  KEY `fk_pc_document` (`document_id`),
  CONSTRAINT `fk_pc_competence` FOREIGN KEY (`competence_id`) REFERENCES `competences_catalogue` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_pc_document` FOREIGN KEY (`document_id`) REFERENCES `documents` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_pc_personnel` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_competences`
--

LOCK TABLES `personnel_competences` WRITE;
/*!40000 ALTER TABLE `personnel_competences` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_competences` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_infos`
--

DROP TABLE IF EXISTS `personnel_infos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_infos` (
  `personnel_id` int(11) NOT NULL,
  `sexe` enum('F','M','X','NSP') DEFAULT 'NSP',
  `date_entree` date DEFAULT NULL,
  `nationalite` varchar(50) DEFAULT NULL,
  `cp_naissance` varchar(20) DEFAULT NULL,
  `ville_naissance` varchar(100) DEFAULT NULL,
  `pays_naissance` varchar(100) DEFAULT NULL,
  `date_naissance` date DEFAULT NULL,
  `adresse1` varchar(255) DEFAULT NULL,
  `adresse2` varchar(255) DEFAULT NULL,
  `cp_adresse` varchar(20) DEFAULT NULL,
  `ville_adresse` varchar(100) DEFAULT NULL,
  `pays_adresse` varchar(100) DEFAULT NULL,
  `telephone` varchar(20) DEFAULT NULL,
  `email` varchar(320) DEFAULT NULL,
  `nir_chiffre` varbinary(255) DEFAULT NULL,
  `nir_nonce` varbinary(16) DEFAULT NULL,
  `nir_tag` varbinary(16) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `numero_ss` varchar(15) DEFAULT NULL,
  PRIMARY KEY (`personnel_id`),
  UNIQUE KEY `uk_operateur_infos` (`personnel_id`),
  KEY `idx_email` (`email`),
  KEY `idx_cp_adresse` (`cp_adresse`),
  KEY `idx_ville_adresse` (`ville_adresse`),
  CONSTRAINT `fk_infos_operateur` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_personnel_infos_personnel` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_infos`
--

LOCK TABLES `personnel_infos` WRITE;
/*!40000 ALTER TABLE `personnel_infos` DISABLE KEYS */;
INSERT INTO `personnel_infos` VALUES
(2,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(3,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(5,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(6,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(7,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(8,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(9,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(10,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(12,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(13,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(14,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(15,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(16,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(17,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(18,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(20,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(22,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(23,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(24,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(25,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(26,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(27,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(28,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(29,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(30,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(32,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(33,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(34,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(36,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(37,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(38,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(39,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(40,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(41,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(42,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(43,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(44,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(45,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(46,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(47,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(48,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(49,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(50,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(51,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(52,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(100,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(108,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(111,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(112,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(114,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(116,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(118,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(120,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(124,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(126,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(128,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(136,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(138,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(142,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(144,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(148,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(150,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(152,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(154,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(155,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(157,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(159,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(161,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(163,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(165,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(167,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(169,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(171,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(173,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(175,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(177,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(179,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(181,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(183,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(185,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(187,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(189,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(191,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(193,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(195,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(197,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(199,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(203,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(205,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(207,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(209,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(211,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(213,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(215,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(219,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(221,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(223,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(225,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(227,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(229,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(231,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(233,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(235,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(237,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(238,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(240,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(242,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(244,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(246,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(248,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(250,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(252,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(254,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(256,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(258,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(260,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(262,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(264,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(266,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(268,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(270,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(272,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(274,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(276,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(278,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(280,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(282,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(284,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(286,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(288,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(290,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(292,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(294,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(296,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(302,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(304,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(308,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(310,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(314,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(316,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(318,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(320,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(322,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(326,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(328,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(330,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(332,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(335,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(337,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(339,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(341,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(342,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(343,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(344,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(348,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(349,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(357,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(359,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(361,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(363,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(365,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(367,'F',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(369,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(396,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(398,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(399,'M',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(402,'M','2026-01-14',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(405,'NSP','2025-12-15',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(408,'NSP','2025-11-12',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(410,'NSP','2026-02-02',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(416,'NSP','2026-01-15',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(417,'NSP','2026-02-09',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `personnel_infos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `polyvalence`
--

DROP TABLE IF EXISTS `polyvalence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `polyvalence` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `poste_id` int(11) NOT NULL,
  `niveau` int(11) DEFAULT NULL,
  `date_evaluation` date DEFAULT NULL,
  `prochaine_evaluation` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `operateur_id` (`operateur_id`),
  KEY `poste_id` (`poste_id`),
  KEY `idx_polyvalence_operateur` (`operateur_id`),
  KEY `idx_polyvalence_poste` (`poste_id`),
  KEY `idx_polyvalence_prochaine_eval` (`prochaine_evaluation`),
  KEY `idx_polyvalence_eval_operateur` (`operateur_id`,`prochaine_evaluation`),
  KEY `idx_polyvalence_niveau_eval` (`niveau`,`prochaine_evaluation`),
  CONSTRAINT `polyvalence_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `polyvalence_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `polyvalence_chk_1` CHECK (`niveau` between 1 and 4)
) ENGINE=InnoDB AUTO_INCREMENT=18371 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `polyvalence`
--

LOCK TABLES `polyvalence` WRITE;
/*!40000 ALTER TABLE `polyvalence` DISABLE KEYS */;
INSERT INTO `polyvalence` VALUES
(17439,1,5,3,'2024-06-17','2034-06-15'),
(17440,1,31,3,'2023-09-29','2033-09-26'),
(17442,2,8,3,'2020-11-02','2030-10-31'),
(17443,2,11,3,'2021-09-29','2031-09-29'),
(17444,2,13,3,'2021-09-29','2031-09-29'),
(17445,2,19,3,'2020-11-02','2030-10-31'),
(17446,2,20,3,'2021-09-29','2031-09-29'),
(17447,2,21,3,'2021-09-29','2031-09-29'),
(17448,2,32,3,'2020-11-02','2030-10-31'),
(17451,4,9,4,'2020-11-02','2030-10-31'),
(17452,4,14,4,'2020-11-02','2030-10-31'),
(17453,4,33,4,'2020-11-02','2030-10-31'),
(17454,5,6,3,'2019-11-25','2029-11-22'),
(17455,5,8,3,'2021-09-30','2031-09-30'),
(17456,5,15,3,'2020-02-13','2030-02-11'),
(17457,5,19,3,'2019-11-26','2029-11-23'),
(17458,5,23,3,'2021-02-18','2031-02-17'),
(17459,6,1,4,'2024-06-14','2034-06-12'),
(17460,6,5,4,'2024-06-14','2034-06-12'),
(17461,6,28,4,'2024-06-14','2034-06-12'),
(17462,6,29,4,'2022-10-24','2032-10-21'),
(17463,6,30,4,'2022-10-24','2032-10-21'),
(17464,6,31,4,'2022-10-24','2032-10-21'),
(17465,6,32,4,'2022-04-20','2032-04-19'),
(17466,6,33,4,'2023-10-24','2033-10-31'),
(17467,7,1,4,'2020-11-02','2030-10-31'),
(17468,7,2,4,'2026-01-09','2036-01-07'),
(17469,7,4,4,'2020-11-02','2030-10-31'),
(17470,7,5,4,'2020-11-02','2030-10-31'),
(17471,7,6,4,'2020-11-02','2030-10-31'),
(17472,7,7,4,'2020-11-02','2030-10-31'),
(17473,7,10,4,'2024-10-10','2034-10-09'),
(17474,7,11,4,'2020-11-02','2030-10-31'),
(17475,7,12,4,'2021-11-24','2031-11-24'),
(17476,7,13,4,'2021-11-24','2031-11-24'),
(17477,7,16,4,'2023-10-23','2033-10-20'),
(17478,7,17,4,'2020-11-02','2030-10-31'),
(17479,7,18,4,'2021-11-24','2031-11-24'),
(17480,7,20,4,'2021-11-24','2031-11-24'),
(17481,7,21,4,'2021-11-24','2031-11-24'),
(17482,7,22,4,'2021-11-24','2031-11-24'),
(17483,7,25,4,'2020-11-02','2030-10-31'),
(17484,7,26,4,'2020-11-02','2030-10-31'),
(17485,7,27,4,'2020-11-02','2030-10-31'),
(17486,7,28,4,'2020-11-02','2030-10-31'),
(17487,7,30,4,'2023-10-23','2033-10-20'),
(17488,7,33,4,'2023-10-23','2033-10-20'),
(17489,8,1,4,'2020-11-10','2030-11-08'),
(17490,8,2,4,'2020-11-10','2030-11-08'),
(17491,8,5,4,'2020-11-10','2030-11-08'),
(17492,8,11,4,'2021-09-29','2031-09-29'),
(17493,8,12,4,'2021-09-29','2031-09-29'),
(17494,8,13,4,'2021-09-29','2031-09-29'),
(17495,8,16,4,'2023-10-23','2033-10-20'),
(17496,8,17,4,'2021-02-02','2031-01-31'),
(17497,8,18,4,'2021-09-29','2031-09-29'),
(17498,8,20,4,'2021-09-29','2031-09-29'),
(17499,8,21,4,'2021-09-29','2031-09-29'),
(17500,8,22,4,'2021-09-29','2031-09-29'),
(17501,8,29,4,'2019-10-15','2029-10-12'),
(17502,8,30,4,'2019-10-15','2029-10-12'),
(17503,8,31,4,'2019-10-15','2029-10-12'),
(17504,8,32,4,'2019-10-15','2029-10-12'),
(17505,8,33,4,'2019-10-14','2029-10-11'),
(17506,9,9,3,'2019-11-25','2029-11-22'),
(17507,9,33,3,'2019-07-24','2029-07-23'),
(17508,10,4,3,'2022-10-18','2032-10-15'),
(17509,10,5,3,'2022-10-19','2032-10-18'),
(17510,10,6,3,'2025-01-31','2035-01-31'),
(17511,11,5,3,'2024-06-17','2034-06-15'),
(17512,11,13,3,'2023-05-30','2033-05-27'),
(17513,11,22,3,'2023-05-13','2033-05-10'),
(17514,11,30,3,'2024-04-12','2034-04-10'),
(17515,12,1,4,'2023-01-11','2033-01-10'),
(17516,12,2,4,'2021-10-01','2031-09-29'),
(17517,12,3,4,'2023-10-24','2033-10-21'),
(17518,12,4,4,'2020-10-19','2030-10-17'),
(17519,12,5,4,'2020-10-19','2030-10-17'),
(17520,12,6,4,'2020-10-19','2030-10-17'),
(17521,12,7,4,'2024-07-05','2034-07-03'),
(17522,12,28,4,'2024-07-05','2034-07-03'),
(17523,13,1,3,'2019-07-17','2029-07-16'),
(17524,13,2,3,'2019-07-17','2029-07-16'),
(17525,13,17,3,'2019-07-16','2029-07-13'),
(17526,14,33,3,'2021-11-16','2031-11-14'),
(17527,15,1,4,'2020-11-02','2030-10-31'),
(17528,15,2,4,'2020-11-02','2030-10-31'),
(17529,15,3,4,'2020-11-02','2030-10-31'),
(17530,15,4,4,'2020-11-02','2030-10-31'),
(17531,15,5,4,'2020-11-02','2030-10-31'),
(17532,15,6,4,'2020-11-02','2030-10-31'),
(17533,15,7,4,'2020-11-02','2030-10-31'),
(17534,15,11,4,'2020-11-02','2030-10-31'),
(17535,15,17,4,'2020-11-02','2030-10-31'),
(17536,15,28,4,'2020-11-02','2030-10-31'),
(17537,16,2,3,'2019-09-17','2029-09-14'),
(17538,16,3,3,'2019-07-17','2029-07-16'),
(17539,16,5,3,'2019-07-17','2029-07-16'),
(17540,16,6,3,'2023-10-23','2033-10-20'),
(17541,16,11,3,'2019-07-17','2029-07-16'),
(17542,16,25,3,'2020-10-19','2030-10-17'),
(17543,16,28,3,'2020-10-19','2030-10-17'),
(17544,17,1,4,'2024-06-17','2034-06-15'),
(17545,17,5,4,'2024-06-17','2034-06-14'),
(17546,17,28,4,'2024-06-17','2034-06-14'),
(17547,17,29,4,'2021-03-15','2031-03-13'),
(17548,17,30,4,'2021-03-03','2031-03-03'),
(17549,17,31,4,'2019-09-17','2029-09-14'),
(17550,17,32,4,'2021-03-03','2031-03-03'),
(17551,17,33,4,'2021-09-21','2031-09-19'),
(17552,18,1,3,'2023-05-30','2033-05-27'),
(17553,19,1,3,'2024-06-14','2034-06-12'),
(17554,19,8,3,'2022-09-19','2032-09-16'),
(17555,19,29,3,'2023-01-30','2033-01-27'),
(17556,20,1,3,'2024-09-10','2034-09-08'),
(17557,20,2,3,'2020-10-19','2030-10-17'),
(17558,20,4,3,'2019-05-06','2029-05-03'),
(17559,20,5,3,'2019-05-06','2029-05-03'),
(17560,20,6,3,'2020-03-16','2030-03-14'),
(17561,20,25,3,'2020-10-19','2030-10-17'),
(17562,20,28,3,'2024-08-01','2034-07-31'),
(17563,21,2,3,'2022-04-26','2032-04-23'),
(17564,21,5,3,'2024-04-26','2034-04-24'),
(17565,21,25,3,'2024-11-25','2034-11-23'),
(17566,21,28,2,'2024-11-25','2025-01-24'),
(17567,22,1,3,'2024-06-17','2034-06-15'),
(17568,22,29,3,'2023-09-29','2033-09-26'),
(17569,22,31,3,'2021-09-21','2031-09-19'),
(17570,23,9,4,'2020-11-02','2030-10-31'),
(17571,23,14,4,'2020-11-02','2030-10-31'),
(17572,23,25,4,'2024-07-05','2034-07-03'),
(17573,23,28,4,'2024-07-05','2034-07-03'),
(17574,23,33,4,'2020-11-02','2030-10-31'),
(17575,24,5,3,'2022-10-18','2032-10-15'),
(17576,24,8,3,'2020-10-20','2030-10-18'),
(17577,24,19,3,'2020-10-20','2030-10-18'),
(17578,24,25,3,'2024-09-02','2034-08-31'),
(17579,24,28,3,'2024-09-02','2034-08-31'),
(17580,25,1,4,'2022-07-01','2032-06-28'),
(17581,25,10,4,'2021-03-03','2031-03-03'),
(17582,25,11,4,'2022-07-01','2032-06-28'),
(17583,25,13,4,'2021-03-03','2031-03-03'),
(17584,25,16,4,'2023-10-23','2033-10-20'),
(17585,25,17,4,'2021-03-03','2031-03-03'),
(17586,25,18,4,'2022-07-01','2032-06-28'),
(17587,25,20,4,'2023-10-23','2033-10-20'),
(17588,25,21,4,'2023-10-23','2033-10-20'),
(17589,25,22,4,'2023-10-23','2033-10-20'),
(17590,25,29,4,'2021-03-03','2031-03-03'),
(17591,25,30,4,'2023-10-23','2033-10-20'),
(17592,25,32,4,'2023-10-23','2033-10-20'),
(17593,25,33,4,'2023-10-23','2033-10-20'),
(17594,26,6,4,'2022-04-02','2032-03-30'),
(17595,26,8,4,'2022-04-02','2032-03-30'),
(17596,26,15,4,'2022-04-02','2032-03-30'),
(17597,26,19,4,'2022-04-02','2032-03-30'),
(17598,26,28,4,'2024-07-05','2034-07-03'),
(17599,27,2,3,'2020-11-02','2030-10-31'),
(17600,27,4,3,'2019-07-11','2029-07-09'),
(17601,27,5,3,'2019-08-28','2029-08-27'),
(17602,27,6,3,'2020-11-02','2030-10-31'),
(17603,27,7,3,'2020-11-02','2030-10-31'),
(17604,27,8,3,'2020-11-02','2030-10-31'),
(17605,27,11,3,'2020-11-02','2030-10-31'),
(17606,27,13,3,'2023-10-23','2033-10-20'),
(17607,27,15,3,'2020-11-02','2030-10-31'),
(17608,27,17,3,'2020-11-02','2030-10-31'),
(17609,27,19,3,'2020-11-02','2030-10-31'),
(17610,27,22,3,'2023-10-23','2033-10-20'),
(17611,27,28,3,'2020-11-02','2030-10-31'),
(17612,28,9,4,'2024-11-25','2034-11-23'),
(17613,28,10,4,'2022-04-25','2032-04-22'),
(17614,28,11,4,'2022-07-01','2032-06-28'),
(17615,28,12,4,'2022-10-19','2032-10-18'),
(17616,28,13,4,'2022-04-25','2032-04-22'),
(17617,28,14,4,'2024-11-25','2034-11-23'),
(17618,28,16,4,'2023-10-24','2033-10-21'),
(17619,28,17,4,'2022-04-25','2032-04-22'),
(17620,28,18,4,'2023-10-24','2033-10-21'),
(17621,28,20,4,'2022-04-25','2032-04-22'),
(17622,28,21,4,'2022-07-01','2032-06-28'),
(17623,28,22,4,'2023-10-24','2033-10-21'),
(17624,28,28,4,'2024-07-08','2034-07-06'),
(17625,29,33,3,'2023-09-27','2033-09-26'),
(17626,30,19,3,'2023-03-06','2033-03-03'),
(17627,30,28,3,'2024-09-02','2034-08-31'),
(17628,31,5,3,'2024-06-13','2034-06-12'),
(17629,31,32,3,'2023-10-11','2033-10-10'),
(17630,32,5,3,'2022-10-19','2032-10-18'),
(17631,32,6,3,'2023-10-23','2033-10-20'),
(17632,32,8,3,'2021-05-20','2031-05-19'),
(17633,32,19,3,'2022-10-19','2032-10-18'),
(17634,32,28,3,'2024-07-08','2034-07-06'),
(17635,33,23,3,'2020-12-03','2030-12-02'),
(17636,33,24,3,'2020-12-03','2030-12-02'),
(17637,33,25,3,'2021-09-13','2031-09-11'),
(17638,33,27,3,'2021-09-13','2031-09-11'),
(17639,33,28,3,'2024-07-05','2034-07-03'),
(17640,34,4,3,'2024-09-02','2034-08-31'),
(17641,34,5,3,'2024-09-02','2034-08-31'),
(17642,34,6,3,'2024-11-25','2034-11-23'),
(17643,35,8,3,'2023-09-27','2033-09-26'),
(17644,35,19,3,'2023-06-20','2033-06-17'),
(17645,35,25,3,'2024-09-02','2034-08-31'),
(17646,35,28,3,'2024-07-05','2034-07-03'),
(17647,36,5,3,'2020-11-13','2030-11-11'),
(17648,36,31,3,'2019-08-29','2029-08-27'),
(17649,37,7,3,'2020-10-19','2030-10-17'),
(17650,37,25,3,'2020-10-19','2030-10-17'),
(17651,37,26,3,'2020-10-19','2030-10-17'),
(17652,37,27,3,'2020-10-19','2030-10-17'),
(17653,37,28,3,'2020-10-19','2030-10-17'),
(17654,38,9,3,'2020-10-19','2030-10-17'),
(17655,38,14,3,'2020-10-19','2030-10-17'),
(17656,38,25,3,'2020-10-19','2030-10-17'),
(17657,39,2,3,'2020-11-02','2030-10-31'),
(17658,39,3,3,'2020-11-02','2030-10-31'),
(17659,39,5,3,'2020-11-02','2030-10-31'),
(17660,39,11,3,'2022-04-25','2032-04-22'),
(17661,39,12,3,'2023-10-23','2033-10-20'),
(17662,39,16,3,'2023-10-23','2033-10-20'),
(17663,39,18,3,'2022-04-25','2032-04-22'),
(17664,39,20,3,'2022-04-25','2032-04-22'),
(17665,39,21,3,'2022-04-25','2032-04-22'),
(17666,39,25,3,'2024-06-14','2034-06-12'),
(17667,39,28,3,'2024-06-14','2034-06-12'),
(17668,39,30,3,'2020-11-02','2030-10-31'),
(17669,39,31,3,'2020-11-02','2030-10-31'),
(17670,40,2,3,'2020-11-02','2030-10-31'),
(17903,40,3,3,'2020-11-02','2030-10-31'),
(17904,40,4,3,'2020-11-02','2030-10-31'),
(17905,40,5,3,'2020-11-02','2030-10-31'),
(17906,40,28,3,'2024-06-14','2034-06-12'),
(17907,40,30,3,'2020-11-02','2030-10-31'),
(17908,40,31,3,'2020-11-02','2030-10-31'),
(17909,40,32,3,'2020-11-02','2030-10-31'),
(17910,40,33,3,'2020-11-02','2030-10-31'),
(17911,41,9,3,'2022-04-04','2032-04-01'),
(17912,41,14,3,'2022-04-04','2032-04-01'),
(17913,41,25,3,'2024-11-25','2034-11-23'),
(17914,42,1,3,'2024-06-13','2034-06-12'),
(17915,42,29,3,'2023-10-23','2033-10-20'),
(17916,43,11,3,'2021-09-29','2031-09-29'),
(17917,43,12,3,'2021-09-29','2031-09-29'),
(17918,43,16,3,'2023-10-24','2033-10-21'),
(17919,43,20,3,'2021-09-29','2031-09-29'),
(17920,43,21,3,'2021-09-29','2031-09-29'),
(17921,43,28,3,'2024-07-08','2034-07-06'),
(17922,43,30,3,'2021-09-29','2031-09-29'),
(17923,43,31,3,'2021-09-29','2031-09-29'),
(17924,44,2,3,'2022-10-24','2032-10-21'),
(17925,44,3,3,'2022-10-24','2032-10-21'),
(17926,44,5,3,'2022-10-24','2032-10-21'),
(17927,44,6,3,'2022-10-24','2032-10-21'),
(17928,45,2,3,'2019-09-16','2029-09-13'),
(17929,45,5,3,'2019-07-30','2029-07-27'),
(17930,45,30,3,'2019-09-17','2029-09-14'),
(17931,46,5,3,'2024-06-14','2034-06-12'),
(17932,46,30,3,'2022-07-27','2032-07-26'),
(17933,47,1,4,'2020-11-02','2030-10-31'),
(17934,47,2,4,'2020-11-02','2030-10-31'),
(17935,47,3,4,'2020-11-02','2030-10-31'),
(17936,47,4,4,'2020-11-02','2030-10-31'),
(17937,47,5,4,'2020-02-11','2030-10-31'),
(17938,47,6,4,'2020-11-02','2030-10-31'),
(17939,47,7,4,'2020-11-02','2030-10-31'),
(17940,47,11,4,'2020-11-02','2030-10-31'),
(17941,47,17,4,'2020-11-02','2030-10-31'),
(17942,47,28,4,'2020-11-02','2030-10-31'),
(17943,47,31,4,'2020-11-02','2030-10-31'),
(17944,48,1,3,'2020-11-02','2030-10-31'),
(17945,48,9,3,'2023-03-09','2033-03-07'),
(17946,48,29,3,'2020-11-02','2030-10-31'),
(17947,49,5,3,'2022-04-03','2032-03-31'),
(17948,49,6,3,'2022-04-03','2032-03-31'),
(17949,49,8,3,'2024-09-11','2034-09-11'),
(17950,49,15,3,'2022-04-03','2032-03-31'),
(17951,49,28,3,'2025-01-31','2035-01-29'),
(17952,50,15,3,'2024-07-05','2034-07-03'),
(17953,51,1,4,'2020-11-02','2030-10-31'),
(17954,51,2,4,'2020-11-02','2030-10-31'),
(17955,51,4,4,'2020-11-02','2030-10-31'),
(17956,51,5,4,'2020-11-02','2030-10-31'),
(17957,51,6,4,'2020-11-02','2030-10-31'),
(17958,51,28,4,'2024-06-13','2034-06-12'),
(17959,51,29,4,'2020-11-02','2030-10-31'),
(17960,51,30,4,'2020-11-02','2030-10-31'),
(18251,51,31,4,'2020-11-02','2030-10-31'),
(18252,51,32,4,'2020-12-10','2030-12-09'),
(18253,51,33,4,'2020-11-02','2030-10-31'),
(18254,52,9,3,'2020-11-02','2030-10-31'),
(18255,52,14,3,'2020-11-02','2030-10-31'),
(18271,76,31,3,'2025-10-15','2035-10-15'),
(18284,12,77,4,'2025-04-07','2035-04-09'),
(18289,99,5,3,'2025-10-15','2025-11-14'),
(18290,99,32,3,'2025-10-15','2025-11-14'),
(18291,100,32,3,'2025-10-22','2035-10-22'),
(18293,2,28,3,'2025-04-07','2035-04-05'),
(18299,15,77,4,'2025-04-07','2035-04-05'),
(18300,16,77,3,'2025-04-07','2035-04-05'),
(18301,20,77,3,'2025-04-07','2035-04-05'),
(18302,28,77,4,'2025-04-07','2035-04-05'),
(18303,28,7,4,'2025-04-07','2035-04-05'),
(18304,34,7,3,'2025-04-07','2035-04-05'),
(18305,34,77,3,'2025-04-07','2035-04-05'),
(18306,44,77,3,'2025-04-07','2035-04-05'),
(18307,47,77,4,'2025-04-07','2035-04-05'),
(18308,16,7,3,'2025-04-07','2035-04-05'),
(18309,20,7,3,'2025-04-07','2035-04-05'),
(18310,32,25,3,'2025-04-07','2035-04-05'),
(18311,44,7,3,'2025-04-07','2035-04-05'),
(18312,51,3,4,'2025-04-07','2035-04-05'),
(18318,3,2,3,'2024-09-27','2034-09-25'),
(18330,3,5,3,'2024-09-27','2034-09-25'),
(18340,2,5,3,'2022-10-18','2032-10-15'),
(18342,12,30,4,'2025-11-25','2035-11-23'),
(18343,12,32,4,'2025-11-25','2035-11-23'),
(18344,395,30,1,'2025-12-19','2026-01-19'),
(18345,396,30,2,'2026-01-12','2026-02-11'),
(18346,28,29,4,'2025-10-21','2035-10-19'),
(18347,41,33,3,'2025-10-20','2035-10-18'),
(18348,397,32,1,NULL,'2026-01-05'),
(18350,398,25,1,'2025-11-24','2025-12-24'),
(18351,399,32,1,NULL,'2026-02-16'),
(18354,402,31,1,NULL,'2026-02-16'),
(18357,405,5,2,NULL,'2026-02-18'),
(18358,20,3,1,'2026-01-19','2026-02-18'),
(18359,34,2,1,'2026-01-19','2026-02-18'),
(18360,34,3,1,'2026-01-19','2026-02-18'),
(18361,405,2,2,'2026-01-19','2026-02-18'),
(18365,408,31,1,'2026-01-22','2026-02-23'),
(18367,410,30,1,NULL,'2026-03-05'),
(18370,416,1,1,NULL,'2026-03-11');
/*!40000 ALTER TABLE `polyvalence` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tg_polyvalence_date_bi` BEFORE INSERT ON `polyvalence` FOR EACH ROW BEGIN
  IF NEW.prochaine_evaluation IS NOT NULL THEN
    SET NEW.prochaine_evaluation =
      CASE DAYOFWEEK(NEW.prochaine_evaluation)
        WHEN 7 THEN DATE_ADD(NEW.prochaine_evaluation, INTERVAL 2 DAY) 
        WHEN 1 THEN DATE_ADD(NEW.prochaine_evaluation, INTERVAL 1 DAY) 
        ELSE NEW.prochaine_evaluation
      END;
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = cp850 */ ;
/*!50003 SET character_set_results = cp850 */ ;
/*!50003 SET collation_connection  = cp850_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'ONLY_FULL_GROUP_BY,STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tg_polyvalence_date_bu` BEFORE UPDATE ON `polyvalence` FOR EACH ROW BEGIN
  IF NEW.prochaine_evaluation IS NOT NULL THEN
    SET NEW.prochaine_evaluation =
      CASE DAYOFWEEK(NEW.prochaine_evaluation)
        WHEN 7 THEN DATE_ADD(NEW.prochaine_evaluation, INTERVAL 2 DAY)
        WHEN 1 THEN DATE_ADD(NEW.prochaine_evaluation, INTERVAL 1 DAY)
        ELSE NEW.prochaine_evaluation
      END;
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `postes`
--

DROP TABLE IF EXISTS `postes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `postes` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `poste_code` varchar(50) NOT NULL,
  `besoins_postes` int(11) NOT NULL DEFAULT 0,
  `visible` tinyint(1) DEFAULT 1,
  `atelier_id` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_atelier` (`atelier_id`),
  KEY `idx_postes_code` (`poste_code`),
  KEY `idx_postes_atelier` (`atelier_id`),
  CONSTRAINT `fk_atelier` FOREIGN KEY (`atelier_id`) REFERENCES `atelier` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=85 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `postes`
--

LOCK TABLES `postes` WRITE;
/*!40000 ALTER TABLE `postes` DISABLE KEYS */;
INSERT INTO `postes` VALUES
(1,'0506',3,1,5),
(2,'0507',3,1,5),
(3,'0510',3,1,5),
(4,'0514',3,1,5),
(5,'0515',3,1,5),
(6,'0516',2,1,NULL),
(7,'0560',2,1,5),
(8,'0830',3,1,NULL),
(9,'0900',3,1,NULL),
(10,'0901',1,1,NULL),
(11,'0902',1,1,NULL),
(12,'0903',1,1,NULL),
(13,'0906',1,1,NULL),
(14,'0910',2,1,NULL),
(15,'0912',2,1,5),
(16,'0920',2,1,NULL),
(17,'0923',1,1,NULL),
(18,'0924',1,1,NULL),
(19,'0930',2,1,NULL),
(20,'0940',1,1,NULL),
(21,'0941',1,1,NULL),
(22,'0942',1,1,NULL),
(23,'1007',1,1,10),
(24,'1026',1,0,10),
(25,'1100',1,1,11),
(26,'1101',1,1,11),
(27,'1103',1,1,11),
(28,'1121',2,1,11),
(29,'1401',3,1,14),
(30,'1402',3,1,14),
(31,'1404',3,1,14),
(32,'1406',3,1,NULL),
(33,'1412',3,1,14),
(77,'0561',2,1,NULL),
(84,'PRODUCTION',0,1,5);
/*!40000 ALTER TABLE `postes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `ref_motif_sortie`
--

DROP TABLE IF EXISTS `ref_motif_sortie`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `ref_motif_sortie` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `libelle` varchar(100) NOT NULL,
  `actif` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_libelle` (`libelle`)
) ENGINE=InnoDB AUTO_INCREMENT=14 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `ref_motif_sortie`
--

LOCK TABLES `ref_motif_sortie` WRITE;
/*!40000 ALTER TABLE `ref_motif_sortie` DISABLE KEYS */;
INSERT INTO `ref_motif_sortie` VALUES
(1,'Démission',1),
(2,'Licenciement économique',1),
(3,'Licenciement pour faute',1),
(4,'Licenciement pour inaptitude',1),
(5,'Fin de CDD',1),
(6,'Fin de période d\'essai',1),
(7,'Rupture conventionnelle',1),
(8,'Retraite',1),
(9,'Décès',1),
(10,'Mutation',1),
(11,'Fin de mission intérim',1),
(12,'Fin de stage',1),
(13,'Fin d\'apprentissage',1);
/*!40000 ALTER TABLE `ref_motif_sortie` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `role_features`
--

DROP TABLE IF EXISTS `role_features`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `role_features` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `role_id` int(11) NOT NULL,
  `feature_key` varchar(100) NOT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_role_feature` (`role_id`,`feature_key`),
  KEY `idx_role` (`role_id`),
  KEY `idx_feature` (`feature_key`),
  CONSTRAINT `role_features_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=275 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Features assignées à chaque rôle';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `role_features`
--

LOCK TABLES `role_features` WRITE;
/*!40000 ALTER TABLE `role_features` DISABLE KEYS */;
INSERT INTO `role_features` VALUES
(78,3,'rh.view','2026-01-27 12:21:43'),
(79,3,'rh.personnel.view','2026-01-27 12:21:43'),
(80,3,'rh.personnel.create','2026-01-27 12:21:43'),
(81,3,'rh.personnel.edit','2026-01-27 12:21:43'),
(82,3,'rh.personnel.delete','2026-01-27 12:21:43'),
(83,3,'rh.contrats.view','2026-01-27 12:21:43'),
(84,3,'rh.contrats.edit','2026-01-27 12:21:43'),
(85,3,'rh.contrats.delete','2026-01-27 12:21:43'),
(86,3,'rh.documents.view','2026-01-27 12:21:43'),
(87,3,'rh.documents.edit','2026-01-27 12:21:43'),
(88,3,'rh.documents.print','2026-01-27 12:21:43'),
(89,3,'rh.templates.view','2026-01-27 12:21:43'),
(90,3,'rh.templates.edit','2026-01-27 12:21:43'),
(91,3,'production.view','2026-01-27 12:21:43'),
(92,3,'production.polyvalence.view','2026-01-27 12:21:43'),
(93,3,'production.postes.view','2026-01-27 12:21:43'),
(94,3,'production.grilles.view','2026-01-27 12:21:43'),
(95,3,'planning.view','2026-01-27 12:21:43'),
(96,3,'planning.absences.view','2026-01-27 12:21:43'),
(97,3,'planning.absences.edit','2026-01-27 12:21:43'),
(98,3,'admin.historique.view','2026-01-27 12:21:43'),
(195,1,'rh.bulk_operations.formations','2026-02-03 07:51:23'),
(196,1,'rh.competences.view','2026-02-03 07:51:23'),
(197,1,'rh.contrats.view','2026-02-03 07:51:23'),
(198,1,'production.postes.view','2026-02-03 07:51:23'),
(199,1,'rh.templates.edit','2026-02-03 07:51:23'),
(200,1,'admin.users.delete','2026-02-03 07:51:23'),
(201,1,'rh.personnel.edit','2026-02-03 07:51:23'),
(202,1,'admin.roles.edit','2026-02-03 07:51:23'),
(203,1,'production.evaluations.edit','2026-02-03 07:51:23'),
(204,1,'planning.view','2026-02-03 07:51:23'),
(205,1,'admin.view','2026-02-03 07:51:23'),
(206,1,'production.view','2026-02-03 07:51:23'),
(207,1,'rh.competences.delete','2026-02-03 07:51:23'),
(208,1,'rh.view','2026-02-03 07:51:23'),
(209,1,'production.polyvalence.edit','2026-02-03 07:51:23'),
(210,1,'rh.competences.edit','2026-02-03 07:51:23'),
(211,1,'rh.documents.print','2026-02-03 07:51:23'),
(212,1,'rh.competences.catalogue','2026-02-03 07:51:23'),
(213,1,'rh.documents.view','2026-02-03 07:51:23'),
(214,1,'rh.bulk_operations','2026-02-03 07:51:23'),
(215,1,'rh.personnel.create','2026-02-03 07:51:23'),
(216,1,'rh.bulk_operations.absences','2026-02-03 07:51:23'),
(217,1,'admin.users.view','2026-02-03 07:51:23'),
(218,1,'rh.contrats.edit','2026-02-03 07:51:23'),
(219,1,'admin.historique.export','2026-02-03 07:51:23'),
(220,1,'rh.personnel.delete','2026-02-03 07:51:23'),
(221,1,'rh.personnel.view','2026-02-03 07:51:23'),
(222,1,'admin.users.edit','2026-02-03 07:51:23'),
(223,1,'planning.absences.view','2026-02-03 07:51:23'),
(224,1,'rh.contrats.delete','2026-02-03 07:51:23'),
(225,1,'production.polyvalence.view','2026-02-03 07:51:23'),
(226,1,'rh.bulk_operations.medical','2026-02-03 07:51:23'),
(227,1,'production.grilles.view','2026-02-03 07:51:23'),
(228,1,'production.evaluations.view','2026-02-03 07:51:23'),
(229,1,'planning.absences.edit','2026-02-03 07:51:23'),
(230,1,'admin.permissions','2026-02-03 07:51:23'),
(231,1,'production.grilles.export','2026-02-03 07:51:23'),
(232,1,'admin.users.create','2026-02-03 07:51:23'),
(233,1,'rh.documents.edit','2026-02-03 07:51:23'),
(234,1,'production.postes.edit','2026-02-03 07:51:23'),
(235,1,'admin.historique.view','2026-02-03 07:51:23'),
(236,1,'rh.templates.view','2026-02-03 07:51:23'),
(237,1,'rh.formations.view','2026-02-03 07:54:37'),
(238,1,'rh.formations.edit','2026-02-03 07:54:37'),
(239,1,'rh.formations.delete','2026-02-03 07:54:37'),
(240,3,'rh.formations.view','2026-02-03 07:54:37'),
(241,3,'rh.formations.edit','2026-02-03 07:54:37'),
(242,3,'rh.formations.delete','2026-02-03 07:54:37'),
(260,2,'production.postes.view','2026-02-05 13:41:08'),
(261,2,'production.grilles.export','2026-02-05 13:41:08'),
(262,2,'production.view','2026-02-05 13:41:08'),
(263,2,'production.polyvalence.edit','2026-02-05 13:41:08'),
(264,2,'rh.personnel.create','2026-02-05 13:41:08'),
(265,2,'planning.absences.view','2026-02-05 13:41:08'),
(266,2,'production.evaluations.edit','2026-02-05 13:41:08'),
(267,2,'production.postes.edit','2026-02-05 13:41:08'),
(268,2,'rh.personnel.view','2026-02-05 13:41:08'),
(269,2,'production.grilles.view','2026-02-05 13:41:08'),
(270,2,'rh.personnel.edit','2026-02-05 13:41:08'),
(271,2,'rh.personnel.delete','2026-02-05 13:41:08'),
(272,2,'planning.view','2026-02-05 13:41:08'),
(273,2,'production.evaluations.view','2026-02-05 13:41:08'),
(274,2,'production.polyvalence.view','2026-02-05 13:41:08');
/*!40000 ALTER TABLE `role_features` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `roles`
--

DROP TABLE IF EXISTS `roles`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `roles` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(50) NOT NULL,
  `description` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `nom` (`nom`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `roles`
--

LOCK TABLES `roles` WRITE;
/*!40000 ALTER TABLE `roles` DISABLE KEYS */;
INSERT INTO `roles` VALUES
(1,'admin','Administrateur - Accès complet à toutes les fonctionnalités'),
(2,'gestion_production','Gestion Production - Accès aux évaluations et polyvalence (lecture seule sur les contrats)'),
(3,'gestion_rh','Gestion RH - Accès aux contrats et documents administratifs (lecture seule sur la polyvalence)');
/*!40000 ALTER TABLE `roles` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `services`
--

DROP TABLE IF EXISTS `services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `services` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom_service` varchar(100) NOT NULL,
  `description` text DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `services`
--

LOCK TABLES `services` WRITE;
/*!40000 ALTER TABLE `services` DISABLE KEYS */;
INSERT INTO `services` VALUES
(1,'PRODUCTION','Personnel de production'),
(2,'R&D','Recherche et développement'),
(3,'MAINTENANCE','Service maintenance'),
(4,'ADMIN','Administratif'),
(5,'LABO','Laboratoire'),
(6,'HSE','Hygiène, Sécurité, Environnement'),
(7,'METHODES','Méthodes / industrialisation'),
(8,'QUALITE','Service qualité'),
(9,'PRODUCTION','Personnel de production'),
(10,'R&D','Recherche et développement'),
(11,'MAINTENANCE','Service maintenance'),
(12,'ADMIN','Administratif'),
(13,'LABO','Laboratoire'),
(14,'HSE','Hygiène, Sécurité, Environnement'),
(15,'METHODES','Méthodes et industrialisation'),
(16,'QUALITE','Service qualité');
/*!40000 ALTER TABLE `services` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `solde_conges`
--

DROP TABLE IF EXISTS `solde_conges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `solde_conges` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `personnel_id` int(11) NOT NULL,
  `annee` int(11) NOT NULL,
  `cp_acquis` decimal(5,2) DEFAULT 0.00 COMMENT 'CP acquis dans l année',
  `cp_n_1` decimal(5,2) DEFAULT 0.00 COMMENT 'CP reportés de N-1',
  `cp_pris` decimal(5,2) DEFAULT 0.00 COMMENT 'CP déjà pris',
  `rtt_acquis` decimal(5,2) DEFAULT 0.00,
  `rtt_pris` decimal(5,2) DEFAULT 0.00,
  `date_maj` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_personnel_annee` (`personnel_id`,`annee`),
  KEY `idx_annee` (`annee`),
  CONSTRAINT `solde_conges_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=167 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `solde_conges`
--

LOCK TABLES `solde_conges` WRITE;
/*!40000 ALTER TABLE `solde_conges` DISABLE KEYS */;
INSERT INTO `solde_conges` VALUES
(1,2,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(2,3,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(3,5,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(4,6,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(5,7,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(6,8,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(7,9,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(8,10,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(9,11,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(10,12,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(11,13,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(12,14,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(13,15,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(14,16,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(15,17,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(16,18,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(17,20,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(18,22,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(19,23,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(20,24,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(21,25,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(22,26,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(23,27,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(24,28,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(25,29,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(26,30,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(27,32,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(28,33,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(29,34,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(30,36,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(31,37,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(32,38,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(33,39,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(34,40,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(35,41,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(36,42,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(37,43,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(38,44,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(39,45,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(40,46,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(41,47,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(42,48,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(43,49,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(44,50,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(45,51,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(46,52,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(47,76,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(48,99,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(49,100,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(50,108,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(51,111,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(52,112,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(53,114,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(54,116,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(55,118,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(56,120,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(57,124,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(58,126,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(59,128,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(60,136,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(61,138,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(62,142,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(63,144,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(64,148,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(65,150,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(66,152,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(67,154,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(68,155,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(69,157,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(70,159,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(71,161,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(72,163,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(73,165,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(74,167,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(75,169,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(76,171,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(77,173,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(78,175,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(79,177,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(80,179,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(81,181,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(82,183,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(83,185,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(84,187,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(85,189,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(86,191,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(87,193,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(88,195,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(89,197,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(90,199,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(91,203,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(92,205,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(93,207,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(94,209,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(95,211,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(96,213,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(97,215,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(98,219,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(99,221,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(100,223,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(101,225,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(102,227,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(103,229,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(104,231,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(105,233,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(106,235,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(107,237,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(108,238,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(109,240,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(110,242,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(111,244,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(112,246,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(113,248,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(114,250,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(115,252,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(116,254,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(117,256,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(118,258,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(119,260,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(120,262,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(121,264,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(122,266,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(123,268,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(124,270,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(125,272,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(126,274,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(127,276,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(128,278,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(129,280,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(130,282,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(131,284,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(132,286,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(133,288,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(134,290,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(135,292,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(136,294,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(137,296,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(138,302,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(139,304,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(140,308,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(141,310,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(142,314,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(143,316,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(144,318,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(145,320,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(146,322,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(147,326,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(148,328,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(149,330,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(150,332,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(151,335,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(152,337,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(153,339,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(154,341,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(155,342,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(156,343,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(157,344,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(158,348,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(159,349,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(160,357,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(161,359,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(162,361,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(163,363,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(164,365,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(165,367,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),
(166,369,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50');
/*!40000 ALTER TABLE `solde_conges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tranche_age`
--

DROP TABLE IF EXISTS `tranche_age`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `tranche_age` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `libelle` varchar(50) NOT NULL,
  `age_min` int(11) NOT NULL,
  `age_max` int(11) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tranche_age`
--

LOCK TABLES `tranche_age` WRITE;
/*!40000 ALTER TABLE `tranche_age` DISABLE KEYS */;
INSERT INTO `tranche_age` VALUES
(1,'0-25 ans',0,25),
(2,'26-45 ans',26,45),
(3,'46-54 ans',46,54),
(4,'55 ans et +',55,NULL);
/*!40000 ALTER TABLE `tranche_age` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `type_absence`
--

DROP TABLE IF EXISTS `type_absence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `type_absence` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `code` varchar(20) NOT NULL,
  `libelle` varchar(100) NOT NULL,
  `decompte_solde` tinyint(1) DEFAULT 1 COMMENT 'Si TRUE, décompte du solde de congés',
  `couleur` varchar(7) DEFAULT '#3498db' COMMENT 'Couleur pour le calendrier (format hex)',
  `actif` tinyint(1) DEFAULT 1,
  PRIMARY KEY (`id`),
  UNIQUE KEY `code` (`code`),
  KEY `idx_code` (`code`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `type_absence`
--

LOCK TABLES `type_absence` WRITE;
/*!40000 ALTER TABLE `type_absence` DISABLE KEYS */;
INSERT INTO `type_absence` VALUES
(1,'CP','Congés Payés',1,'#27ae60',1),
(2,'RTT','RTT',1,'#3498db',1),
(3,'MALADIE','Arrêt Maladie',0,'#e74c3c',1),
(4,'SANS_SOLDE','Congé Sans Solde',0,'#95a5a6',1),
(5,'MATERNITE','Congé Maternité',0,'#e91e63',1),
(6,'PATERNITE','Congé Paternité',0,'#9c27b0',1),
(7,'FORMATION','Formation',0,'#ff9800',1),
(8,'EVENEMENT','Événement Familial',0,'#00bcd4',1),
(9,'AUTRE','Autre',0,'#607d8b',1);
/*!40000 ALTER TABLE `type_absence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_features`
--

DROP TABLE IF EXISTS `user_features`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_features` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `user_id` int(11) NOT NULL,
  `feature_key` varchar(100) NOT NULL,
  `value` tinyint(1) NOT NULL COMMENT 'TRUE=autorisé, FALSE=refusé (override du rôle)',
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `modifie_par` int(11) DEFAULT NULL COMMENT 'Admin qui a fait la modification',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_user_feature` (`user_id`,`feature_key`),
  KEY `modifie_par` (`modifie_par`),
  KEY `idx_user` (`user_id`),
  KEY `idx_feature` (`feature_key`),
  CONSTRAINT `user_features_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `utilisateurs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `user_features_ibfk_2` FOREIGN KEY (`modifie_par`) REFERENCES `utilisateurs` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Overrides de permissions par utilisateur. Override > rôle.';
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_features`
--

LOCK TABLES `user_features` WRITE;
/*!40000 ALTER TABLE `user_features` DISABLE KEYS */;
/*!40000 ALTER TABLE `user_features` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `utilisateurs`
--

DROP TABLE IF EXISTS `utilisateurs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `utilisateurs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `username` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `nom` varchar(255) NOT NULL,
  `prenom` varchar(255) NOT NULL,
  `role_id` int(11) NOT NULL,
  `actif` tinyint(1) DEFAULT 1,
  `date_creation` datetime DEFAULT current_timestamp(),
  `derniere_connexion` datetime DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `username` (`username`),
  KEY `role_id` (`role_id`),
  CONSTRAINT `utilisateurs_ibfk_1` FOREIGN KEY (`role_id`) REFERENCES `roles` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `utilisateurs`
--

LOCK TABLES `utilisateurs` WRITE;
/*!40000 ALTER TABLE `utilisateurs` DISABLE KEYS */;
INSERT INTO `utilisateurs` VALUES
(1,'admin','$2b$12$N2q3r.7Vj4PvKAuIsJ1gyusJpxhuxZ1OYq4U59CHKDhMWoX/gCWCS','Administrateur','Système',1,1,'2025-12-18 09:25:29','2026-02-11 14:38:03'),
(2,'gprod','$2b$12$HMZApTivL.54rMHJUkLrEez552nW2Bq.lJusvGn3eilym.9nCT3bG','Gestion','Production',2,1,'2026-01-13 11:03:17','2026-02-05 16:44:10'),
(4,'test','$2b$12$bnOqvAkH0rEGOwxiXDxgBu3vMCUt5UH2CdTEs.4c0XnuyiwbTzSa2','test','test',3,1,'2026-02-05 09:29:19','2026-02-05 09:35:14');
/*!40000 ALTER TABLE `utilisateurs` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary table structure for view `v_absences_details`
--

DROP TABLE IF EXISTS `v_absences_details`;
/*!50001 DROP VIEW IF EXISTS `v_absences_details`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_absences_details` AS SELECT
 1 AS `id`,
  1 AS `personnel_id`,
  1 AS `nom_complet`,
  1 AS `matricule`,
  1 AS `type_code`,
  1 AS `type_libelle`,
  1 AS `couleur`,
  1 AS `date_debut`,
  1 AS `date_fin`,
  1 AS `demi_journee_debut`,
  1 AS `demi_journee_fin`,
  1 AS `nb_jours`,
  1 AS `motif`,
  1 AS `statut`,
  1 AS `validateur`,
  1 AS `date_validation`,
  1 AS `commentaire_validation`,
  1 AS `date_creation` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_alertes_entretiens`
--

DROP TABLE IF EXISTS `v_alertes_entretiens`;
/*!50001 DROP VIEW IF EXISTS `v_alertes_entretiens`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_alertes_entretiens` AS SELECT
 1 AS `operateur_id`,
  1 AS `nom`,
  1 AS `prenom`,
  1 AS `matricule`,
  1 AS `type_alerte`,
  1 AS `derniere_date`,
  1 AS `jours_retard` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_alertes_medicales`
--

DROP TABLE IF EXISTS `v_alertes_medicales`;
/*!50001 DROP VIEW IF EXISTS `v_alertes_medicales`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_alertes_medicales` AS SELECT
 1 AS `operateur_id`,
  1 AS `nom`,
  1 AS `prenom`,
  1 AS `matricule`,
  1 AS `type_alerte`,
  1 AS `date_alerte`,
  1 AS `jours_retard` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_batch_operations_stats`
--

DROP TABLE IF EXISTS `v_batch_operations_stats`;
/*!50001 DROP VIEW IF EXISTS `v_batch_operations_stats`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_batch_operations_stats` AS SELECT
 1 AS `id`,
  1 AS `operation_type`,
  1 AS `description`,
  1 AS `nb_personnel`,
  1 AS `nb_success`,
  1 AS `nb_errors`,
  1 AS `created_by`,
  1 AS `created_at`,
  1 AS `completed_at`,
  1 AS `status`,
  1 AS `duration_seconds`,
  1 AS `success_rate` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_contrat_anciennete`
--

DROP TABLE IF EXISTS `v_contrat_anciennete`;
/*!50001 DROP VIEW IF EXISTS `v_contrat_anciennete`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_contrat_anciennete` AS SELECT
 1 AS `id`,
  1 AS `operateur_id`,
  1 AS `nom`,
  1 AS `prenom`,
  1 AS `matricule`,
  1 AS `type_contrat`,
  1 AS `date_debut`,
  1 AS `date_fin`,
  1 AS `date_sortie`,
  1 AS `actif`,
  1 AS `anciennete_annees`,
  1 AS `anciennete_detail`,
  1 AS `jours_restants` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_contrats_fin_proche`
--

DROP TABLE IF EXISTS `v_contrats_fin_proche`;
/*!50001 DROP VIEW IF EXISTS `v_contrats_fin_proche`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_contrats_fin_proche` AS SELECT
 1 AS `id`,
  1 AS `operateur_id`,
  1 AS `nom`,
  1 AS `prenom`,
  1 AS `matricule`,
  1 AS `type_contrat`,
  1 AS `date_debut`,
  1 AS `date_fin`,
  1 AS `jours_restants`,
  1 AS `statut_alerte` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_document_rules_with_templates`
--

DROP TABLE IF EXISTS `v_document_rules_with_templates`;
/*!50001 DROP VIEW IF EXISTS `v_document_rules_with_templates`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_document_rules_with_templates` AS SELECT
 1 AS `rule_id`,
  1 AS `event_name`,
  1 AS `execution_mode`,
  1 AS `condition_json`,
  1 AS `priority`,
  1 AS `rule_actif`,
  1 AS `template_id`,
  1 AS `template_nom`,
  1 AS `fichier_source`,
  1 AS `contexte`,
  1 AS `postes_associes`,
  1 AS `champ_operateur`,
  1 AS `champ_auditeur`,
  1 AS `champ_date`,
  1 AS `obligatoire`,
  1 AS `template_description` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_documents_complet`
--

DROP TABLE IF EXISTS `v_documents_complet`;
/*!50001 DROP VIEW IF EXISTS `v_documents_complet`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_documents_complet` AS SELECT
 1 AS `id`,
  1 AS `personnel_id`,
  1 AS `categorie_id`,
  1 AS `formation_id`,
  1 AS `contrat_id`,
  1 AS `declaration_id`,
  1 AS `nom_fichier`,
  1 AS `nom_affichage`,
  1 AS `chemin_fichier`,
  1 AS `type_mime`,
  1 AS `taille_octets`,
  1 AS `date_expiration`,
  1 AS `notes`,
  1 AS `uploaded_by`,
  1 AS `statut`,
  1 AS `date_upload`,
  1 AS `date_modification`,
  1 AS `personnel_nom`,
  1 AS `personnel_prenom`,
  1 AS `personnel_matricule`,
  1 AS `categorie_nom`,
  1 AS `categorie_description`,
  1 AS `categorie_couleur`,
  1 AS `formation_intitule`,
  1 AS `formation_date_debut`,
  1 AS `contrat_type`,
  1 AS `contrat_date_debut`,
  1 AS `contrat_date_fin`,
  1 AS `etat_expiration`,
  1 AS `jours_avant_expiration` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_documents_stats_operateur`
--

DROP TABLE IF EXISTS `v_documents_stats_operateur`;
/*!50001 DROP VIEW IF EXISTS `v_documents_stats_operateur`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_documents_stats_operateur` AS SELECT
 1 AS `operateur_id`,
  1 AS `matricule`,
  1 AS `operateur_nom`,
  1 AS `total_documents`,
  1 AS `documents_actifs`,
  1 AS `documents_expires`,
  1 AS `documents_expire_bientot`,
  1 AS `taille_totale_octets`,
  1 AS `taille_totale_mo`,
  1 AS `derniere_mise_a_jour` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_historique_polyvalence_complet`
--

DROP TABLE IF EXISTS `v_historique_polyvalence_complet`;
/*!50001 DROP VIEW IF EXISTS `v_historique_polyvalence_complet`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_historique_polyvalence_complet` AS SELECT
 1 AS `id`,
  1 AS `date_action`,
  1 AS `action_type`,
  1 AS `operateur_nom`,
  1 AS `operateur_prenom`,
  1 AS `operateur_matricule`,
  1 AS `operateur_id`,
  1 AS `poste_code`,
  1 AS `poste_id`,
  1 AS `ancien_niveau`,
  1 AS `ancienne_date_evaluation`,
  1 AS `ancienne_prochaine_evaluation`,
  1 AS `ancien_statut`,
  1 AS `nouveau_niveau`,
  1 AS `nouvelle_date_evaluation`,
  1 AS `nouvelle_prochaine_evaluation`,
  1 AS `nouveau_statut`,
  1 AS `utilisateur`,
  1 AS `commentaire`,
  1 AS `source`,
  1 AS `import_batch_id`,
  1 AS `metadata_json`,
  1 AS `resume` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_personnel_age`
--

DROP TABLE IF EXISTS `v_personnel_age`;
/*!50001 DROP VIEW IF EXISTS `v_personnel_age`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_personnel_age` AS SELECT
 1 AS `id`,
  1 AS `nom`,
  1 AS `prenom`,
  1 AS `matricule`,
  1 AS `statut`,
  1 AS `date_naissance`,
  1 AS `age`,
  1 AS `tranche_age` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_personnel_anciennete`
--

DROP TABLE IF EXISTS `v_personnel_anciennete`;
/*!50001 DROP VIEW IF EXISTS `v_personnel_anciennete`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_personnel_anciennete` AS SELECT
 1 AS `id`,
  1 AS `nom`,
  1 AS `prenom`,
  1 AS `matricule`,
  1 AS `statut`,
  1 AS `date_entree`,
  1 AS `anciennete_annees`,
  1 AS `anciennete_mois`,
  1 AS `anciennete_jours`,
  1 AS `anciennete_texte` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_soldes_disponibles`
--

DROP TABLE IF EXISTS `v_soldes_disponibles`;
/*!50001 DROP VIEW IF EXISTS `v_soldes_disponibles`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_soldes_disponibles` AS SELECT
 1 AS `id`,
  1 AS `personnel_id`,
  1 AS `nom_complet`,
  1 AS `matricule`,
  1 AS `annee`,
  1 AS `cp_acquis`,
  1 AS `cp_n_1`,
  1 AS `cp_pris`,
  1 AS `cp_restant`,
  1 AS `rtt_acquis`,
  1 AS `rtt_pris`,
  1 AS `rtt_restant`,
  1 AS `date_maj` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_stats_absences`
--

DROP TABLE IF EXISTS `v_stats_absences`;
/*!50001 DROP VIEW IF EXISTS `v_stats_absences`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_stats_absences` AS SELECT
 1 AS `personnel_id`,
  1 AS `nom_complet`,
  1 AS `annee`,
  1 AS `type_absence`,
  1 AS `nb_demandes`,
  1 AS `total_jours`,
  1 AS `jours_valides`,
  1 AS `jours_en_attente` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_suivi_medical`
--

DROP TABLE IF EXISTS `v_suivi_medical`;
/*!50001 DROP VIEW IF EXISTS `v_suivi_medical`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_suivi_medical` AS SELECT
 1 AS `operateur_id`,
  1 AS `nom`,
  1 AS `prenom`,
  1 AS `matricule`,
  1 AS `statut`,
  1 AS `type_suivi_vip`,
  1 AS `periodicite_vip_mois`,
  1 AS `derniere_visite`,
  1 AS `prochaine_visite`,
  1 AS `statut_visite`,
  1 AS `date_debut_rqth`,
  1 AS `date_fin_rqth`,
  1 AS `statut_rqth`,
  1 AS `date_debut_oeth`,
  1 AS `date_fin_oeth`,
  1 AS `taux_incapacite`,
  1 AS `maladie_pro`,
  1 AS `nb_accidents` */;
SET character_set_client = @saved_cs_client;

--
-- Temporary table structure for view `v_vie_salarie_recap`
--

DROP TABLE IF EXISTS `v_vie_salarie_recap`;
/*!50001 DROP VIEW IF EXISTS `v_vie_salarie_recap`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
/*!50001 CREATE VIEW `v_vie_salarie_recap` AS SELECT
 1 AS `operateur_id`,
  1 AS `nom`,
  1 AS `prenom`,
  1 AS `statut`,
  1 AS `nb_sanctions`,
  1 AS `derniere_sanction`,
  1 AS `nb_controles_alcool`,
  1 AS `nb_positifs_alcool`,
  1 AS `nb_tests_salivaires`,
  1 AS `nb_positifs_salivaire`,
  1 AS `dernier_epp`,
  1 AS `dernier_eap`,
  1 AS `prochain_entretien` */;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `validite`
--

DROP TABLE IF EXISTS `validite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `validite` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `type_validite` enum('RQTH','OETH') NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `periodicite` enum('Périodique','Permanent') DEFAULT 'Périodique',
  `taux_incapacite` decimal(5,2) DEFAULT NULL COMMENT 'Pourcentage pour RQTH',
  `document_justificatif` varchar(255) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `date_creation` timestamp NULL DEFAULT current_timestamp(),
  `date_modification` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_type` (`type_validite`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  CONSTRAINT `fk_validite_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `validite`
--

LOCK TABLES `validite` WRITE;
/*!40000 ALTER TABLE `validite` DISABLE KEYS */;
/*!40000 ALTER TABLE `validite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vie_salarie_alcoolemie`
--

DROP TABLE IF EXISTS `vie_salarie_alcoolemie`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `vie_salarie_alcoolemie` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `date_controle` datetime NOT NULL,
  `resultat` enum('Négatif','Positif') NOT NULL,
  `taux` decimal(4,2) DEFAULT NULL,
  `type_controle` enum('Aléatoire','Ciblé','Accident') DEFAULT 'Aléatoire',
  `commentaire` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_alcool_operateur` (`operateur_id`),
  KEY `idx_alcool_date` (`date_controle`),
  KEY `idx_alcool_resultat` (`resultat`),
  CONSTRAINT `fk_alcool_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vie_salarie_alcoolemie`
--

LOCK TABLES `vie_salarie_alcoolemie` WRITE;
/*!40000 ALTER TABLE `vie_salarie_alcoolemie` DISABLE KEYS */;
/*!40000 ALTER TABLE `vie_salarie_alcoolemie` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vie_salarie_entretien`
--

DROP TABLE IF EXISTS `vie_salarie_entretien`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `vie_salarie_entretien` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `type_entretien` enum('EPP','EAP','Bilan 6 ans','Entretien annuel','Autre') NOT NULL,
  `date_entretien` date NOT NULL,
  `manager_id` int(11) DEFAULT NULL,
  `objectifs_atteints` text DEFAULT NULL,
  `objectifs_fixes` text DEFAULT NULL,
  `besoins_formation` text DEFAULT NULL,
  `souhaits_evolution` text DEFAULT NULL,
  `commentaire_salarie` text DEFAULT NULL,
  `commentaire_manager` text DEFAULT NULL,
  `document_reference` varchar(255) DEFAULT NULL,
  `prochaine_date` date DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_entretien_operateur` (`operateur_id`),
  KEY `idx_entretien_date` (`date_entretien`),
  KEY `idx_entretien_type` (`type_entretien`),
  KEY `idx_entretien_manager` (`manager_id`),
  CONSTRAINT `fk_entretien_manager` FOREIGN KEY (`manager_id`) REFERENCES `personnel` (`id`) ON DELETE SET NULL,
  CONSTRAINT `fk_entretien_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vie_salarie_entretien`
--

LOCK TABLES `vie_salarie_entretien` WRITE;
/*!40000 ALTER TABLE `vie_salarie_entretien` DISABLE KEYS */;
/*!40000 ALTER TABLE `vie_salarie_entretien` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vie_salarie_sanction`
--

DROP TABLE IF EXISTS `vie_salarie_sanction`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `vie_salarie_sanction` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `type_sanction` enum('Observation verbale','Observation écrite','Avertissement','Mise à pied disciplinaire','Mise à pied conservatoire') NOT NULL,
  `date_sanction` date NOT NULL,
  `duree_jours` int(11) DEFAULT NULL,
  `motif` text DEFAULT NULL,
  `document_reference` varchar(255) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_sanction_operateur` (`operateur_id`),
  KEY `idx_sanction_date` (`date_sanction`),
  KEY `idx_sanction_type` (`type_sanction`),
  CONSTRAINT `fk_sanction_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vie_salarie_sanction`
--

LOCK TABLES `vie_salarie_sanction` WRITE;
/*!40000 ALTER TABLE `vie_salarie_sanction` DISABLE KEYS */;
/*!40000 ALTER TABLE `vie_salarie_sanction` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vie_salarie_test_salivaire`
--

DROP TABLE IF EXISTS `vie_salarie_test_salivaire`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `vie_salarie_test_salivaire` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `date_test` datetime NOT NULL,
  `resultat` enum('Négatif','Positif','Non concluant') NOT NULL,
  `type_controle` enum('Aléatoire','Ciblé','Accident') DEFAULT 'Aléatoire',
  `commentaire` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id`),
  KEY `idx_salivaire_operateur` (`operateur_id`),
  KEY `idx_salivaire_date` (`date_test`),
  KEY `idx_salivaire_resultat` (`resultat`),
  CONSTRAINT `fk_salivaire_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vie_salarie_test_salivaire`
--

LOCK TABLES `vie_salarie_test_salivaire` WRITE;
/*!40000 ALTER TABLE `vie_salarie_test_salivaire` DISABLE KEYS */;
/*!40000 ALTER TABLE `vie_salarie_test_salivaire` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping events for database 'emac_db'
--

--
-- Dumping routines for database 'emac_db'
--

--
-- Final view structure for view `v_absences_details`
--

/*!50001 DROP VIEW IF EXISTS `v_absences_details`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_absences_details` AS select `da`.`id` AS `id`,`da`.`personnel_id` AS `personnel_id`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `nom_complet`,`p`.`matricule` AS `matricule`,`ta`.`code` AS `type_code`,`ta`.`libelle` AS `type_libelle`,`ta`.`couleur` AS `couleur`,`da`.`date_debut` AS `date_debut`,`da`.`date_fin` AS `date_fin`,`da`.`demi_journee_debut` AS `demi_journee_debut`,`da`.`demi_journee_fin` AS `demi_journee_fin`,`da`.`nb_jours` AS `nb_jours`,`da`.`motif` AS `motif`,`da`.`statut` AS `statut`,case when `da`.`validateur_id` is not null then concat(`v`.`prenom`,' ',`v`.`nom`) else NULL end AS `validateur`,`da`.`date_validation` AS `date_validation`,`da`.`commentaire_validation` AS `commentaire_validation`,`da`.`date_creation` AS `date_creation` from (((`demande_absence` `da` join `personnel` `p` on(`da`.`personnel_id` = `p`.`id`)) join `type_absence` `ta` on(`da`.`type_absence_id` = `ta`.`id`)) left join `personnel` `v` on(`da`.`validateur_id` = `v`.`id`)) where `p`.`statut` = 'ACTIF' */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_alertes_entretiens`
--

/*!50001 DROP VIEW IF EXISTS `v_alertes_entretiens`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_alertes_entretiens` AS select `p`.`id` AS `operateur_id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`matricule` AS `matricule`,'EPP en retard' AS `type_alerte`,coalesce((select max(`e`.`date_entretien`) from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` and `e`.`type_entretien` = 'EPP'),`pi`.`date_entree`) AS `derniere_date`,to_days(curdate()) - to_days(coalesce((select max(`e`.`date_entretien`) from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` and `e`.`type_entretien` = 'EPP'),`pi`.`date_entree`) + interval 2 year) AS `jours_retard` from (`personnel` `p` left join `personnel_infos` `pi` on(`p`.`id` = `pi`.`personnel_id`)) where `p`.`statut` = 'ACTIF' and to_days(curdate()) - to_days(coalesce((select max(`e`.`date_entretien`) from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` and `e`.`type_entretien` = 'EPP'),`pi`.`date_entree`) + interval 2 year) > 0 union all select `p`.`id` AS `operateur_id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`matricule` AS `matricule`,'EAP en retard' AS `type_alerte`,(select max(`e`.`date_entretien`) from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` and `e`.`type_entretien` = 'EAP') AS `derniere_date`,to_days(curdate()) - to_days((select max(`e`.`date_entretien`) from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` and `e`.`type_entretien` = 'EAP') + interval 1 year) AS `jours_retard` from `personnel` `p` where `p`.`statut` = 'ACTIF' and (select max(`e`.`date_entretien`) from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` and `e`.`type_entretien` = 'EAP') is not null and to_days(curdate()) - to_days((select max(`e`.`date_entretien`) from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` and `e`.`type_entretien` = 'EAP') + interval 1 year) > 0 */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_alertes_medicales`
--

/*!50001 DROP VIEW IF EXISTS `v_alertes_medicales`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_alertes_medicales` AS select `p`.`id` AS `operateur_id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`matricule` AS `matricule`,'Visite médicale en retard' AS `type_alerte`,`mv`.`prochaine_visite` AS `date_alerte`,to_days(curdate()) - to_days(`mv`.`prochaine_visite`) AS `jours_retard` from (`personnel` `p` join `medical_visite` `mv` on(`p`.`id` = `mv`.`operateur_id`)) where `p`.`statut` = 'ACTIF' and `mv`.`prochaine_visite` < curdate() and `mv`.`id` = (select max(`medical_visite`.`id`) from `medical_visite` where `medical_visite`.`operateur_id` = `p`.`id`) union all select `p`.`id` AS `operateur_id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`matricule` AS `matricule`,'RQTH expirant bientôt' AS `type_alerte`,`v`.`date_fin` AS `date_alerte`,to_days(`v`.`date_fin`) - to_days(curdate()) AS `jours_retard` from (`personnel` `p` join `validite` `v` on(`p`.`id` = `v`.`operateur_id`)) where `p`.`statut` = 'ACTIF' and `v`.`type_validite` = 'RQTH' and `v`.`date_fin` between curdate() and curdate() + interval 90 day */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_batch_operations_stats`
--

/*!50001 DROP VIEW IF EXISTS `v_batch_operations_stats`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_batch_operations_stats` AS select `bo`.`id` AS `id`,`bo`.`operation_type` AS `operation_type`,`bo`.`description` AS `description`,`bo`.`nb_personnel` AS `nb_personnel`,`bo`.`nb_success` AS `nb_success`,`bo`.`nb_errors` AS `nb_errors`,`bo`.`created_by` AS `created_by`,`bo`.`created_at` AS `created_at`,`bo`.`completed_at` AS `completed_at`,`bo`.`status` AS `status`,timestampdiff(SECOND,`bo`.`created_at`,coalesce(`bo`.`completed_at`,current_timestamp())) AS `duration_seconds`,round(`bo`.`nb_success` * 100.0 / nullif(`bo`.`nb_personnel`,0),1) AS `success_rate` from `batch_operations` `bo` order by `bo`.`created_at` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_contrat_anciennete`
--

/*!50001 DROP VIEW IF EXISTS `v_contrat_anciennete`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_contrat_anciennete` AS select `c`.`id` AS `id`,`c`.`operateur_id` AS `operateur_id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`matricule` AS `matricule`,`c`.`type_contrat` AS `type_contrat`,`c`.`date_debut` AS `date_debut`,`c`.`date_fin` AS `date_fin`,`c`.`date_sortie` AS `date_sortie`,`c`.`actif` AS `actif`,round((to_days(coalesce(`c`.`date_sortie`,curdate())) - to_days(`c`.`date_debut`)) / 365.25,2) AS `anciennete_annees`,concat(timestampdiff(YEAR,`c`.`date_debut`,coalesce(`c`.`date_sortie`,curdate())),' ans ',timestampdiff(MONTH,`c`.`date_debut`,coalesce(`c`.`date_sortie`,curdate())) MOD 12,' mois') AS `anciennete_detail`,case when `c`.`type_contrat` in ('CDD','Intérimaire','Stagiaire','Apprentissage') and `c`.`date_fin` is not null and `c`.`date_sortie` is null then to_days(`c`.`date_fin`) - to_days(curdate()) else NULL end AS `jours_restants` from (`contrat` `c` join `personnel` `p` on(`c`.`operateur_id` = `p`.`id`)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_contrats_fin_proche`
--

/*!50001 DROP VIEW IF EXISTS `v_contrats_fin_proche`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_contrats_fin_proche` AS select `c`.`id` AS `id`,`c`.`operateur_id` AS `operateur_id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`matricule` AS `matricule`,`c`.`type_contrat` AS `type_contrat`,`c`.`date_debut` AS `date_debut`,`c`.`date_fin` AS `date_fin`,to_days(`c`.`date_fin`) - to_days(curdate()) AS `jours_restants`,case when to_days(`c`.`date_fin`) - to_days(curdate()) < 0 then 'EXPIRE' when to_days(`c`.`date_fin`) - to_days(curdate()) <= 7 then 'URGENT' when to_days(`c`.`date_fin`) - to_days(curdate()) <= 30 then 'ATTENTION' else 'OK' end AS `statut_alerte` from (`contrat` `c` join `personnel` `p` on(`c`.`operateur_id` = `p`.`id`)) where `c`.`actif` = 1 and `c`.`date_fin` is not null and `c`.`date_sortie` is null and to_days(`c`.`date_fin`) - to_days(curdate()) <= 60 order by `c`.`date_fin` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_document_rules_with_templates`
--

/*!50001 DROP VIEW IF EXISTS `v_document_rules_with_templates`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_document_rules_with_templates` AS select `r`.`id` AS `rule_id`,`r`.`event_name` AS `event_name`,`r`.`execution_mode` AS `execution_mode`,`r`.`condition_json` AS `condition_json`,`r`.`priority` AS `priority`,`r`.`actif` AS `rule_actif`,`t`.`id` AS `template_id`,`t`.`nom` AS `template_nom`,`t`.`fichier_source` AS `fichier_source`,`t`.`contexte` AS `contexte`,`t`.`postes_associes` AS `postes_associes`,`t`.`champ_operateur` AS `champ_operateur`,`t`.`champ_auditeur` AS `champ_auditeur`,`t`.`champ_date` AS `champ_date`,`t`.`obligatoire` AS `obligatoire`,`t`.`description` AS `template_description` from (`document_event_rules` `r` join `documents_templates` `t` on(`r`.`template_id` = `t`.`id`)) where `r`.`actif` = 1 and `t`.`actif` = 1 order by `r`.`event_name`,`r`.`priority` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_documents_complet`
--

/*!50001 DROP VIEW IF EXISTS `v_documents_complet`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_documents_complet` AS select `d`.`id` AS `id`,`d`.`personnel_id` AS `personnel_id`,`d`.`categorie_id` AS `categorie_id`,`d`.`formation_id` AS `formation_id`,`d`.`contrat_id` AS `contrat_id`,`d`.`declaration_id` AS `declaration_id`,`d`.`nom_fichier` AS `nom_fichier`,`d`.`nom_affichage` AS `nom_affichage`,`d`.`chemin_fichier` AS `chemin_fichier`,`d`.`type_mime` AS `type_mime`,`d`.`taille_octets` AS `taille_octets`,`d`.`date_expiration` AS `date_expiration`,`d`.`notes` AS `notes`,`d`.`uploaded_by` AS `uploaded_by`,`d`.`statut` AS `statut`,`d`.`date_upload` AS `date_upload`,`d`.`date_modification` AS `date_modification`,`p`.`nom` AS `personnel_nom`,`p`.`prenom` AS `personnel_prenom`,`p`.`matricule` AS `personnel_matricule`,`c`.`nom` AS `categorie_nom`,`c`.`description` AS `categorie_description`,`c`.`couleur` AS `categorie_couleur`,`f`.`intitule` AS `formation_intitule`,`f`.`date_debut` AS `formation_date_debut`,`ct`.`type_contrat` AS `contrat_type`,`ct`.`date_debut` AS `contrat_date_debut`,`ct`.`date_fin` AS `contrat_date_fin`,case when `d`.`date_expiration` is null then 'non_applicable' when `d`.`date_expiration` < curdate() then 'expire' when `d`.`date_expiration` <= curdate() + interval 30 day then 'expire_bientot' else 'valide' end AS `etat_expiration`,case when `d`.`date_expiration` is not null then to_days(`d`.`date_expiration`) - to_days(curdate()) else NULL end AS `jours_avant_expiration` from ((((`documents` `d` join `personnel` `p` on(`d`.`personnel_id` = `p`.`id`)) join `categories_documents` `c` on(`d`.`categorie_id` = `c`.`id`)) left join `formation` `f` on(`d`.`formation_id` = `f`.`id`)) left join `contrat` `ct` on(`d`.`contrat_id` = `ct`.`id`)) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_documents_stats_operateur`
--

/*!50001 DROP VIEW IF EXISTS `v_documents_stats_operateur`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_documents_stats_operateur` AS select `p`.`id` AS `operateur_id`,`p`.`matricule` AS `matricule`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `operateur_nom`,count(`d`.`id`) AS `total_documents`,sum(case when `d`.`statut` = 'actif' then 1 else 0 end) AS `documents_actifs`,sum(case when `d`.`statut` = 'expire' then 1 else 0 end) AS `documents_expires`,sum(case when `d`.`date_expiration` is not null and `d`.`date_expiration` <= curdate() + interval 30 day and `d`.`date_expiration` >= curdate() then 1 else 0 end) AS `documents_expire_bientot`,sum(`d`.`taille_octets`) AS `taille_totale_octets`,round(sum(`d`.`taille_octets`) / 1048576,2) AS `taille_totale_mo`,max(`d`.`date_upload`) AS `derniere_mise_a_jour` from (`personnel` `p` left join `documents` `d` on(`p`.`id` = `d`.`personnel_id`)) group by `p`.`id`,`p`.`matricule`,`p`.`prenom`,`p`.`nom` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_historique_polyvalence_complet`
--

/*!50001 DROP VIEW IF EXISTS `v_historique_polyvalence_complet`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_historique_polyvalence_complet` AS select `hp`.`id` AS `id`,`hp`.`date_action` AS `date_action`,`hp`.`action_type` AS `action_type`,`pers`.`nom` AS `operateur_nom`,`pers`.`prenom` AS `operateur_prenom`,`pers`.`matricule` AS `operateur_matricule`,`hp`.`operateur_id` AS `operateur_id`,`pos`.`poste_code` AS `poste_code`,`hp`.`poste_id` AS `poste_id`,`hp`.`ancien_niveau` AS `ancien_niveau`,`hp`.`ancienne_date_evaluation` AS `ancienne_date_evaluation`,`hp`.`ancienne_prochaine_evaluation` AS `ancienne_prochaine_evaluation`,`hp`.`ancien_statut` AS `ancien_statut`,`hp`.`nouveau_niveau` AS `nouveau_niveau`,`hp`.`nouvelle_date_evaluation` AS `nouvelle_date_evaluation`,`hp`.`nouvelle_prochaine_evaluation` AS `nouvelle_prochaine_evaluation`,`hp`.`nouveau_statut` AS `nouveau_statut`,`hp`.`utilisateur` AS `utilisateur`,`hp`.`commentaire` AS `commentaire`,`hp`.`source` AS `source`,`hp`.`import_batch_id` AS `import_batch_id`,`hp`.`metadata_json` AS `metadata_json`,case when `hp`.`action_type` = 'AJOUT' then concat('Ajout niveau ',`hp`.`nouveau_niveau`) when `hp`.`action_type` = 'MODIFICATION' then concat('Modification : N',`hp`.`ancien_niveau`,' → N',`hp`.`nouveau_niveau`) when `hp`.`action_type` = 'SUPPRESSION' then concat('Suppression niveau ',`hp`.`ancien_niveau`) when `hp`.`action_type` = 'IMPORT_MANUEL' then concat('Import manuel : ',coalesce(`hp`.`commentaire`,'')) end AS `resume` from ((`historique_polyvalence` `hp` left join `personnel` `pers` on(`hp`.`operateur_id` = `pers`.`id`)) left join `postes` `pos` on(`hp`.`poste_id` = `pos`.`id`)) order by `hp`.`date_action` desc */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_personnel_age`
--

/*!50001 DROP VIEW IF EXISTS `v_personnel_age`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_personnel_age` AS select `p`.`id` AS `id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`matricule` AS `matricule`,`p`.`statut` AS `statut`,`pi`.`date_naissance` AS `date_naissance`,timestampdiff(YEAR,`pi`.`date_naissance`,curdate()) AS `age`,`ta`.`libelle` AS `tranche_age` from ((`personnel` `p` left join `personnel_infos` `pi` on(`p`.`id` = `pi`.`personnel_id`)) left join `tranche_age` `ta` on(timestampdiff(YEAR,`pi`.`date_naissance`,curdate()) >= `ta`.`age_min` and (`ta`.`age_max` is null or timestampdiff(YEAR,`pi`.`date_naissance`,curdate()) <= `ta`.`age_max`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_personnel_anciennete`
--

/*!50001 DROP VIEW IF EXISTS `v_personnel_anciennete`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_personnel_anciennete` AS select `p`.`id` AS `id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`matricule` AS `matricule`,`p`.`statut` AS `statut`,`pi`.`date_entree` AS `date_entree`,timestampdiff(YEAR,`pi`.`date_entree`,curdate()) AS `anciennete_annees`,timestampdiff(MONTH,`pi`.`date_entree`,curdate()) MOD 12 AS `anciennete_mois`,to_days(curdate()) - to_days(`pi`.`date_entree`) AS `anciennete_jours`,concat(timestampdiff(YEAR,`pi`.`date_entree`,curdate()),' ans ',timestampdiff(MONTH,`pi`.`date_entree`,curdate()) MOD 12,' mois') AS `anciennete_texte` from (`personnel` `p` left join `personnel_infos` `pi` on(`p`.`id` = `pi`.`personnel_id`)) where `pi`.`date_entree` is not null */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_soldes_disponibles`
--

/*!50001 DROP VIEW IF EXISTS `v_soldes_disponibles`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_soldes_disponibles` AS select `sc`.`id` AS `id`,`sc`.`personnel_id` AS `personnel_id`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `nom_complet`,`p`.`matricule` AS `matricule`,`sc`.`annee` AS `annee`,`sc`.`cp_acquis` AS `cp_acquis`,`sc`.`cp_n_1` AS `cp_n_1`,`sc`.`cp_pris` AS `cp_pris`,`sc`.`cp_acquis` + `sc`.`cp_n_1` - `sc`.`cp_pris` AS `cp_restant`,`sc`.`rtt_acquis` AS `rtt_acquis`,`sc`.`rtt_pris` AS `rtt_pris`,`sc`.`rtt_acquis` - `sc`.`rtt_pris` AS `rtt_restant`,`sc`.`date_maj` AS `date_maj` from (`solde_conges` `sc` join `personnel` `p` on(`sc`.`personnel_id` = `p`.`id`)) where `p`.`statut` = 'ACTIF' */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_stats_absences`
--

/*!50001 DROP VIEW IF EXISTS `v_stats_absences`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_stats_absences` AS select `p`.`id` AS `personnel_id`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `nom_complet`,year(`da`.`date_debut`) AS `annee`,`ta`.`libelle` AS `type_absence`,count(0) AS `nb_demandes`,sum(`da`.`nb_jours`) AS `total_jours`,sum(case when `da`.`statut` = 'VALIDEE' then `da`.`nb_jours` else 0 end) AS `jours_valides`,sum(case when `da`.`statut` = 'EN_ATTENTE' then `da`.`nb_jours` else 0 end) AS `jours_en_attente` from ((`demande_absence` `da` join `personnel` `p` on(`da`.`personnel_id` = `p`.`id`)) join `type_absence` `ta` on(`da`.`type_absence_id` = `ta`.`id`)) where `p`.`statut` = 'ACTIF' group by `p`.`id`,year(`da`.`date_debut`),`ta`.`libelle` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_suivi_medical`
--

/*!50001 DROP VIEW IF EXISTS `v_suivi_medical`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_suivi_medical` AS select `p`.`id` AS `operateur_id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`matricule` AS `matricule`,`p`.`statut` AS `statut`,`m`.`type_suivi_vip` AS `type_suivi_vip`,`m`.`periodicite_vip_mois` AS `periodicite_vip_mois`,(select max(`mv`.`date_visite`) from `medical_visite` `mv` where `mv`.`operateur_id` = `p`.`id`) AS `derniere_visite`,(select `mv`.`prochaine_visite` from `medical_visite` `mv` where `mv`.`operateur_id` = `p`.`id` order by `mv`.`date_visite` desc limit 1) AS `prochaine_visite`,case when (select `mv`.`prochaine_visite` from `medical_visite` `mv` where `mv`.`operateur_id` = `p`.`id` order by `mv`.`date_visite` desc limit 1) < curdate() then 'En retard' when (select `mv`.`prochaine_visite` from `medical_visite` `mv` where `mv`.`operateur_id` = `p`.`id` order by `mv`.`date_visite` desc limit 1) <= curdate() + interval 30 day then 'À planifier' else 'OK' end AS `statut_visite`,(select `v`.`date_debut` from `validite` `v` where `v`.`operateur_id` = `p`.`id` and `v`.`type_validite` = 'RQTH' order by `v`.`date_debut` desc limit 1) AS `date_debut_rqth`,(select `v`.`date_fin` from `validite` `v` where `v`.`operateur_id` = `p`.`id` and `v`.`type_validite` = 'RQTH' order by `v`.`date_debut` desc limit 1) AS `date_fin_rqth`,case when (select `v`.`date_fin` from `validite` `v` where `v`.`operateur_id` = `p`.`id` and `v`.`type_validite` = 'RQTH' order by `v`.`date_debut` desc limit 1) is not null and (select `v`.`date_fin` from `validite` `v` where `v`.`operateur_id` = `p`.`id` and `v`.`type_validite` = 'RQTH' order by `v`.`date_debut` desc limit 1) >= curdate() then 'Active' when (select `v`.`date_fin` from `validite` `v` where `v`.`operateur_id` = `p`.`id` and `v`.`type_validite` = 'RQTH' order by `v`.`date_debut` desc limit 1) is not null and (select `v`.`date_fin` from `validite` `v` where `v`.`operateur_id` = `p`.`id` and `v`.`type_validite` = 'RQTH' order by `v`.`date_debut` desc limit 1) < curdate() then 'Expirée' else 'Non applicable' end AS `statut_rqth`,(select `v`.`date_debut` from `validite` `v` where `v`.`operateur_id` = `p`.`id` and `v`.`type_validite` = 'OETH' order by `v`.`date_debut` desc limit 1) AS `date_debut_oeth`,(select `v`.`date_fin` from `validite` `v` where `v`.`operateur_id` = `p`.`id` and `v`.`type_validite` = 'OETH' order by `v`.`date_debut` desc limit 1) AS `date_fin_oeth`,(select `v`.`taux_incapacite` from `validite` `v` where `v`.`operateur_id` = `p`.`id` order by `v`.`date_debut` desc limit 1) AS `taux_incapacite`,`m`.`maladie_pro` AS `maladie_pro`,(select count(0) from `medical_accident_travail` `at` where `at`.`operateur_id` = `p`.`id`) AS `nb_accidents` from (`personnel` `p` left join `medical` `m` on(`p`.`id` = `m`.`operateur_id`)) where `p`.`statut` = 'ACTIF' */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_vie_salarie_recap`
--

/*!50001 DROP VIEW IF EXISTS `v_vie_salarie_recap`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb3 */;
/*!50001 SET character_set_results     = utf8mb3 */;
/*!50001 SET collation_connection      = utf8mb3_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`gestionrh`@`localhost` SQL SECURITY INVOKER */
/*!50001 VIEW `v_vie_salarie_recap` AS select `p`.`id` AS `operateur_id`,`p`.`nom` AS `nom`,`p`.`prenom` AS `prenom`,`p`.`statut` AS `statut`,(select count(0) from `vie_salarie_sanction` `s` where `s`.`operateur_id` = `p`.`id`) AS `nb_sanctions`,(select max(`s`.`date_sanction`) from `vie_salarie_sanction` `s` where `s`.`operateur_id` = `p`.`id`) AS `derniere_sanction`,(select count(0) from `vie_salarie_alcoolemie` `a` where `a`.`operateur_id` = `p`.`id`) AS `nb_controles_alcool`,(select count(0) from `vie_salarie_alcoolemie` `a` where `a`.`operateur_id` = `p`.`id` and `a`.`resultat` = 'Positif') AS `nb_positifs_alcool`,(select count(0) from `vie_salarie_test_salivaire` `t` where `t`.`operateur_id` = `p`.`id`) AS `nb_tests_salivaires`,(select count(0) from `vie_salarie_test_salivaire` `t` where `t`.`operateur_id` = `p`.`id` and `t`.`resultat` = 'Positif') AS `nb_positifs_salivaire`,(select max(`e`.`date_entretien`) from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` and `e`.`type_entretien` = 'EPP') AS `dernier_epp`,(select max(`e`.`date_entretien`) from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` and `e`.`type_entretien` = 'EAP') AS `dernier_eap`,(select `e`.`prochaine_date` from `vie_salarie_entretien` `e` where `e`.`operateur_id` = `p`.`id` order by `e`.`date_entretien` desc limit 1) AS `prochain_entretien` from `personnel` `p` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-02-12  9:38:52
