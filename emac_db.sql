-- MySQL dump 10.13  Distrib 8.0.43, for Win64 (x86_64)
--
-- Host: localhost    Database: emac_db
-- ------------------------------------------------------
-- Server version	8.0.43

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
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
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `atelier` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `atelier`
--

LOCK TABLES `atelier` WRITE;
/*!40000 ALTER TABLE `atelier` DISABLE KEYS */;
INSERT INTO `atelier` VALUES (5,'Atelier 5'),(8,'Atelier 8'),(9,'Atelier 9'),(10,'Atelier 10'),(11,'Atelier 11'),(14,'Atelier 14');
/*!40000 ALTER TABLE `atelier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `categories_documents`
--

DROP TABLE IF EXISTS `categories_documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `categories_documents` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `description` text COLLATE utf8mb4_general_ci,
  `couleur` varchar(7) COLLATE utf8mb4_general_ci DEFAULT '#3b82f6',
  `exige_date_expiration` tinyint(1) DEFAULT '0',
  `ordre_affichage` int DEFAULT '0',
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_categorie_nom` (`nom`)
) ENGINE=InnoDB AUTO_INCREMENT=9 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `categories_documents`
--

LOCK TABLES `categories_documents` WRITE;
/*!40000 ALTER TABLE `categories_documents` DISABLE KEYS */;
INSERT INTO `categories_documents` VALUES (1,'Contrats de travail','Contrats CDI, CDD, avenants','#10b981',1,1,'2025-11-28 10:45:14','2025-11-28 10:45:14'),(2,'Certificats m├®dicaux','Visites m├®dicales, aptitudes, RQTH','#ef4444',1,2,'2025-11-28 10:45:14','2025-11-28 10:45:14'),(3,'Dipl├┤mes et formations','Dipl├┤mes, certificats de formation, habilitations','#8b5cf6',0,3,'2025-11-28 10:45:14','2025-11-28 10:45:14'),(4,'Autorisations de travail','Titres de s├®jour, autorisations de travail pour ├®trangers','#f59e0b',1,4,'2025-11-28 10:45:14','2025-11-28 10:45:14'),(5,'Pi├¿ces d\'identit├®','CNI, passeport, permis de conduire','#06b6d4',1,5,'2025-11-28 10:45:14','2025-11-28 10:45:14'),(6,'Attestations diverses','Attestations employeur, certificats de travail','#6366f1',0,6,'2025-11-28 10:45:14','2025-11-28 10:45:14'),(7,'Documents administratifs','Fiches de paie, relev├®s, justificatifs','#64748b',0,7,'2025-11-28 10:45:14','2025-11-28 10:45:14'),(8,'Autres','Documents non class├®s','#9ca3af',0,99,'2025-11-28 10:45:14','2025-11-28 10:45:14');
/*!40000 ALTER TABLE `categories_documents` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `classeur1`
--

DROP TABLE IF EXISTS `classeur1`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `classeur1` (
  `NOMFAMILLE` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `PRENOM` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `SEXE` varchar(10) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `NAISDT` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ENTREEGROUPEDT` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `EMAIL` varchar(320) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `GSM` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ADRCPL1_0001` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `CPOSTAL_0001` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `VIL_0001` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `PAY_0001` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `COMNAIS` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `CODEPAYSNAIS` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `DEPARNAIS` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `CODEPAYSNATION` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `classeur1`
--

LOCK TABLES `classeur1` WRITE;
/*!40000 ALTER TABLE `classeur1` DISABLE KEYS */;
/*!40000 ALTER TABLE `classeur1` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contrat`
--

DROP TABLE IF EXISTS `contrat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contrat` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `type_contrat` enum('Stagiaire','Apprentissage','Intérimaire','Mise à disposition GE','Etranger hors UE','Temps partiel','CDI','CDD','CIFRE') COLLATE utf8mb4_general_ci NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `etp` decimal(3,2) DEFAULT '1.00' COMMENT 'Équivalent Temps Plein',
  `categorie` enum('Ouvrier','Ouvrier qualifié','Employé','Agent de maîtrise','Cadre') COLLATE utf8mb4_general_ci DEFAULT NULL,
  `echelon` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `emploi` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `salaire` decimal(10,2) DEFAULT NULL,
  `actif` tinyint(1) DEFAULT '1',
  `nom_tuteur` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `prenom_tuteur` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ecole` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `nom_ett` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `adresse_ett` text COLLATE utf8mb4_general_ci,
  `nom_ge` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `adresse_ge` text COLLATE utf8mb4_general_ci,
  `date_autorisation_travail` date DEFAULT NULL,
  `date_demande_autorisation` date DEFAULT NULL,
  `type_titre_autorisation` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `numero_autorisation_travail` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `date_limite_autorisation` date DEFAULT NULL,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_type_contrat` (`type_contrat`),
  KEY `idx_actif` (`actif`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_contrat_dates_actif` (`date_debut`,`date_fin`,`actif`),
  CONSTRAINT `fk_contrat_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `contrat`
--

LOCK TABLES `contrat` WRITE;
/*!40000 ALTER TABLE `contrat` DISABLE KEYS */;
/*!40000 ALTER TABLE `contrat` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `declaration`
--

DROP TABLE IF EXISTS `declaration`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `declaration` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `type_declaration` enum('CongePaye','RTT','SansSolde','Maladie','AccidentTravail','AccidentTrajet','ArretTravail','CongeNaissance','Formation','Autorisation','Autre') NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `motif` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  CONSTRAINT `fk_absences_conges_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE= utf8mb4_general_ci;
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
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `demande_absence` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `type_absence_id` int NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `demi_journee_debut` enum('MATIN','APRES_MIDI','JOURNEE') COLLATE utf8mb4_unicode_ci DEFAULT 'JOURNEE',
  `demi_journee_fin` enum('MATIN','APRES_MIDI','JOURNEE') COLLATE utf8mb4_unicode_ci DEFAULT 'JOURNEE',
  `nb_jours` decimal(4,2) NOT NULL COMMENT 'Nombre de jours ouvrés',
  `motif` text COLLATE utf8mb4_unicode_ci,
  `statut` enum('EN_ATTENTE','VALIDEE','REFUSEE','ANNULEE') COLLATE utf8mb4_unicode_ci DEFAULT 'EN_ATTENTE',
  `validateur_id` int DEFAULT NULL COMMENT 'ID du personnel qui a validé/refusé',
  `date_validation` datetime DEFAULT NULL,
  `commentaire_validation` text COLLATE utf8mb4_unicode_ci,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `type_absence_id` (`type_absence_id`),
  KEY `validateur_id` (`validateur_id`),
  KEY `idx_personnel` (`personnel_id`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_statut` (`statut`),
  CONSTRAINT `demande_absence_ibfk_1` FOREIGN KEY (`personnel_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `demande_absence_ibfk_2` FOREIGN KEY (`type_absence_id`) REFERENCES `type_absence` (`id`),
  CONSTRAINT `demande_absence_ibfk_3` FOREIGN KEY (`validateur_id`) REFERENCES `personnel` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `demande_absence`
--

LOCK TABLES `demande_absence` WRITE;
/*!40000 ALTER TABLE `demande_absence` DISABLE KEYS */;
/*!40000 ALTER TABLE `demande_absence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `documents`
--

DROP TABLE IF EXISTS `documents`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `documents` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `categorie_id` int NOT NULL,
  `nom_fichier` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `nom_affichage` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `chemin_fichier` varchar(500) COLLATE utf8mb4_general_ci NOT NULL,
  `type_mime` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `taille_octets` bigint DEFAULT '0',
  `date_upload` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_expiration` date DEFAULT NULL,
  `statut` enum('actif','expire','archive') COLLATE utf8mb4_general_ci DEFAULT 'actif',
  `notes` text COLLATE utf8mb4_general_ci,
  `uploaded_by` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_categorie` (`categorie_id`),
  KEY `idx_statut` (`statut`),
  KEY `idx_expiration` (`date_expiration`),
  CONSTRAINT `fk_documents_categorie` FOREIGN KEY (`categorie_id`) REFERENCES `categories_documents` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_documents_personnel` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `documents`
--

LOCK TABLES `documents` WRITE;
/*!40000 ALTER TABLE `documents` DISABLE KEYS */;
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
-- Table structure for table `formation`
--

DROP TABLE IF EXISTS `formation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `intitule` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `organisme` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `duree_heures` decimal(6,2) DEFAULT NULL,
  `statut` enum('Planifiée','En cours','Terminée','Annulée') COLLATE utf8mb4_general_ci DEFAULT 'Planifiée',
  `certificat_obtenu` tinyint(1) DEFAULT '0',
  `cout` decimal(10,2) DEFAULT NULL,
  `commentaire` text COLLATE utf8mb4_general_ci,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_statut` (`statut`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_formation_operateur_dates` (`operateur_id`,`date_debut`,`date_fin`),
  CONSTRAINT `fk_formation_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `formation`
--

LOCK TABLES `formation` WRITE;
/*!40000 ALTER TABLE `formation` DISABLE KEYS */;
/*!40000 ALTER TABLE `formation` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `historique`
--

DROP TABLE IF EXISTS `historique`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `historique` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date_time` datetime NOT NULL,
  `action` varchar(255) COLLATE utf8mb4_general_ci NOT NULL,
  `operateur_id` int DEFAULT NULL,
  `poste_id` int DEFAULT NULL,
  `description` text COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`id`),
  KEY `operateur_id` (`operateur_id`),
  KEY `poste_id` (`poste_id`),
  CONSTRAINT `historique_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `historique_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historique`
--

LOCK TABLES `historique` WRITE;
/*!40000 ALTER TABLE `historique` DISABLE KEYS */;
INSERT INTO `historique` VALUES (12,'2025-11-27 14:37:15','INSERT',1,1,'{\"operateur\": \"TEST MANUEL\", \"poste\": \"TEST\", \"niveau\": 3, \"type\": \"test\"}'),(13,'2025-11-27 15:50:03','INSERT',2,5,'{\"operateur\": \"Aguerre Stephane\", \"poste\": \"0515\", \"niveau\": 3, \"type\": \"ajout\"}'),(14,'2025-11-27 15:55:23','INSERT',2,5,'{\"operateur\": \"Aguerre Stephane\", \"poste\": \"0515\", \"niveau\": 4, \"type\": \"ajout\"}'),(15,'2025-11-28 08:48:47','INSERT',2,5,'{\"operateur\": \"Aguerre Stephane\", \"poste\": \"0515\", \"niveau\": 3, \"type\": \"ajout\"}'),(18,'2025-12-01 14:26:47','UPDATE',3,5,'{\"operateur\": \"Bagdasariani Eduardi\", \"poste\": \"0515\", \"changes\": {\"niveau\": {\"old\": 3, \"new\": 4}}, \"type\": \"modification\"}'),(19,'2025-12-01 14:27:21','INSERT',3,5,'{\"operateur\": \"Bagdasariani Eduardi\", \"poste\": \"0515\", \"niveau\": 3, \"type\": \"ajout\"}');
/*!40000 ALTER TABLE `historique` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `import_personnel`
--

DROP TABLE IF EXISTS `import_personnel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `import_personnel` (
  `id` int NOT NULL AUTO_INCREMENT,
  `PINDIVIDU_ID` int DEFAULT NULL,
  `NOMFAMILLE` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `PRENOM` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `NUMPOSTE` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_nom` (`NOMFAMILLE`),
  KEY `idx_prenom` (`PRENOM`)
) ENGINE=InnoDB AUTO_INCREMENT=171 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `import_personnel`
--

LOCK TABLES `import_personnel` WRITE;
/*!40000 ALTER TABLE `import_personnel` DISABLE KEYS */;
INSERT INTO `import_personnel` VALUES (1,16,'AMAT                                                                            ','ROMAIN FLORIAN                                                                  ','                    '),(2,17,'PERARO                                                                          ','MICKAEL ERIC MICHEL                                                             ','PRODUCTION          '),(3,18,'AGUERRE                                                                         ','STEPHANE JEAN MICHEL                                                            ','                    '),(4,19,'ARNAL                                                                           ','JEAN MARIE                                                                      ','                    '),(5,20,'BAILLY                                                                          ','XAVIER MARC JEAN                                                                ','PRODUCTION          '),(6,21,'BEHEREGARAY                                                                     ','JEAN MICHEL                                                                     ','200                 '),(7,22,'BENGOCHEA                                                                       ','EMMANUEL                                                                        ','PRODUCTION          '),(8,23,'BERCAITS                                                                        ','FRANCOIS MARIE                                                                  ','PRODUCTION          '),(9,24,'BERHO                                                                           ','INAKI                                                                           ','PRODUCTION          '),(10,25,'BERROGAIN                                                                       ','JEAN BAPTISTE                                                                   ','242                 '),(11,26,'BERTHE                                                                          ','OPHELIE JEANNE SUZANNE                                                          ','PRODUCTION          '),(12,27,'BIDONDO                                                                         ','MICKAEL ALEXANDRE                                                               ','PRODUCTION          '),(13,28,'BIDONDO                                                                         ','PIERRE                                                                          ','247                 '),(14,29,'BOULDOIRES                                                                      ','MATHIEU                                                                         ','R&D                 '),(15,30,'BRANKAER                                                                        ','ALEXANDRE                                                                       ','PRODUCTION          '),(16,31,'CAMY                                                                            ','ALAIN                                                                           ','PRODUCTION          '),(17,32,'CASTEX                                                                          ','LAURENT CHRISTIAN                                                               ','PRODUCTION          '),(18,33,'CORDANI                                                                         ','JEANMARIE JOSEPH                                                                ','PRODUCTION          '),(19,34,'CORREIA DOS SANTOS                                                              ','JORGE MANUEL                                                                    ','PRODUCTION          '),(20,35,'COSTA                                                                           ','DANIEL                                                                          ','342                 '),(21,36,'COURTIES                                                                        ','DORYAN MARC MARCEL                                                              ','PRODUCTION          '),(22,37,'DAGUERRE                                                                        ','PATRICK JEAN CLAUDE                                                             ','233                 '),(23,38,'DAUBAS                                                                          ','GEORGES MICHEL                                                                  ','PRODUCTION          '),(24,39,'DELGADO                                                                         ','CEDRIC GERARD CHRISTIAN                                                         ','PRODUCTION          '),(25,40,'DUHALDE                                                                         ','PIERRE SAUVEUR                                                                  ','PRODUCTION          '),(26,41,'ERRECART                                                                        ','SERGE                                                                           ','PRODUCTION          '),(27,42,'ETCHEVERRY                                                                      ','FREDERIC JEANBERNARD DOMINIQUE                                                  ','PRODUCTION          '),(28,43,'FERNANDES                                                                       ','MARIE FRANCOISE                                                                 ','LABORATOIRE         '),(29,44,'GODFRIN                                                                         ','DAVID                                                                           ','226                 '),(30,45,'GOUVERT                                                                         ','CAROLINE CATHERINE JOSEPHINE                                                    ','222                 '),(31,46,'GUIMON                                                                          ','ALAIN                                                                           ','LEADER              '),(32,47,'HEUGAS                                                                          ','JEREMY                                                                          ','243/241             '),(33,48,'IGLESIAS                                                                        ','LUDOVIC MALIK                                                                   ','PRODUCTION          '),(34,49,'ITURRIA                                                                         ','LOIC                                                                            ','MAINTENANCE         '),(35,50,'JIMENEZ                                                                         ','ANDRE                                                                           ','264                 '),(36,51,'JOUMAH                                                                          ','HASSAN                                                                          ','240                 '),(37,52,'KERN                                                                            ','BERNARD                                                                         ','PRODUCTION          '),(38,53,'LAC PEYRAS                                                                      ','PASCALE                                                                         ','241                 '),(39,54,'LAGOURGUE                                                                       ','DIDIER GUILLERMO                                                                ','PRODUCTION          '),(40,55,'LARRABURU                                                                       ','PASCALE                                                                         ','LABORATOIRE         '),(41,56,'LORDON                                                                          ','JEANBAPTISTE                                                                    ','PRODUCTION          '),(42,57,'MAFFRAND                                                                        ','ALEXIS                                                                          ','PRODUCTION          '),(43,58,'MARQUES                                                                         ','PAULINE MARIE ELODIE                                                            ','PRODUCTION          '),(44,59,'MENDRIBIL                                                                       ','ALAIN                                                                           ','PRODUCTION          '),(45,60,'MOLUS                                                                           ','SONIA                                                                           ','PRODUCTION          '),(46,62,'MOUSTROUS                                                                       ','HERVE                                                                           ','PRODUCTION          '),(47,63,'OLIVIER                                                                         ','ALBAN ROGER                                                                     ','207                 '),(48,64,'PEREZ                                                                           ','XAVIER                                                                          ','PRODUCTION          '),(49,65,'POCHELU                                                                         ','ANDRE MAURICE                                                                   ','PRODUCTION          '),(50,66,'RECALT                                                                          ','HERVE                                                                           ','220                 '),(51,67,'RECALT                                                                          ','JEAN PAUL                                                                       ','222                 '),(52,68,'REINA                                                                           ','FREDERIC                                                                        ','257                 '),(53,69,'SALLABERRY                                                                      ','JEAN MICHEL                                                                     ','211                 '),(54,70,'SARALEGUI                                                                       ','ERIC                                                                            ','PRODUCTION          '),(55,71,'SARDA                                                                           ','MANON MARIE                                                                     ','ADMIN               '),(56,72,'SEBILO                                                                          ','ALLAN GEORGES GERARD                                                            ','PRODUCTION          '),(57,73,'SICRE                                                                           ','PIERRE                                                                          ','342                 '),(58,74,'SIMON                                                                           ','THOMAS THIERRY DIDIER                                                           ','PRODUCTION          '),(59,75,'SOUBIRAN                                                                        ','VERONIQUE SOPHIE                                                                ','LABORATOIRE         '),(60,76,'SUBLIME                                                                         ','CYRIL GEORGES ANDRE                                                             ','208                 '),(61,77,'TARDY                                                                           ','JEAN MARIE                                                                      ','PRODUCTION          '),(62,78,'TRADERE                                                                         ','JONATHAN JEAN                                                                   ','PRODUCTION          '),(63,79,'VASSEUR                                                                         ','JOFFREY                                                                         ','PRODUCTION          '),(64,80,'VERGE                                                                           ','OLIVIER                                                                         ','PRODUCTION          '),(65,81,'VERGE                                                                           ','REMY                                                                            ','PRODUCTION          '),(66,82,'ALTHABE                                                                         ','MICHEL                                                                          ','205                 '),(67,83,'ARHANCETEBEHERE                                                                 ','DIDIER                                                                          ','218                 '),(68,84,'ARROUGE                                                                         ','THOMAS                                                                          ','MAITENANCE          '),(69,85,'BERGEZ                                                                          ','FRANCK                                                                          ','228                 '),(70,86,'CHARMAN                                                                         ','MAXIME DANIEL                                                                   ','214                 '),(71,87,'COUCHINIAV                                                                      ','SONIA                                                                           ','202                 '),(72,88,'COUCHINIAV                                                                      ','ERIC                                                                            ','PRODUCTION          '),(73,89,'GAUCHET                                                                         ','STEVE JEAN RENE                                                                 ','206                 '),(74,90,'GAUDIN                                                                          ','ALEXANDRA                                                                       ','243                 '),(75,91,'GERONY                                                                          ','CAROLE                                                                          ','229                 '),(76,92,'GESSE                                                                           ','MARIE CLAIRE                                                                    ','230                 '),(77,93,'GUIRESSE                                                                        ','BRIGITTE                                                                        ','203                 '),(78,94,'ORDUNA                                                                          ','PIERRE                                                                          ','PRODUCTION          '),(79,95,'EPELVA                                                                          ','Fran├ºois                                                                        ','PRODUCTION          '),(80,96,'PICOT                                                                           ','FREDERIC                                                                        ','PRODUCTION          '),(81,97,'DOS SANTOS                                                                      ','Elisa                                                                           ','ADMIN               '),(82,99,'MOUREU                                                                          ','MARIE LAURE                                                                     ','201                 '),(83,101,'CAZENAVE                                                                        ','JEAN                                                                            ','PRODUCTION          '),(84,102,'LEPOLARD                                                                        ','Aur├®lien, Michel                                                                ','                    '),(85,103,'POLI                                                                            ','Xabi, Saint, Martin                                                             ','PRODUCTION          '),(86,104,'DENECKER                                                                        ','Charlotte                                                                       ','ADMIN               '),(87,105,'HEGUIABEHERE                                                                    ','Alexandre                                                                       ','PRODUCTION          '),(88,106,'REMON                                                                           ','Florian                                                                         ','PRODUCTION          '),(89,107,'FERNANDEZ                                                                       ','Thomas                                                                          ','PRODUCTION          '),(90,108,'BARAT                                                                           ','Romain                                                                          ','ADMIN               '),(91,109,'DUTTER                                                                          ','Muriel                                                                          ','LABO                '),(92,110,'OYHENART                                                                        ','Nicolas                                                                         ','PRODUCTION          '),(93,111,'BERRETEROT                                                                      ','Julien                                                                          ','PRODUCTION          '),(94,112,'GONOT                                                                           ','Damien                                                                          ','PRODUCTION          '),(95,113,'CAPURET                                                                         ','Anthony                                                                         ','PRODUCTION          '),(96,114,'RABINEAU                                                                        ','Nicolas                                                                         ','ADMIN               '),(97,115,'DESLANDES                                                                       ','Laurent                                                                         ','PRODUCTION          '),(98,116,'ERBIN                                                                           ','Julien                                                                          ','PRODUCTION          '),(99,117,'LEPOLARD                                                                        ','Baptiste                                                                        ','PRODUCTION          '),(100,118,'AREN                                                                            ','Pierre                                                                          ','PRODUCTION          '),(101,119,'LAUGA                                                                           ','Fr├®d├®ric                                                                        ','PRODUCTION          '),(102,120,'CAMPANE                                                                         ','Lionel                                                                          ','PRODUCTION          '),(103,121,'DUMOLLARD                                                                       ','Thierry                                                                         ','PRODUCTION          '),(104,122,'JELASSI                                                                         ','Jo├½l-Jean                                                                       ','MAINTENANCE         '),(105,123,'MILAGE                                                                          ','Alban                                                                           ','PRODUCTION          '),(106,124,'DUMUR-LOURTEAU                                                                  ','Vincent                                                                         ','PRODUCTION          '),(107,125,'RAMONTEU-CHIROS                                                                 ','Ludovic                                                                         ','PRODUCTION          '),(108,126,'HAVY                                                                            ','Floriant                                                                        ','PRODUCTION          '),(109,127,'DEVERITE                                                                        ','Jonathan                                                                        ','PRODUCTION          '),(110,129,'LARROQUE                                                                        ','GUILLAUME                                                                       ','MAINTENANCE         '),(111,130,'DOS SANTOS                                                                      ','CHARLY                                                                          ','PRODUCTION 1404     '),(112,131,'RICE                                                                            ','MATTHEW                                                                         ','PRODUCTION          '),(113,132,'PEYROU                                                                          ','Maxime                                                                          ','PRODUCTION          '),(114,133,'LASCOUMES                                                                       ','MARIE                                                                           ','ADMIN               '),(115,134,'SALMON                                                                          ','Quentin                                                                         ','PRODUCTION          '),(116,135,'EL HAMOUCHI                                                                     ','Mohamed                                                                         ','LABORATOIRE         '),(117,136,'CHAMMAM                                                                         ','Marwa                                                                           ','ADMINISTRATIF       '),(118,137,'REBIERE                                                                         ','Th├®o, Romain                                                                    ','R&D                 '),(119,138,'DENNEMONT                                                                       ','Valentin                                                                        ','PRODUCTION          '),(120,139,'COURTIES                                                                        ','Paul, Marc                                                                      ','PRODUCTION          '),(121,140,'GOUVINHAS                                                                       ','Alexandre                                                                       ','PRODUCTION          '),(122,141,'LUQUET                                                                          ','Fran├ºois                                                                        ','PRODUCTION          '),(123,142,'POISSONNET                                                                      ','Jean-Louis                                                                      ','PRODUCTION          '),(124,143,'BIDONDO                                                                         ','Anthony                                                                         ','PRODUCTION          '),(125,144,'UNANUA                                                                          ','Dominique                                                                       ','PRODUCTION          '),(126,145,'DEVAUX                                                                          ','David                                                                           ','PRODUCTION          '),(127,146,'GONZALEZ MERG                                                                   ','Paulo Cristiano                                                                 ','PRODUCTION          '),(128,147,'LOUREIRO                                                                        ','Michel                                                                          ','PRODUCTION          '),(129,148,'SERVANT                                                                         ','Mika├½l                                                                          ','PRODUCTION          '),(130,149,'FERNANDEZ                                                                       ','Yohan                                                                           ','PRODUCTION          '),(131,150,'PELEGRINELLI                                                                    ','Damien                                                                          ','PRODUCTION          '),(132,151,'DAVIES                                                                          ','Edouard                                                                         ','PRODUCTION          '),(133,152,'SALLETTE                                                                        ','Fr├®d├®ric                                                                        ','PRODUCTION          '),(134,153,'COURTIES                                                                        ','Cl├®rik                                                                          ','PRODUCTION          '),(135,154,'DUCHAMP                                                                         ','Lionel                                                                          ','PRODUCTION          '),(136,155,'SAIZ FERNANDEZ                                                                  ','K├®vin                                                                           ','PRODUCTION          '),(137,156,'ETCHEVERRY                                                                      ','Fabien                                                                          ','PRODUCTION          '),(138,157,'TARDY                                                                           ','Maxime                                                                          ','PRODUCTION          '),(139,158,'CAMPANE                                                                         ','Jean-Fran├ºois                                                                   ','PRODUCTION          '),(140,159,'BERGERON                                                                        ','Marie-No├½le                                                                     ','LABORATOIRE         '),(141,160,'MUNOZ TERES                                                                     ','Vanessa                                                                         ','QUALITE             '),(142,161,'DA COSTA-RAMOS                                                                  ','Sergio                                                                          ','PRODUCTION          '),(143,162,'CARRICABURU                                                                     ','Alain                                                                           ','                    '),(144,163,'CHARDIN                                                                         ','K├®vin                                                                           ','                    '),(145,164,'MARTA                                                                           ','Fr├®d├®ric                                                                        ','                    '),(146,165,'ACEDO                                                                           ','S├®bastien                                                                       ','                    '),(147,166,'LOUSTALOT                                                                       ','Marl├¿ne                                                                         ','Cariste-HSE         '),(148,167,'BRANA                                                                           ','Jean-Paul                                                                       ','PRODUCTION          '),(149,168,'ETCHEBERRIBORDE                                                                 ','Julie                                                                           ','ADMIN               '),(150,169,'DA COSTA SILVA                                                                  ','Sonia                                                                           ','                    '),(151,170,'MOSQUEDA                                                                        ','Martin                                                                          ','                    '),(152,171,'GELARD                                                                          ','Alain                                                                           ','                    '),(153,172,'IDIART                                                                          ','C├®line                                                                          ','ADMINISTRATIF       '),(154,173,'MORIAT                                                                          ','Andr├®                                                                           ','PRODUCTION          '),(155,174,'ETCHEVERRY                                                                      ','Adrien                                                                          ','                    '),(156,175,'MICHAUT                                                                         ','Bettan                                                                          ','MAINTENANCE         '),(157,176,'POUTOU                                                                          ','Eldon                                                                           ','PRODUCTION          '),(158,177,'MERCIRIS                                                                        ','Th├®o                                                                            ','PRODUCTION          '),(159,178,'MARCADIEU                                                                       ','C├®dric                                                                          ','PRODUCTION          '),(160,179,'THIERY                                                                          ','Adrien                                                                          ','Agent HSE - Cariste '),(161,180,'REVIDIEGO                                                                       ','Isabelle                                                                        ','Agent HSE           '),(162,181,'SAUVE                                                                           ','Ama├»a                                                                           ','PRODUCTION          '),(163,182,'MONTOIS                                                                         ','Xabi                                                                            ','PRODUCTION          '),(164,183,'URRUTIA                                                                         ','Laurent                                                                         ','PRODUCTION          '),(165,184,'LAJOURNADE                                                                      ','Antoine                                                                         ','METHODE             '),(166,185,'BAGDASARIANI                                                                    ','Eduardi                                                                         ','PRODUCTION          '),(167,186,'BANQUET                                                                         ','Marine                                                                          ','QUALITE             '),(168,187,'FRETAY                                                                          ','Sabrina                                                                         ','HSE                 '),(169,188,'COLAS                                                                           ','Martin                                                                          ','ADMIN               '),(170,189,'ETCHEVERRIA                                                                     ','Joaquim                                                                         ','PRODUCTION          ');
/*!40000 ALTER TABLE `import_personnel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `jours_feries`
--

DROP TABLE IF EXISTS `jours_feries`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `jours_feries` (
  `id` int NOT NULL AUTO_INCREMENT,
  `date_ferie` date NOT NULL,
  `libelle` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `fixe` tinyint(1) DEFAULT '1' COMMENT 'TRUE si date fixe chaque année',
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
INSERT INTO `jours_feries` VALUES (1,'2025-01-01','Jour de l\'An',1),(2,'2025-04-21','Lundi de Pâques',0),(3,'2025-05-01','Fête du Travail',1),(4,'2025-05-08','Victoire 1945',1),(5,'2025-05-29','Ascension',0),(6,'2025-06-09','Lundi de Pentecôte',0),(7,'2025-07-14','Fête Nationale',1),(8,'2025-08-15','Assomption',1),(9,'2025-11-01','Toussaint',1),(10,'2025-11-11','Armistice 1918',1),(11,'2025-12-25','Noël',1);
/*!40000 ALTER TABLE `jours_feries` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel`
--

DROP TABLE IF EXISTS `personnel`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `prenom` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `statut` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `service_id` int DEFAULT NULL,
  `numposte` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `matricule` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_matricule` (`matricule`),
  UNIQUE KEY `uc_personnel` (`nom`,`prenom`)
) ENGINE=InnoDB AUTO_INCREMENT=394 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel`
--

LOCK TABLES `personnel` WRITE;
/*!40000 ALTER TABLE `personnel` DISABLE KEYS */;
INSERT INTO `personnel` VALUES (1,'Acedo','Sebastien','INACTIF',NULL,NULL,'M000001'),(2,'Aguerre','Stephane','ACTIF',NULL,NULL,'M000002'),(3,'Bagdasariani','Eduardi','ACTIF',1,'Production','M000003'),(4,'Beheregaray','Jean Michel','INACTIF',1,'200','M000004'),(5,'Bengochea','Emmanuel','ACTIF',1,'Production','M000005'),(6,'Bidondo','Anthony','ACTIF',1,'Production','M000006'),(7,'Bidondo','Mickael Alexandre','ACTIF',NULL,NULL,'M000007'),(8,'Bidondo','Pierre','ACTIF',1,'247','M000008'),(9,'Brankaer','Alexandre','ACTIF',1,'Production','M000009'),(10,'Campane','Jean Francois','ACTIF',NULL,NULL,'M000010'),(11,'Carricaburu','Alain','ACTIF',NULL,NULL,'M000011'),(12,'Cazenave','Jean','ACTIF',1,'Production','M000012'),(13,'Cordani','Jean-Marie Joseph','ACTIF',NULL,NULL,'M000013'),(14,'Correia Dos Santos','Jorge Manuel','ACTIF',NULL,NULL,'M000014'),(15,'Costa','Daniel','ACTIF',1,'342','M000015'),(16,'Couchinave','Eric','ACTIF',NULL,NULL,'M000016'),(17,'Courties','Doryan','ACTIF',9,'Production','M000017'),(18,'Da Costa','Sergio','ACTIF',NULL,NULL,'M000018'),(19,'Davies','Edouard','INACTIF',1,'Production','M000019'),(20,'Delgado','Cedric','ACTIF',9,'Production','M000020'),(21,'Devaux','David','INACTIF',1,'Production','M000021'),(22,'Dos Santos','Charly','ACTIF',1,'Production 1404','M000022'),(23,'Etcheverry','Frederic','ACTIF',9,'Production','M000023'),(24,'Fernandez','Thomas','ACTIF',1,'Production','M000024'),(25,'Gonot','Damien','ACTIF',1,'Production','M000025'),(26,'Gouvinhas','Alexandre','ACTIF',1,'Production','M000026'),(27,'Guimon','Alain','ACTIF',1,'Leader','M000027'),(28,'Luquet','Francois','ACTIF',NULL,NULL,'M000028'),(29,'Marcadieu','Cedric','ACTIF',NULL,NULL,'M000029'),(30,'Marta','Frederic','ACTIF',NULL,NULL,'M000030'),(31,'Merciris','Theo','INACTIF',NULL,NULL,'M000031'),(32,'Milage','Alban','ACTIF',1,'Production','M000032'),(33,'Molus','Sonia','ACTIF',1,'Production','M000033'),(34,'Montois','Xabi','ACTIF',1,'Production','M000034'),(35,'Moriat','Andre','INACTIF',NULL,NULL,'M000035'),(36,'Moustrous','Herve','ACTIF',1,'Production','M000036'),(37,'Orduna','Pierre','ACTIF',1,'Production','M000037'),(38,'Oyhenart','Nicolas','ACTIF',1,'Production','M000038'),(39,'Perez','Xavier','ACTIF',1,'Production','M000039'),(40,'Pochelu','Andre Maurice','ACTIF',1,'Production','M000040'),(41,'Poissonnet','Jean Louis','ACTIF',NULL,NULL,'M000041'),(42,'Poutou','Eldon Tresor','ACTIF',NULL,NULL,'M000042'),(43,'Rice','Matthew','ACTIF',1,'Production','M000043'),(44,'Sallette','Frederic','ACTIF',NULL,NULL,'M000044'),(45,'Saralegui','Eric','ACTIF',1,'Production','M000045'),(46,'Servant','Mikaël','ACTIF',NULL,NULL,'M000046'),(47,'Sicre','Pierre','ACTIF',1,'342','M000047'),(48,'Tradere','Jonathan','ACTIF',9,'Production','M000048'),(49,'Unanua','Dominique','ACTIF',1,'Production','M000049'),(50,'Urrutia','Laurent','ACTIF',1,'Production','M000050'),(51,'Vasseur','Joffrey','ACTIF',1,'Production','M000051'),(52,'Verge','Olivier','ACTIF',1,'Production','M000052'),(76,'Varin','Fabien','ACTIF',NULL,NULL,'M000076'),(99,'Etcheverria','Joaquim','ACTIF',1,'Production','M000099'),(100,'Laurent','Alain','ACTIF',NULL,NULL,'M000100'),(107,'Amat','Romain Florian','INACTIF',NULL,NULL,NULL),(108,'Peraro','Mickael Eric Michel','ACTIF',9,'Production',NULL),(111,'Arnal','Jean Marie','ACTIF',NULL,NULL,NULL),(112,'Bailly','Xavier Marc Jean','ACTIF',9,'Production',NULL),(114,'Bercaits','Francois Marie','ACTIF',9,'Production',NULL),(116,'Berho','Inaki','ACTIF',9,'Production',NULL),(118,'Berrogain','Jean Baptiste','ACTIF',9,'242',NULL),(120,'Berthe','Ophelie Jeanne Suzanne','ACTIF',9,'Production',NULL),(124,'Bouldoires','Mathieu','ACTIF',10,'R&D',NULL),(126,'Camy','Alain','ACTIF',9,'Production',NULL),(128,'Castex','Laurent Christian','ACTIF',9,'Production',NULL),(136,'Daguerre','Patrick Jean Claude','ACTIF',9,'233',NULL),(138,'Daubas','Georges Michel','ACTIF',9,'Production',NULL),(142,'Duhalde','Pierre Sauveur','ACTIF',9,'Production',NULL),(144,'Errecart','Serge','ACTIF',9,'Production',NULL),(148,'Fernandes','Marie Francoise','ACTIF',13,'Laboratoire',NULL),(150,'Godfrin','David','ACTIF',9,'226',NULL),(152,'Gouvert','Caroline Catherine Josephine','ACTIF',9,'222',NULL),(154,'Heugas','Jeremy','ACTIF',NULL,'243/241',NULL),(155,'Iglesias','Ludovic Malik','ACTIF',9,'Production',NULL),(157,'Iturria','Loic','ACTIF',11,'Maintenance',NULL),(159,'Jimenez','Andre','ACTIF',9,'264',NULL),(161,'Joumah','Hassan','ACTIF',9,'240',NULL),(163,'Kern','Bernard','ACTIF',9,'Production',NULL),(165,'Lac Peyras','Pascale','ACTIF',9,'241',NULL),(167,'Lagourgue','Didier Guillermo','ACTIF',9,'Production',NULL),(169,'Larraburu','Pascale','ACTIF',13,'Laboratoire',NULL),(171,'Lordon','Jeanbaptiste','ACTIF',9,'Production',NULL),(173,'Maffrand','Alexis','ACTIF',9,'Production',NULL),(175,'Marques','Pauline Marie Elodie','ACTIF',9,'Production',NULL),(177,'Mendribil','Alain','ACTIF',9,'Production',NULL),(179,'Olivier','Alban Roger','ACTIF',9,'207',NULL),(181,'Recalt','Herve','ACTIF',9,'220',NULL),(183,'Recalt','Jean Paul','ACTIF',9,'222',NULL),(185,'Reina','Frederic','ACTIF',9,'257',NULL),(187,'Sallaberry','Jean Michel','ACTIF',9,'211',NULL),(189,'Sarda','Manon Marie','ACTIF',12,'Admin',NULL),(191,'Sebilo','Allan Georges Gerard','ACTIF',9,'Production',NULL),(193,'Simon','Thomas Thierry Didier','ACTIF',9,'Production',NULL),(195,'Soubiran','Veronique Sophie','ACTIF',13,'Laboratoire',NULL),(197,'Sublime','Cyril Georges Andre','ACTIF',9,'208',NULL),(199,'Tardy','Jean Marie','ACTIF',9,'Production',NULL),(203,'Verge','Remy','ACTIF',9,'Production',NULL),(205,'Althabe','Michel','ACTIF',9,'205',NULL),(207,'Arhancetebehere','Didier','ACTIF',9,'218',NULL),(209,'Arrouge','Thomas','ACTIF',11,'Maitenance',NULL),(211,'Bergez','Franck','ACTIF',9,'228',NULL),(213,'Charman','Maxime Daniel','ACTIF',9,'214',NULL),(215,'Couchiniave','Sonia','ACTIF',9,'202',NULL),(219,'Gauchet','Steve Jean Rene','ACTIF',9,'206',NULL),(221,'Gaudin','Alexandra','ACTIF',9,'243',NULL),(223,'Gerony','Carole','ACTIF',9,'229',NULL),(225,'Gesse','Marie Claire','ACTIF',9,'230',NULL),(227,'Guiresse','Brigitte','ACTIF',9,'203',NULL),(229,'Epelva','François','ACTIF',9,'Production',NULL),(231,'Picot','Frederic','ACTIF',9,'Production',NULL),(233,'Dos Santos','Elisa','ACTIF',12,'Admin',NULL),(235,'Moureu','Marie Laure','ACTIF',9,'201',NULL),(237,'Lepolard','Aurélien Michel','ACTIF',NULL,NULL,NULL),(238,'Poli','Xabi Saint Martin','ACTIF',9,'Production',NULL),(240,'Denecker','Charlotte','ACTIF',12,'Admin',NULL),(242,'Heguiabehere','Alexandre','ACTIF',9,'Production',NULL),(244,'Remon','Florian','ACTIF',9,'Production',NULL),(246,'Barat','Romain','ACTIF',12,'Admin',NULL),(248,'Dutter','Muriel','ACTIF',13,'Labo',NULL),(250,'Berreterot','Julien','ACTIF',9,'Production',NULL),(252,'Capuret','Anthony','ACTIF',9,'Production',NULL),(254,'Rabineau','Nicolas','ACTIF',12,'Admin',NULL),(256,'Deslandes','Laurent','ACTIF',9,'Production',NULL),(258,'Erbin','Julien','ACTIF',9,'Production',NULL),(260,'Lepolard','Baptiste','ACTIF',9,'Production',NULL),(262,'Aren','Pierre','ACTIF',9,'Production',NULL),(264,'Lauga','Frédéric','ACTIF',9,'Production',NULL),(266,'Campane','Lionel','ACTIF',9,'Production',NULL),(268,'Dumollard','Thierry','ACTIF',9,'Production',NULL),(270,'Jelassi','Joël Jean','ACTIF',11,'Maintenance',NULL),(272,'Dumurlourteau','Vincent','ACTIF',9,'Production',NULL),(274,'Ramonteuchiros','Ludovic','ACTIF',9,'Production',NULL),(276,'Havy','Floriant','ACTIF',9,'Production',NULL),(278,'Deverite','Jonathan','ACTIF',9,'Production',NULL),(280,'Larroque','Guillaume','ACTIF',11,'Maintenance',NULL),(282,'Peyrou','Maxime','ACTIF',9,'Production',NULL),(284,'Lascoumes','Marie','ACTIF',12,'Admin',NULL),(286,'Salmon','Quentin','ACTIF',9,'Production',NULL),(288,'El Hamouchi','Mohamed','ACTIF',13,'Laboratoire',NULL),(290,'Chammam','Marwa','ACTIF',12,'Administratif',NULL),(292,'Rebiere','Théo Romain','ACTIF',10,'R&D',NULL),(294,'Dennemont','Valentin','ACTIF',9,'Production',NULL),(296,'Courties','Paul Marc','ACTIF',9,'Production',NULL),(302,'Gonzalez Merg','Paulo Cristiano','ACTIF',9,'Production',NULL),(304,'Loureiro','Michel','ACTIF',9,'Production',NULL),(308,'Fernandez','Yohan','ACTIF',9,'Production',NULL),(310,'Pelegrinelli','Damien','ACTIF',9,'Production',NULL),(314,'Courties','Clérik','ACTIF',9,'Production',NULL),(316,'Duchamp','Lionel','ACTIF',9,'Production',NULL),(318,'Saiz Fernandez','Kévin','ACTIF',9,'Production',NULL),(320,'Etcheverry','Fabien','ACTIF',9,'Production',NULL),(322,'Tardy','Maxime','ACTIF',9,'Production',NULL),(326,'Bergeron','Marie-Noëlle','ACTIF',13,'Laboratoire',NULL),(328,'Munoz Teres','Vanessa','ACTIF',16,'Qualite',NULL),(330,'Da Costaramos','Sergio','ACTIF',9,'Production',NULL),(332,'Chardin','Kévin','ACTIF',NULL,NULL,NULL),(335,'Loustalot','Marlène','ACTIF',14,'Cariste-Hse',NULL),(337,'Brana','Jeanpaul','ACTIF',9,'Production',NULL),(339,'Etcheberriborde','Julie','ACTIF',12,'Admin',NULL),(341,'Da Costa Silva','Sonia','ACTIF',NULL,NULL,NULL),(342,'Mosqueda','Martin','ACTIF',NULL,NULL,NULL),(343,'Gelard','Alain','ACTIF',NULL,NULL,NULL),(344,'Idiart','Céline','ACTIF',12,'Administratif',NULL),(348,'Etcheverry','Adrien','ACTIF',NULL,NULL,NULL),(349,'Michaut','Bettan','ACTIF',11,'Maintenance',NULL),(357,'Thiery','Adrien','ACTIF',14,'Agent Hse - Cariste',NULL),(359,'Revidiego','Isabelle','ACTIF',14,'Agent Hse',NULL),(361,'Sauve','Amaïa','ACTIF',9,'Production',NULL),(363,'Lajournade','Antoine','ACTIF',15,'Methode',NULL),(365,'Banquet','Marine','ACTIF',16,'Qualite',NULL),(367,'Fretay','Sabrina','ACTIF',14,'Hse',NULL),(369,'Colas','Martin','ACTIF',12,'Admin',NULL);
/*!40000 ALTER TABLE `personnel` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_backup_20251124_141820`
--

DROP TABLE IF EXISTS `personnel_backup_20251124_141820`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_backup_20251124_141820` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `prenom` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `statut` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `service_id` int DEFAULT NULL,
  `numposte` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `matricule` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_matricule` (`matricule`),
  UNIQUE KEY `uc_personnel` (`nom`,`prenom`)
) ENGINE=InnoDB AUTO_INCREMENT=370 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_backup_20251124_141820`
--

LOCK TABLES `personnel_backup_20251124_141820` WRITE;
/*!40000 ALTER TABLE `personnel_backup_20251124_141820` DISABLE KEYS */;
INSERT INTO `personnel_backup_20251124_141820` VALUES (1,'ACEDO','Sebastien','INACTIF',NULL,NULL,'M000001'),(2,'AGUERRE','Stephane','ACTIF',NULL,'','M000002'),(3,'BAGDASARIANI','Eduardi','ACTIF',1,'PRODUCTION','M000003'),(4,'BEHEREGARAY','Jean michel','INACTIF',1,'200','M000004'),(5,'BENGOCHEA','Emmanuel','ACTIF',1,'PRODUCTION','M000005'),(6,'BIDONDO','Anthony','ACTIF',1,'PRODUCTION','M000006'),(7,'BIDONDO','Michael','ACTIF',NULL,NULL,'M000007'),(8,'BIDONDO','Pierre','ACTIF',1,'247','M000008'),(9,'BRANKAER','Alexandre','ACTIF',1,'PRODUCTION','M000009'),(10,'CAMPANE','Jean francois','ACTIF',NULL,NULL,'M000010'),(11,'CARRICABURU','Alain','ACTIF',NULL,'','M000011'),(12,'CAZENAVE','Jean','ACTIF',1,'PRODUCTION','M000012'),(13,'CORDANI','Jean marie','ACTIF',NULL,NULL,'M000013'),(14,'CORREIA DOS SANTOS','Jorg','ACTIF',NULL,NULL,'M000014'),(15,'COSTA','Daniel','ACTIF',1,'342','M000015'),(16,'COUCHINAVE','Eric','ACTIF',NULL,NULL,'M000016'),(17,'COURTIES','Doryan','ACTIF',9,'PRODUCTION','M000017'),(18,'DA COSTA','Sergio','ACTIF',NULL,NULL,'M000018'),(19,'DAVIES','Edouard','INACTIF',1,'PRODUCTION','M000019'),(20,'DELGADO','Cedric','ACTIF',9,'PRODUCTION','M000020'),(21,'DEVAUX','David','INACTIF',1,'PRODUCTION','M000021'),(22,'DOS SANTOS','Charly','ACTIF',1,'PRODUCTION 1404','M000022'),(23,'ETCHEVERRY','Frederic','ACTIF',9,'PRODUCTION','M000023'),(24,'FERNANDEZ','Thomas','ACTIF',1,'PRODUCTION','M000024'),(25,'GONOT','Damien','ACTIF',1,'PRODUCTION','M000025'),(26,'GOUVINHAS','Alexandre','ACTIF',1,'PRODUCTION','M000026'),(27,'GUIMON','Alain','ACTIF',1,'LEADER','M000027'),(28,'LUQUET','Francois','ACTIF',NULL,NULL,'M000028'),(29,'MARCADIEU','Cedric','ACTIF',NULL,NULL,'M000029'),(30,'MARTA','Frederic','ACTIF',NULL,NULL,'M000030'),(31,'MERCIRIS','Theo','INACTIF',NULL,NULL,'M000031'),(32,'MILAGE','Alban','ACTIF',1,'PRODUCTION','M000032'),(33,'MOLUS','Sonia','ACTIF',1,'PRODUCTION','M000033'),(34,'MONTOIS','Xabi','ACTIF',1,'PRODUCTION','M000034'),(35,'MORIAT','Andre','INACTIF',NULL,NULL,'M000035'),(36,'MOUSTROUS','Herve','ACTIF',1,'PRODUCTION','M000036'),(37,'ORDUNA','Pierre','ACTIF',1,'PRODUCTION','M000037'),(38,'OYHENART','Nicolas','ACTIF',1,'PRODUCTION','M000038'),(39,'PEREZ','Xavier','ACTIF',1,'PRODUCTION','M000039'),(40,'POCHELU','Andre maurice','ACTIF',1,'PRODUCTION','M000040'),(41,'POISSONNET','Jean louis','ACTIF',NULL,NULL,'M000041'),(42,'POUTOU','Eldon tresor','ACTIF',NULL,NULL,'M000042'),(43,'RICE','Matthew','ACTIF',1,'PRODUCTION','M000043'),(44,'SALLETTE','Frederic','ACTIF',NULL,NULL,'M000044'),(45,'SARALEGUI','Eric','ACTIF',1,'PRODUCTION','M000045'),(46,'SERVANT','Mikaël','ACTIF',NULL,NULL,'M000046'),(47,'SICRE','Pierre','ACTIF',1,'342','M000047'),(48,'TRADERE','Jonathan','ACTIF',9,'PRODUCTION','M000048'),(49,'UNANUA','Dominique','ACTIF',1,'PRODUCTION','M000049'),(50,'URRUTIA','Laurent','ACTIF',1,'PRODUCTION','M000050'),(51,'VASSEUR','Joffrey','ACTIF',1,'PRODUCTION','M000051'),(52,'VERGE','Olivier','ACTIF',1,'PRODUCTION','M000052'),(76,'VARIN','Fabien','ACTIF',NULL,NULL,'M000076'),(99,'ETCHEVERRIA','Joaquim','ACTIF',1,'PRODUCTION','M000099'),(100,'LAURENT','Alain','ACTIF',NULL,NULL,'M000100'),(107,'AMAT','Romain florian','ACTIF',NULL,'',NULL),(108,'PERARO','Mickael eric michel','ACTIF',9,'PRODUCTION',NULL),(111,'ARNAL','Jean marie','ACTIF',NULL,'',NULL),(112,'BAILLY','Xavier marc jean','ACTIF',9,'PRODUCTION',NULL),(114,'BERCAITS','Francois marie','ACTIF',9,'PRODUCTION',NULL),(116,'BERHO','Inaki','ACTIF',9,'PRODUCTION',NULL),(118,'BERROGAIN','Jean baptiste','ACTIF',9,'242',NULL),(120,'BERTHE','Ophelie jeanne suzanne','ACTIF',9,'PRODUCTION',NULL),(122,'BIDONDO','Mickael alexandre','ACTIF',9,'PRODUCTION',NULL),(124,'BOULDOIRES','Mathieu','ACTIF',10,'R&D',NULL),(126,'CAMY','Alain','ACTIF',9,'PRODUCTION',NULL),(128,'CASTEX','Laurent christian','ACTIF',9,'PRODUCTION',NULL),(130,'CORDANI','Jeanmarie joseph','ACTIF',9,'PRODUCTION',NULL),(132,'CORREIA DOS SANTOS','Jorge manuel','ACTIF',9,'PRODUCTION',NULL),(136,'DAGUERRE','Patrick jean claude','ACTIF',9,'233',NULL),(138,'DAUBAS','Georges michel','ACTIF',9,'PRODUCTION',NULL),(142,'DUHALDE','Pierre sauveur','ACTIF',9,'PRODUCTION',NULL),(144,'ERRECART','Serge','ACTIF',9,'PRODUCTION',NULL),(148,'FERNANDES','Marie francoise','ACTIF',13,'LABORATOIRE',NULL),(150,'GODFRIN','David','ACTIF',9,'226',NULL),(152,'GOUVERT','Caroline catherine josephine','ACTIF',9,'222',NULL),(154,'HEUGAS','Jeremy','ACTIF',NULL,'243/241',NULL),(155,'IGLESIAS','Ludovic malik','ACTIF',9,'PRODUCTION',NULL),(157,'ITURRIA','Loic','ACTIF',11,'MAINTENANCE',NULL),(159,'JIMENEZ','Andre','ACTIF',9,'264',NULL),(161,'JOUMAH','Hassan','ACTIF',9,'240',NULL),(163,'KERN','Bernard','ACTIF',9,'PRODUCTION',NULL),(165,'LAC PEYRAS','Pascale','ACTIF',9,'241',NULL),(167,'LAGOURGUE','Didier guillermo','ACTIF',9,'PRODUCTION',NULL),(169,'LARRABURU','Pascale','ACTIF',13,'LABORATOIRE',NULL),(171,'LORDON','Jeanbaptiste','ACTIF',9,'PRODUCTION',NULL),(173,'MAFFRAND','Alexis','ACTIF',9,'PRODUCTION',NULL),(175,'MARQUES','Pauline marie elodie','ACTIF',9,'PRODUCTION',NULL),(177,'MENDRIBIL','Alain','ACTIF',9,'PRODUCTION',NULL),(179,'OLIVIER','Alban roger','ACTIF',9,'207',NULL),(181,'RECALT','Herve','ACTIF',9,'220',NULL),(183,'RECALT','Jean paul','ACTIF',9,'222',NULL),(185,'REINA','Frederic','ACTIF',9,'257',NULL),(187,'SALLABERRY','Jean michel','ACTIF',9,'211',NULL),(189,'SARDA','Manon marie','ACTIF',12,'ADMIN',NULL),(191,'SEBILO','Allan georges gerard','ACTIF',9,'PRODUCTION',NULL),(193,'SIMON','Thomas thierry didier','ACTIF',9,'PRODUCTION',NULL),(195,'SOUBIRAN','Veronique sophie','ACTIF',13,'LABORATOIRE',NULL),(197,'SUBLIME','Cyril georges andre','ACTIF',9,'208',NULL),(199,'TARDY','Jean marie','ACTIF',9,'PRODUCTION',NULL),(203,'VERGE','Remy','ACTIF',9,'PRODUCTION',NULL),(205,'ALTHABE','Michel','ACTIF',9,'205',NULL),(207,'ARHANCETEBEHERE','Didier','ACTIF',9,'218',NULL),(209,'ARROUGE','Thomas','ACTIF',11,'MAITENANCE',NULL),(211,'BERGEZ','Franck','ACTIF',9,'228',NULL),(213,'CHARMAN','Maxime daniel','ACTIF',9,'214',NULL),(215,'COUCHINIAV','Sonia','ACTIF',9,'202',NULL),(217,'COUCHINIAV','Eric','ACTIF',9,'PRODUCTION',NULL),(219,'GAUCHET','Steve jean rene','ACTIF',9,'206',NULL),(221,'GAUDIN','Alexandra','ACTIF',9,'243',NULL),(223,'GERONY','Carole','ACTIF',9,'229',NULL),(225,'GESSE','Marie claire','ACTIF',9,'230',NULL),(227,'GUIRESSE','Brigitte','ACTIF',9,'203',NULL),(229,'EPELVA','Franºois','ACTIF',9,'PRODUCTION',NULL),(231,'PICOT','Frederic','ACTIF',9,'PRODUCTION',NULL),(233,'DOS SANTOS','Elisa','ACTIF',12,'ADMIN',NULL),(235,'MOUREU','Marie laure','ACTIF',9,'201',NULL),(237,'LEPOLARD','Aur®lien michel','ACTIF',NULL,'',NULL),(238,'POLI','Xabi saint martin','ACTIF',9,'PRODUCTION',NULL),(240,'DENECKER','Charlotte','ACTIF',12,'ADMIN',NULL),(242,'HEGUIABEHERE','Alexandre','ACTIF',9,'PRODUCTION',NULL),(244,'REMON','Florian','ACTIF',9,'PRODUCTION',NULL),(246,'BARAT','Romain','ACTIF',12,'ADMIN',NULL),(248,'DUTTER','Muriel','ACTIF',13,'LABO',NULL),(250,'BERRETEROT','Julien','ACTIF',9,'PRODUCTION',NULL),(252,'CAPURET','Anthony','ACTIF',9,'PRODUCTION',NULL),(254,'RABINEAU','Nicolas','ACTIF',12,'ADMIN',NULL),(256,'DESLANDES','Laurent','ACTIF',9,'PRODUCTION',NULL),(258,'ERBIN','Julien','ACTIF',9,'PRODUCTION',NULL),(260,'LEPOLARD','Baptiste','ACTIF',9,'PRODUCTION',NULL),(262,'AREN','Pierre','ACTIF',9,'PRODUCTION',NULL),(264,'LAUGA','Fr®d®ric','ACTIF',9,'PRODUCTION',NULL),(266,'CAMPANE','Lionel','ACTIF',9,'PRODUCTION',NULL),(268,'DUMOLLARD','Thierry','ACTIF',9,'PRODUCTION',NULL),(270,'JELASSI','Jo½ljean','ACTIF',11,'MAINTENANCE',NULL),(272,'DUMURLOURTEAU','Vincent','ACTIF',9,'PRODUCTION',NULL),(274,'RAMONTEUCHIROS','Ludovic','ACTIF',9,'PRODUCTION',NULL),(276,'HAVY','Floriant','ACTIF',9,'PRODUCTION',NULL),(278,'DEVERITE','Jonathan','ACTIF',9,'PRODUCTION',NULL),(280,'LARROQUE','Guillaume','ACTIF',11,'MAINTENANCE',NULL),(282,'PEYROU','Maxime','ACTIF',9,'PRODUCTION',NULL),(284,'LASCOUMES','Marie','ACTIF',12,'ADMIN',NULL),(286,'SALMON','Quentin','ACTIF',9,'PRODUCTION',NULL),(288,'EL HAMOUCHI','Mohamed','ACTIF',13,'LABORATOIRE',NULL),(290,'CHAMMAM','Marwa','ACTIF',12,'ADMINISTRATIF',NULL),(292,'REBIERE','Th®o romain','ACTIF',10,'R&D',NULL),(294,'DENNEMONT','Valentin','ACTIF',9,'PRODUCTION',NULL),(296,'COURTIES','Paul marc','ACTIF',9,'PRODUCTION',NULL),(298,'LUQUET','Franºois','ACTIF',9,'PRODUCTION',NULL),(300,'POISSONNET','Jeanlouis','ACTIF',9,'PRODUCTION',NULL),(302,'GONZALEZ MERG','Paulo cristiano','ACTIF',9,'PRODUCTION',NULL),(304,'LOUREIRO','Michel','ACTIF',9,'PRODUCTION',NULL),(306,'SERVANT','Mika½l','ACTIF',9,'PRODUCTION',NULL),(308,'FERNANDEZ','Yohan','ACTIF',9,'PRODUCTION',NULL),(310,'PELEGRINELLI','Damien','ACTIF',9,'PRODUCTION',NULL),(312,'SALLETTE','Fr®d®ric','ACTIF',9,'PRODUCTION',NULL),(314,'COURTIES','Cl®rik','ACTIF',9,'PRODUCTION',NULL),(316,'DUCHAMP','Lionel','ACTIF',9,'PRODUCTION',NULL),(318,'SAIZ FERNANDEZ','K®vin','ACTIF',9,'PRODUCTION',NULL),(320,'ETCHEVERRY','Fabien','ACTIF',9,'PRODUCTION',NULL),(322,'TARDY','Maxime','ACTIF',9,'PRODUCTION',NULL),(324,'CAMPANE','Jeanfranºois','ACTIF',9,'PRODUCTION',NULL),(326,'BERGERON','Marieno½le','ACTIF',13,'LABORATOIRE',NULL),(328,'MUNOZ TERES','Vanessa','ACTIF',16,'QUALITE',NULL),(330,'DA COSTARAMOS','Sergio','ACTIF',9,'PRODUCTION',NULL),(332,'CHARDIN','K®vin','ACTIF',NULL,'',NULL),(333,'MARTA','Fr®d®ric','ACTIF',NULL,'',NULL),(334,'ACEDO','S®bastien','ACTIF',NULL,'',NULL),(335,'LOUSTALOT','Marl¿ne','ACTIF',14,'Cariste-HSE',NULL),(337,'BRANA','Jeanpaul','ACTIF',9,'PRODUCTION',NULL),(339,'ETCHEBERRIBORDE','Julie','ACTIF',12,'ADMIN',NULL),(341,'DA COSTA SILVA','Sonia','ACTIF',NULL,'',NULL),(342,'MOSQUEDA','Martin','ACTIF',NULL,'',NULL),(343,'GELARD','Alain','ACTIF',NULL,'',NULL),(344,'IDIART','C®line','ACTIF',12,'ADMINISTRATIF',NULL),(346,'MORIAT','Andr®','ACTIF',9,'PRODUCTION',NULL),(348,'ETCHEVERRY','Adrien','ACTIF',NULL,'',NULL),(349,'MICHAUT','Bettan','ACTIF',11,'MAINTENANCE',NULL),(351,'POUTOU','Eldon','ACTIF',9,'PRODUCTION',NULL),(353,'MERCIRIS','Th®o','ACTIF',9,'PRODUCTION',NULL),(355,'MARCADIEU','C®dric','ACTIF',9,'PRODUCTION',NULL),(357,'THIERY','Adrien','ACTIF',14,'Agent HSE - Cariste',NULL),(359,'REVIDIEGO','Isabelle','ACTIF',14,'Agent HSE',NULL),(361,'SAUVE','Ama»a','ACTIF',9,'PRODUCTION',NULL),(363,'LAJOURNADE','Antoine','ACTIF',15,'METHODE',NULL),(365,'BANQUET','Marine','ACTIF',16,'QUALITE',NULL),(367,'FRETAY','Sabrina','ACTIF',14,'HSE',NULL),(369,'COLAS','Martin','ACTIF',12,'ADMIN',NULL);
/*!40000 ALTER TABLE `personnel_backup_20251124_141820` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `personnel_infos`
--

DROP TABLE IF EXISTS `personnel_infos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `personnel_infos` (
  `operateur_id` int NOT NULL,
  `sexe` enum('F','M','X','NSP') COLLATE utf8mb4_general_ci DEFAULT 'NSP',
  `date_entree` date DEFAULT NULL,
  `nationalite` varchar(50) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `cp_naissance` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ville_naissance` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pays_naissance` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `date_naissance` date DEFAULT NULL,
  `adresse1` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `adresse2` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `cp_adresse` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `ville_adresse` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `pays_adresse` varchar(100) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `telephone` varchar(20) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `email` varchar(320) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `nir_chiffre` varbinary(255) DEFAULT NULL,
  `nir_nonce` varbinary(16) DEFAULT NULL,
  `nir_tag` varbinary(16) DEFAULT NULL,
  `commentaire` text COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`operateur_id`),
  UNIQUE KEY `uk_operateur_infos` (`operateur_id`),
  KEY `idx_email` (`email`),
  KEY `idx_cp_adresse` (`cp_adresse`),
  KEY `idx_ville_adresse` (`ville_adresse`),
  CONSTRAINT `fk_infos_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `personnel_infos`
--

LOCK TABLES `personnel_infos` WRITE;
/*!40000 ALTER TABLE `personnel_infos` DISABLE KEYS */;
/*!40000 ALTER TABLE `personnel_infos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `polyvalence`
--

DROP TABLE IF EXISTS `polyvalence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `polyvalence` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `poste_id` int NOT NULL,
  `niveau` int DEFAULT NULL,
  `date_evaluation` date DEFAULT NULL,
  `prochaine_evaluation` date DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `operateur_id` (`operateur_id`),
  KEY `poste_id` (`poste_id`),
  CONSTRAINT `polyvalence_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `personnel` (`id`) ON DELETE CASCADE,
  CONSTRAINT `polyvalence_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `polyvalence_chk_1` CHECK ((`niveau` between 1 and 4))
) ENGINE=InnoDB AUTO_INCREMENT=18338 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `polyvalence`
--

LOCK TABLES `polyvalence` WRITE;
/*!40000 ALTER TABLE `polyvalence` DISABLE KEYS */;
INSERT INTO `polyvalence` VALUES (17439,1,5,3,'2024-06-17','2034-06-15'),(17440,1,31,3,'2023-09-29','2033-09-26'),(17441,2,5,3,'2022-10-18','2025-12-29'),(17442,2,8,3,'2020-11-02','2030-10-31'),(17443,2,11,3,'2021-09-29','2031-09-29'),(17444,2,13,3,'2021-09-29','2031-09-29'),(17445,2,19,3,'2020-11-02','2030-10-31'),(17446,2,20,3,'2021-09-29','2031-09-29'),(17447,2,21,3,'2021-09-29','2031-09-29'),(17448,2,32,3,'2020-11-02','2030-10-31'),(17449,3,2,3,'2024-09-27','2025-12-29'),(17450,3,5,3,'2024-09-27','2025-12-31'),(17451,4,9,4,'2020-11-02','2030-10-31'),(17452,4,14,4,'2020-11-02','2030-10-31'),(17453,4,33,4,'2020-11-02','2030-10-31'),(17454,5,6,3,'2019-11-25','2029-11-22'),(17455,5,8,3,'2021-09-30','2031-09-30'),(17456,5,15,3,'2020-02-13','2030-02-11'),(17457,5,19,3,'2019-11-26','2029-11-23'),(17458,5,23,3,'2021-02-18','2031-02-17'),(17459,6,1,4,'2024-06-14','2034-06-12'),(17460,6,5,4,'2024-06-14','2034-06-12'),(17461,6,28,4,'2024-06-14','2034-06-12'),(17462,6,29,4,'2022-10-24','2032-10-21'),(17463,6,30,4,'2022-10-24','2032-10-21'),(17464,6,31,4,'2022-10-24','2032-10-21'),(17465,6,32,4,'2022-04-20','2032-04-19'),(17466,6,33,4,'2023-10-24','2033-10-31'),(17467,7,1,4,'2020-11-02','2030-10-31'),(17468,7,2,4,'2020-11-02','2030-10-31'),(17469,7,4,4,'2020-11-02','2030-10-31'),(17470,7,5,4,'2020-11-02','2030-10-31'),(17471,7,6,4,'2020-11-02','2030-10-31'),(17472,7,7,4,'2020-11-02','2030-10-31'),(17473,7,10,4,'2024-10-10','2034-10-09'),(17474,7,11,4,'2020-11-02','2030-10-31'),(17475,7,12,4,'2021-11-24','2031-11-24'),(17476,7,13,4,'2021-11-24','2031-11-24'),(17477,7,16,4,'2023-10-23','2033-10-20'),(17478,7,17,4,'2020-11-02','2030-10-31'),(17479,7,18,4,'2021-11-24','2031-11-24'),(17480,7,20,4,'2021-11-24','2031-11-24'),(17481,7,21,4,'2021-11-24','2031-11-24'),(17482,7,22,4,'2021-11-24','2031-11-24'),(17483,7,25,4,'2020-11-02','2030-10-31'),(17484,7,26,4,'2020-11-02','2030-10-31'),(17485,7,27,4,'2020-11-02','2030-10-31'),(17486,7,28,4,'2020-11-02','2030-10-31'),(17487,7,30,4,'2023-10-23','2033-10-20'),(17488,7,33,4,'2023-10-23','2033-10-20'),(17489,8,1,4,'2020-11-10','2030-11-08'),(17490,8,2,4,'2020-11-10','2030-11-08'),(17491,8,5,4,'2020-11-10','2030-11-08'),(17492,8,11,4,'2021-09-29','2031-09-29'),(17493,8,12,4,'2021-09-29','2031-09-29'),(17494,8,13,4,'2021-09-29','2031-09-29'),(17495,8,16,4,'2023-10-23','2033-10-20'),(17496,8,17,4,'2021-02-02','2031-01-31'),(17497,8,18,4,'2021-09-29','2031-09-29'),(17498,8,20,4,'2021-09-29','2031-09-29'),(17499,8,21,4,'2021-09-29','2031-09-29'),(17500,8,22,4,'2021-09-29','2031-09-29'),(17501,8,29,4,'2019-10-15','2029-10-12'),(17502,8,30,4,'2019-10-15','2025-11-28'),(17503,8,31,4,'2019-10-15','2029-10-12'),(17504,8,32,4,'2019-10-15','2029-10-12'),(17505,8,33,4,'2019-10-14','2029-10-11'),(17506,9,9,3,'2019-11-25','2029-11-22'),(17507,9,33,3,'2019-07-24','2029-07-23'),(17508,10,4,3,'2022-10-18','2032-10-15'),(17509,10,5,3,'2022-10-19','2032-10-18'),(17510,10,6,3,'2025-01-31','2035-01-31'),(17511,11,5,3,'2024-06-17','2034-06-15'),(17512,11,13,3,'2023-05-30','2033-05-27'),(17513,11,22,3,'2023-05-13','2033-05-10'),(17514,11,30,3,'2024-04-12','2034-04-10'),(17515,12,1,4,'2023-01-11','2033-01-10'),(17516,12,2,4,'2021-10-01','2031-09-29'),(17517,12,3,4,'2023-10-24','2033-10-21'),(17518,12,4,4,'2020-10-19','2030-10-17'),(17519,12,5,4,'2020-10-19','2030-10-17'),(17520,12,6,4,'2020-10-19','2030-10-17'),(17521,12,7,4,'2024-07-05','2034-07-03'),(17522,12,28,4,'2024-07-05','2034-07-03'),(17523,13,1,3,'2019-07-17','2029-07-16'),(17524,13,2,3,'2019-07-17','2029-07-16'),(17525,13,17,3,'2019-07-16','2029-07-13'),(17526,14,33,3,'2021-11-16','2031-11-14'),(17527,15,1,4,'2020-11-02','2030-10-31'),(17528,15,2,4,'2020-11-02','2030-10-31'),(17529,15,3,4,'2020-11-02','2030-10-31'),(17530,15,4,4,'2020-11-02','2030-10-31'),(17531,15,5,4,'2020-11-02','2030-10-31'),(17532,15,6,4,'2020-11-02','2030-10-31'),(17533,15,7,4,'2020-11-02','2030-10-31'),(17534,15,11,4,'2020-11-02','2030-10-31'),(17535,15,17,4,'2020-11-02','2030-10-31'),(17536,15,28,4,'2020-11-02','2030-10-31'),(17537,16,2,3,'2019-09-17','2029-09-14'),(17538,16,3,3,'2019-07-17','2029-07-16'),(17539,16,5,3,'2019-07-17','2029-07-16'),(17540,16,6,3,'2023-10-23','2033-10-20'),(17541,16,11,3,'2019-07-17','2029-07-16'),(17542,16,25,3,'2020-10-19','2030-10-17'),(17543,16,28,3,'2020-10-19','2030-10-17'),(17544,17,1,4,'2024-06-17','2034-06-15'),(17545,17,5,4,'2024-06-17','2034-06-14'),(17546,17,28,4,'2024-06-17','2034-06-14'),(17547,17,29,4,'2021-03-15','2031-03-13'),(17548,17,30,4,'2021-03-03','2031-03-03'),(17549,17,31,4,'2019-09-17','2029-09-14'),(17550,17,32,4,'2021-03-03','2031-03-03'),(17551,17,33,4,'2021-09-21','2031-09-19'),(17552,18,1,3,'2023-05-30','2033-05-27'),(17553,19,1,3,'2024-06-14','2034-06-12'),(17554,19,8,3,'2022-09-19','2032-09-16'),(17555,19,29,3,'2023-01-30','2033-01-27'),(17556,20,1,3,'2024-09-10','2034-09-08'),(17557,20,2,3,'2020-10-19','2030-10-17'),(17558,20,4,3,'2019-05-06','2029-05-03'),(17559,20,5,3,'2019-05-06','2029-05-03'),(17560,20,6,3,'2020-03-16','2030-03-14'),(17561,20,25,3,'2020-10-19','2030-10-17'),(17562,20,28,3,'2024-08-01','2034-07-31'),(17563,21,2,3,'2022-04-26','2032-04-23'),(17564,21,5,3,'2024-04-26','2034-04-24'),(17565,21,25,3,'2024-11-25','2034-11-23'),(17566,21,28,2,'2024-11-25','2025-01-24'),(17567,22,1,3,'2024-06-17','2034-06-15'),(17568,22,29,3,'2023-09-29','2033-09-26'),(17569,22,31,3,'2021-09-21','2031-09-19'),(17570,23,9,4,'2020-11-02','2030-10-31'),(17571,23,14,4,'2020-11-02','2030-10-31'),(17572,23,25,4,'2024-07-05','2034-07-03'),(17573,23,28,4,'2024-07-05','2034-07-03'),(17574,23,33,4,'2020-11-02','2030-10-31'),(17575,24,5,3,'2022-10-18','2032-10-15'),(17576,24,8,3,'2020-10-20','2030-10-18'),(17577,24,19,3,'2020-10-20','2030-10-18'),(17578,24,25,3,'2024-09-02','2034-08-31'),(17579,24,28,3,'2024-09-02','2034-08-31'),(17580,25,1,4,'2022-07-01','2032-06-28'),(17581,25,10,4,'2021-03-03','2031-03-03'),(17582,25,11,4,'2022-07-01','2032-06-28'),(17583,25,13,4,'2021-03-03','2031-03-03'),(17584,25,16,4,'2023-10-23','2033-10-20'),(17585,25,17,4,'2021-03-03','2031-03-03'),(17586,25,18,4,'2022-07-01','2032-06-28'),(17587,25,20,4,'2023-10-23','2033-10-20'),(17588,25,21,4,'2023-10-23','2033-10-20'),(17589,25,22,4,'2023-10-23','2033-10-20'),(17590,25,29,4,'2021-03-03','2031-03-03'),(17591,25,30,4,'2023-10-23','2033-10-20'),(17592,25,32,4,'2023-10-23','2033-10-20'),(17593,25,33,4,'2023-10-23','2033-10-20'),(17594,26,6,4,'2022-04-02','2032-03-30'),(17595,26,8,4,'2022-04-02','2032-03-30'),(17596,26,15,4,'2022-04-02','2032-03-30'),(17597,26,19,4,'2022-04-02','2032-03-30'),(17598,26,28,4,'2024-07-05','2034-07-03'),(17599,27,2,3,'2020-11-02','2030-10-31'),(17600,27,4,3,'2019-07-11','2029-07-09'),(17601,27,5,3,'2019-08-28','2029-08-27'),(17602,27,6,3,'2020-11-02','2030-10-31'),(17603,27,7,3,'2020-11-02','2030-10-31'),(17604,27,8,3,'2020-11-02','2030-10-31'),(17605,27,11,3,'2020-11-02','2030-10-31'),(17606,27,13,3,'2023-10-23','2033-10-20'),(17607,27,15,3,'2020-11-02','2030-10-31'),(17608,27,17,3,'2020-11-02','2030-10-31'),(17609,27,19,3,'2020-11-02','2030-10-31'),(17610,27,22,3,'2023-10-23','2033-10-20'),(17611,27,28,3,'2020-11-02','2030-10-31'),(17612,28,9,4,'2024-11-25','2034-11-23'),(17613,28,10,4,'2022-04-25','2032-04-22'),(17614,28,11,4,'2022-07-01','2032-06-28'),(17615,28,12,4,'2022-10-19','2032-10-18'),(17616,28,13,4,'2022-04-25','2032-04-22'),(17617,28,14,4,'2024-11-25','2034-11-23'),(17618,28,16,4,'2023-10-24','2033-10-21'),(17619,28,17,4,'2022-04-25','2032-04-22'),(17620,28,18,4,'2023-10-24','2033-10-21'),(17621,28,20,4,'2022-04-25','2032-04-22'),(17622,28,21,4,'2022-07-01','2032-06-28'),(17623,28,22,4,'2023-10-24','2033-10-21'),(17624,28,28,4,'2024-07-08','2034-07-06'),(17625,29,33,3,'2023-09-27','2033-09-26'),(17626,30,19,3,'2023-03-06','2033-03-03'),(17627,30,28,3,'2024-09-02','2034-08-31'),(17628,31,5,3,'2024-06-13','2034-06-12'),(17629,31,32,3,'2023-10-11','2033-10-10'),(17630,32,5,3,'2022-10-19','2032-10-18'),(17631,32,6,3,'2023-10-23','2033-10-20'),(17632,32,8,3,'2021-05-20','2031-05-19'),(17633,32,19,3,'2022-10-19','2032-10-18'),(17634,32,28,3,'2024-07-08','2034-07-06'),(17635,33,23,3,'2020-12-03','2030-12-02'),(17636,33,24,3,'2020-12-03','2030-12-02'),(17637,33,25,3,'2021-09-13','2031-09-11'),(17638,33,27,3,'2021-09-13','2031-09-11'),(17639,33,28,3,'2024-07-05','2034-07-03'),(17640,34,4,3,'2024-09-02','2034-08-31'),(17641,34,5,3,'2024-09-02','2034-08-31'),(17642,34,6,3,'2024-11-25','2034-11-23'),(17643,35,8,3,'2023-09-27','2033-09-26'),(17644,35,19,3,'2023-06-20','2033-06-17'),(17645,35,25,3,'2024-09-02','2034-08-31'),(17646,35,28,3,'2024-07-05','2034-07-03'),(17647,36,5,3,'2020-11-13','2030-11-11'),(17648,36,31,3,'2019-08-29','2029-08-27'),(17649,37,7,3,'2020-10-19','2030-10-17'),(17650,37,25,3,'2020-10-19','2030-10-17'),(17651,37,26,3,'2020-10-19','2030-10-17'),(17652,37,27,3,'2020-10-19','2030-10-17'),(17653,37,28,3,'2020-10-19','2030-10-17'),(17654,38,9,3,'2020-10-19','2030-10-17'),(17655,38,14,3,'2020-10-19','2030-10-17'),(17656,38,25,3,'2020-10-19','2030-10-17'),(17657,39,2,3,'2020-11-02','2030-10-31'),(17658,39,3,3,'2020-11-02','2030-10-31'),(17659,39,5,3,'2020-11-02','2030-10-31'),(17660,39,11,3,'2022-04-25','2032-04-22'),(17661,39,12,3,'2023-10-23','2033-10-20'),(17662,39,16,3,'2023-10-23','2033-10-20'),(17663,39,18,3,'2022-04-25','2032-04-22'),(17664,39,20,3,'2022-04-25','2032-04-22'),(17665,39,21,3,'2022-04-25','2032-04-22'),(17666,39,25,3,'2024-06-14','2034-06-12'),(17667,39,28,3,'2024-06-14','2034-06-12'),(17668,39,30,3,'2020-11-02','2030-10-31'),(17669,39,31,3,'2020-11-02','2030-10-31'),(17670,40,2,3,'2020-11-02','2030-10-31'),(17903,40,3,3,'2020-11-02','2030-10-31'),(17904,40,4,3,'2020-11-02','2030-10-31'),(17905,40,5,3,'2020-11-02','2030-10-31'),(17906,40,28,3,'2024-06-14','2034-06-12'),(17907,40,30,3,'2020-11-02','2030-10-31'),(17908,40,31,3,'2020-11-02','2030-10-31'),(17909,40,32,3,'2020-11-02','2030-10-31'),(17910,40,33,3,'2020-11-02','2030-10-31'),(17911,41,9,3,'2022-04-04','2032-04-01'),(17912,41,14,3,'2022-04-04','2032-04-01'),(17913,41,25,3,'2024-11-25','2034-11-23'),(17914,42,1,3,'2024-06-13','2034-06-12'),(17915,42,29,3,'2023-10-23','2033-10-20'),(17916,43,11,3,'2021-09-29','2031-09-29'),(17917,43,12,3,'2021-09-29','2031-09-29'),(17918,43,16,3,'2023-10-24','2033-10-21'),(17919,43,20,3,'2021-09-29','2031-09-29'),(17920,43,21,3,'2021-09-29','2031-09-29'),(17921,43,28,3,'2024-07-08','2034-07-06'),(17922,43,30,3,'2021-09-29','2031-09-29'),(17923,43,31,3,'2021-09-29','2031-09-29'),(17924,44,2,3,'2022-10-24','2032-10-21'),(17925,44,3,3,'2022-10-24','2032-10-21'),(17926,44,5,3,'2022-10-24','2032-10-21'),(17927,44,6,3,'2022-10-24','2032-10-21'),(17928,45,2,3,'2019-09-16','2029-09-13'),(17929,45,5,3,'2019-07-30','2029-07-27'),(17930,45,30,3,'2019-09-17','2029-09-14'),(17931,46,5,3,'2024-06-14','2034-06-12'),(17932,46,30,3,'2022-07-27','2032-07-26'),(17933,47,1,4,'2020-11-02','2030-10-31'),(17934,47,2,4,'2020-11-02','2030-10-31'),(17935,47,3,4,'2020-11-02','2030-10-31'),(17936,47,4,4,'2020-11-02','2030-10-31'),(17937,47,5,4,'2020-02-11','2030-10-31'),(17938,47,6,4,'2020-11-02','2030-10-31'),(17939,47,7,4,'2020-11-02','2030-10-31'),(17940,47,11,4,'2020-11-02','2030-10-31'),(17941,47,17,4,'2020-11-02','2030-10-31'),(17942,47,28,4,'2020-11-02','2030-10-31'),(17943,47,31,4,'2020-11-02','2030-10-31'),(17944,48,1,3,'2020-11-02','2030-10-31'),(17945,48,9,3,'2023-03-09','2033-03-07'),(17946,48,29,3,'2020-11-02','2030-10-31'),(17947,49,5,3,'2022-04-03','2032-03-31'),(17948,49,6,3,'2022-04-03','2032-03-31'),(17949,49,8,3,'2024-09-11','2034-09-11'),(17950,49,15,3,'2022-04-03','2032-03-31'),(17951,49,28,3,'2025-10-15','2025-11-14'),(17952,50,15,3,'2024-07-05','2034-07-03'),(17953,51,1,4,'2020-11-02','2030-10-31'),(17954,51,2,4,'2020-11-02','2030-10-31'),(17955,51,4,4,'2020-11-02','2030-10-31'),(17956,51,5,4,'2020-11-02','2030-10-31'),(17957,51,6,4,'2020-11-02','2030-10-31'),(17958,51,28,4,'2024-06-13','2034-06-12'),(17959,51,29,4,'2020-11-02','2030-10-31'),(17960,51,30,4,'2020-11-02','2030-10-31'),(18251,51,31,4,'2020-11-02','2030-10-31'),(18252,51,32,4,'2020-12-10','2030-12-09'),(18253,51,33,4,'2020-11-02','2030-10-31'),(18254,52,9,3,'2020-11-02','2030-10-31'),(18255,52,14,3,'2020-11-02','2030-10-31'),(18271,76,31,2,'2025-09-16','2025-10-16'),(18284,12,77,4,'2025-04-07','2035-04-09'),(18289,99,5,3,'2025-10-15','2025-11-14'),(18290,99,32,3,'2025-10-15','2025-11-14'),(18291,100,32,1,'2025-10-15','2025-11-14'),(18293,2,28,3,NULL,'2025-11-19'),(18299,15,77,4,NULL,'2025-11-27'),(18300,16,77,3,NULL,'2025-11-27'),(18301,20,77,3,NULL,'2025-11-27'),(18302,28,77,4,NULL,'2025-11-27'),(18303,28,7,4,NULL,'2025-11-27'),(18304,34,7,3,NULL,'2025-11-27'),(18305,34,77,3,NULL,'2025-11-27'),(18306,44,77,3,NULL,'2025-11-27'),(18307,47,77,4,NULL,'2025-11-27'),(18308,16,7,3,NULL,'2025-11-27'),(18309,20,7,3,NULL,'2025-11-27'),(18310,32,25,3,NULL,'2025-11-27'),(18311,44,7,3,NULL,'2025-11-27'),(18312,51,3,4,NULL,'2025-11-27'),(18315,3,2,4,NULL,'2025-12-29'),(18316,3,2,3,NULL,'2025-12-29'),(18317,3,2,4,NULL,'2025-12-29'),(18318,3,2,3,NULL,'2025-12-29'),(18319,2,5,4,NULL,'2025-12-29'),(18320,2,5,3,NULL,'2025-12-29'),(18321,2,5,4,NULL,'2025-12-29'),(18322,2,5,3,NULL,'2025-12-29'),(18323,2,5,4,NULL,'2025-12-29'),(18324,2,5,3,NULL,'2025-12-29'),(18325,2,5,4,NULL,'2025-12-29'),(18326,2,5,3,NULL,'2025-12-29'),(18329,3,5,4,NULL,'2025-12-31'),(18330,3,5,3,NULL,'2025-12-31');
/*!40000 ALTER TABLE `polyvalence` ENABLE KEYS */;
UNLOCK TABLES;
ALTER DATABASE `emac_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
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
ALTER DATABASE `emac_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
ALTER DATABASE `emac_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;
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
ALTER DATABASE `emac_db` CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci ;

--
-- Table structure for table `postes`
--

DROP TABLE IF EXISTS `postes`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `postes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `poste_code` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `besoins_postes` int NOT NULL DEFAULT '0',
  `visible` tinyint(1) DEFAULT '1',
  `atelier_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_atelier` (`atelier_id`),
  CONSTRAINT `fk_atelier` FOREIGN KEY (`atelier_id`) REFERENCES `atelier` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=82 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `postes`
--

LOCK TABLES `postes` WRITE;
/*!40000 ALTER TABLE `postes` DISABLE KEYS */;
INSERT INTO `postes` VALUES (1,'0506',3,1,5),(2,'0507',3,1,5),(3,'0510',3,1,5),(4,'0514',3,1,5),(5,'0515',3,1,5),(6,'0516',2,1,NULL),(7,'0560',2,1,5),(8,'0830',3,1,NULL),(9,'0900',3,1,NULL),(10,'0901',1,1,NULL),(11,'0902',1,1,NULL),(12,'0903',1,1,NULL),(13,'0906',1,1,NULL),(14,'0910',2,1,NULL),(15,'0912',2,1,5),(16,'0920',2,1,NULL),(17,'0923',1,1,NULL),(18,'0924',1,1,NULL),(19,'0930',2,1,NULL),(20,'0940',1,1,NULL),(21,'0941',1,1,NULL),(22,'0942',1,1,NULL),(23,'1007',1,1,10),(24,'1026',1,1,10),(25,'1100',1,1,11),(26,'1101',1,1,11),(27,'1103',1,1,11),(28,'1121',2,1,11),(29,'1401',3,1,14),(30,'1402',3,1,14),(31,'1404',3,1,14),(32,'1406',3,1,NULL),(33,'1412',3,1,14),(77,'0561',2,1,NULL);
/*!40000 ALTER TABLE `postes` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `services`
--

DROP TABLE IF EXISTS `services`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `services` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom_service` varchar(100) COLLATE utf8mb4_general_ci NOT NULL,
  `description` text COLLATE utf8mb4_general_ci,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=17 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `services`
--

LOCK TABLES `services` WRITE;
/*!40000 ALTER TABLE `services` DISABLE KEYS */;
INSERT INTO `services` VALUES (1,'PRODUCTION','Personnel de production'),(2,'R&D','Recherche et développement'),(3,'MAINTENANCE','Service maintenance'),(4,'ADMIN','Administratif'),(5,'LABO','Laboratoire'),(6,'HSE','Hygiène, Sécurité, Environnement'),(7,'METHODES','Méthodes / industrialisation'),(8,'QUALITE','Service qualité'),(9,'PRODUCTION','Personnel de production'),(10,'R&D','Recherche et développement'),(11,'MAINTENANCE','Service maintenance'),(12,'ADMIN','Administratif'),(13,'LABO','Laboratoire'),(14,'HSE','Hygiène, Sécurité, Environnement'),(15,'METHODES','Méthodes et industrialisation'),(16,'QUALITE','Service qualité');
/*!40000 ALTER TABLE `services` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `solde_conges`
--

DROP TABLE IF EXISTS `solde_conges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `solde_conges` (
  `id` int NOT NULL AUTO_INCREMENT,
  `personnel_id` int NOT NULL,
  `annee` int NOT NULL,
  `cp_acquis` decimal(5,2) DEFAULT '0.00' COMMENT 'CP acquis dans l année',
  `cp_n_1` decimal(5,2) DEFAULT '0.00' COMMENT 'CP reportés de N-1',
  `cp_pris` decimal(5,2) DEFAULT '0.00' COMMENT 'CP déjà pris',
  `rtt_acquis` decimal(5,2) DEFAULT '0.00',
  `rtt_pris` decimal(5,2) DEFAULT '0.00',
  `date_maj` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
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
INSERT INTO `solde_conges` VALUES (1,2,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(2,3,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(3,5,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(4,6,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(5,7,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(6,8,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(7,9,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(8,10,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(9,11,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(10,12,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(11,13,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(12,14,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(13,15,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(14,16,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(15,17,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(16,18,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(17,20,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(18,22,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(19,23,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(20,24,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(21,25,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(22,26,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(23,27,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(24,28,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(25,29,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(26,30,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(27,32,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(28,33,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(29,34,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(30,36,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(31,37,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(32,38,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(33,39,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(34,40,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(35,41,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(36,42,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(37,43,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(38,44,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(39,45,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(40,46,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(41,47,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(42,48,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(43,49,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(44,50,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(45,51,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(46,52,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(47,76,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(48,99,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(49,100,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(50,108,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(51,111,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(52,112,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(53,114,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(54,116,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(55,118,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(56,120,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(57,124,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(58,126,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(59,128,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(60,136,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(61,138,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(62,142,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(63,144,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(64,148,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(65,150,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(66,152,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(67,154,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(68,155,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(69,157,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(70,159,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(71,161,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(72,163,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(73,165,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(74,167,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(75,169,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(76,171,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(77,173,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(78,175,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(79,177,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(80,179,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(81,181,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(82,183,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(83,185,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(84,187,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(85,189,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(86,191,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(87,193,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(88,195,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(89,197,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(90,199,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(91,203,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(92,205,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(93,207,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(94,209,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(95,211,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(96,213,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(97,215,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(98,219,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(99,221,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(100,223,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(101,225,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(102,227,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(103,229,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(104,231,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(105,233,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(106,235,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(107,237,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(108,238,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(109,240,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(110,242,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(111,244,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(112,246,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(113,248,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(114,250,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(115,252,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(116,254,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(117,256,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(118,258,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(119,260,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(120,262,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(121,264,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(122,266,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(123,268,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(124,270,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(125,272,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(126,274,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(127,276,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(128,278,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(129,280,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(130,282,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(131,284,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(132,286,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(133,288,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(134,290,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(135,292,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(136,294,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(137,296,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(138,302,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(139,304,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(140,308,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(141,310,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(142,314,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(143,316,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(144,318,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(145,320,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(146,322,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(147,326,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(148,328,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(149,330,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(150,332,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(151,335,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(152,337,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(153,339,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(154,341,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(155,342,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(156,343,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(157,344,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(158,348,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(159,349,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(160,357,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(161,359,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(162,361,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(163,363,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(164,365,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(165,367,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50'),(166,369,2025,25.00,0.00,0.00,10.00,0.00,'2025-12-02 09:30:50');
/*!40000 ALTER TABLE `solde_conges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `tranche_age`
--

DROP TABLE IF EXISTS `tranche_age`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tranche_age` (
  `id` int NOT NULL AUTO_INCREMENT,
  `libelle` varchar(50) COLLATE utf8mb4_general_ci NOT NULL,
  `age_min` int NOT NULL,
  `age_max` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `tranche_age`
--

LOCK TABLES `tranche_age` WRITE;
/*!40000 ALTER TABLE `tranche_age` DISABLE KEYS */;
INSERT INTO `tranche_age` VALUES (1,'0-25 ans',0,25),(2,'26-45 ans',26,45),(3,'46-54 ans',46,54),(4,'55 ans et +',55,NULL);
/*!40000 ALTER TABLE `tranche_age` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `type_absence`
--

DROP TABLE IF EXISTS `type_absence`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `type_absence` (
  `id` int NOT NULL AUTO_INCREMENT,
  `code` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `libelle` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `decompte_solde` tinyint(1) DEFAULT '1' COMMENT 'Si TRUE, décompte du solde de congés',
  `couleur` varchar(7) COLLATE utf8mb4_unicode_ci DEFAULT '#3498db' COMMENT 'Couleur pour le calendrier (format hex)',
  `actif` tinyint(1) DEFAULT '1',
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
INSERT INTO `type_absence` VALUES (1,'CP','Congés Payés',1,'#27ae60',1),(2,'RTT','RTT',1,'#3498db',1),(3,'MALADIE','Arrêt Maladie',0,'#e74c3c',1),(4,'SANS_SOLDE','Congé Sans Solde',0,'#95a5a6',1),(5,'MATERNITE','Congé Maternité',0,'#e91e63',1),(6,'PATERNITE','Congé Paternité',0,'#9c27b0',1),(7,'FORMATION','Formation',0,'#ff9800',1),(8,'EVENEMENT','Événement Familial',0,'#00bcd4',1),(9,'AUTRE','Autre',0,'#607d8b',1);
/*!40000 ALTER TABLE `type_absence` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Temporary view structure for view `v_absences_details`
--

DROP TABLE IF EXISTS `v_absences_details`;
/*!50001 DROP VIEW IF EXISTS `v_absences_details`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
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
 1 AS `date_creation`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_documents_complet`
--

DROP TABLE IF EXISTS `v_documents_complet`;
/*!50001 DROP VIEW IF EXISTS `v_documents_complet`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_documents_complet` AS SELECT 
 1 AS `id`,
 1 AS `operateur_id`,
 1 AS `matricule`,
 1 AS `operateur_nom`,
 1 AS `categorie_id`,
 1 AS `categorie_nom`,
 1 AS `categorie_couleur`,
 1 AS `exige_date_expiration`,
 1 AS `nom_fichier`,
 1 AS `nom_affichage`,
 1 AS `chemin_fichier`,
 1 AS `type_mime`,
 1 AS `taille_octets`,
 1 AS `taille_ko`,
 1 AS `taille_mo`,
 1 AS `date_upload`,
 1 AS `date_expiration`,
 1 AS `alerte_expiration`,
 1 AS `jours_avant_expiration`,
 1 AS `statut`,
 1 AS `notes`,
 1 AS `uploaded_by`,
 1 AS `date_creation`,
 1 AS `date_modification`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_documents_expiration_proche`
--

DROP TABLE IF EXISTS `v_documents_expiration_proche`;
/*!50001 DROP VIEW IF EXISTS `v_documents_expiration_proche`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_documents_expiration_proche` AS SELECT 
 1 AS `id`,
 1 AS `operateur_id`,
 1 AS `matricule`,
 1 AS `operateur_nom`,
 1 AS `categorie_nom`,
 1 AS `nom_affichage`,
 1 AS `date_expiration`,
 1 AS `jours_restants`,
 1 AS `statut`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_documents_stats_operateur`
--

DROP TABLE IF EXISTS `v_documents_stats_operateur`;
/*!50001 DROP VIEW IF EXISTS `v_documents_stats_operateur`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
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
 1 AS `derniere_mise_a_jour`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_soldes_disponibles`
--

DROP TABLE IF EXISTS `v_soldes_disponibles`;
/*!50001 DROP VIEW IF EXISTS `v_soldes_disponibles`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
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
 1 AS `date_maj`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_stats_absences`
--

DROP TABLE IF EXISTS `v_stats_absences`;
/*!50001 DROP VIEW IF EXISTS `v_stats_absences`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_stats_absences` AS SELECT 
 1 AS `personnel_id`,
 1 AS `nom_complet`,
 1 AS `annee`,
 1 AS `type_absence`,
 1 AS `nb_demandes`,
 1 AS `total_jours`,
 1 AS `jours_valides`,
 1 AS `jours_en_attente`*/;
SET character_set_client = @saved_cs_client;

--
-- Table structure for table `validite`
--

DROP TABLE IF EXISTS `validite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `validite` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `type_validite` enum('RQTH','OETH') COLLATE utf8mb4_general_ci NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `periodicite` enum('Périodique','Permanent') COLLATE utf8mb4_general_ci DEFAULT 'Périodique',
  `taux_incapacite` decimal(5,2) DEFAULT NULL COMMENT 'Pourcentage pour RQTH',
  `document_justificatif` varchar(255) COLLATE utf8mb4_general_ci DEFAULT NULL,
  `commentaire` text COLLATE utf8mb4_general_ci,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
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
-- Final view structure for view `v_absences_details`
--

/*!50001 DROP VIEW IF EXISTS `v_absences_details`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_absences_details` AS select `da`.`id` AS `id`,`da`.`personnel_id` AS `personnel_id`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `nom_complet`,`p`.`matricule` AS `matricule`,`ta`.`code` AS `type_code`,`ta`.`libelle` AS `type_libelle`,`ta`.`couleur` AS `couleur`,`da`.`date_debut` AS `date_debut`,`da`.`date_fin` AS `date_fin`,`da`.`demi_journee_debut` AS `demi_journee_debut`,`da`.`demi_journee_fin` AS `demi_journee_fin`,`da`.`nb_jours` AS `nb_jours`,`da`.`motif` AS `motif`,`da`.`statut` AS `statut`,(case when (`da`.`validateur_id` is not null) then concat(`v`.`prenom`,' ',`v`.`nom`) else NULL end) AS `validateur`,`da`.`date_validation` AS `date_validation`,`da`.`commentaire_validation` AS `commentaire_validation`,`da`.`date_creation` AS `date_creation` from (((`demande_absence` `da` join `personnel` `p` on((`da`.`personnel_id` = `p`.`id`))) join `type_absence` `ta` on((`da`.`type_absence_id` = `ta`.`id`))) left join `personnel` `v` on((`da`.`validateur_id` = `v`.`id`))) where (`p`.`statut` = 'ACTIF') */;
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
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_documents_complet` AS select `d`.`id` AS `id`,`d`.`operateur_id` AS `operateur_id`,`p`.`matricule` AS `matricule`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `operateur_nom`,`d`.`categorie_id` AS `categorie_id`,`c`.`nom` AS `categorie_nom`,`c`.`couleur` AS `categorie_couleur`,`c`.`exige_date_expiration` AS `exige_date_expiration`,`d`.`nom_fichier` AS `nom_fichier`,`d`.`nom_affichage` AS `nom_affichage`,`d`.`chemin_fichier` AS `chemin_fichier`,`d`.`type_mime` AS `type_mime`,`d`.`taille_octets` AS `taille_octets`,round((`d`.`taille_octets` / 1024),2) AS `taille_ko`,round((`d`.`taille_octets` / 1048576),2) AS `taille_mo`,`d`.`date_upload` AS `date_upload`,`d`.`date_expiration` AS `date_expiration`,(case when (`d`.`date_expiration` is null) then NULL when (`d`.`date_expiration` < curdate()) then 'Expiré' when (`d`.`date_expiration` <= (curdate() + interval 30 day)) then 'Expire bientôt' else 'Valide' end) AS `alerte_expiration`,(to_days(`d`.`date_expiration`) - to_days(curdate())) AS `jours_avant_expiration`,`d`.`statut` AS `statut`,`d`.`notes` AS `notes`,`d`.`uploaded_by` AS `uploaded_by`,`d`.`date_creation` AS `date_creation`,`d`.`date_modification` AS `date_modification` from ((`documents` `d` join `personnel` `p` on((`d`.`operateur_id` = `p`.`id`))) join `categories_documents` `c` on((`d`.`categorie_id` = `c`.`id`))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_documents_expiration_proche`
--

/*!50001 DROP VIEW IF EXISTS `v_documents_expiration_proche`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_documents_expiration_proche` AS select `d`.`id` AS `id`,`d`.`operateur_id` AS `operateur_id`,`p`.`matricule` AS `matricule`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `operateur_nom`,`c`.`nom` AS `categorie_nom`,`d`.`nom_affichage` AS `nom_affichage`,`d`.`date_expiration` AS `date_expiration`,(to_days(`d`.`date_expiration`) - to_days(curdate())) AS `jours_restants`,`d`.`statut` AS `statut` from ((`documents` `d` join `personnel` `p` on((`d`.`operateur_id` = `p`.`id`))) join `categories_documents` `c` on((`d`.`categorie_id` = `c`.`id`))) where ((`d`.`date_expiration` is not null) and (`d`.`date_expiration` <= (curdate() + interval 30 day)) and (`d`.`date_expiration` >= curdate()) and (`d`.`statut` = 'actif')) order by `d`.`date_expiration` */;
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
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_documents_stats_operateur` AS select `p`.`id` AS `operateur_id`,`p`.`matricule` AS `matricule`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `operateur_nom`,count(`d`.`id`) AS `total_documents`,sum((case when (`d`.`statut` = 'actif') then 1 else 0 end)) AS `documents_actifs`,sum((case when (`d`.`statut` = 'expire') then 1 else 0 end)) AS `documents_expires`,sum((case when ((`d`.`date_expiration` is not null) and (`d`.`date_expiration` <= (curdate() + interval 30 day)) and (`d`.`date_expiration` >= curdate())) then 1 else 0 end)) AS `documents_expire_bientot`,sum(`d`.`taille_octets`) AS `taille_totale_octets`,round((sum(`d`.`taille_octets`) / 1048576),2) AS `taille_totale_mo`,max(`d`.`date_upload`) AS `derniere_mise_a_jour` from (`personnel` `p` left join `documents` `d` on((`p`.`id` = `d`.`operateur_id`))) group by `p`.`id`,`p`.`matricule`,`p`.`prenom`,`p`.`nom` */;
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
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_soldes_disponibles` AS select `sc`.`id` AS `id`,`sc`.`personnel_id` AS `personnel_id`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `nom_complet`,`p`.`matricule` AS `matricule`,`sc`.`annee` AS `annee`,`sc`.`cp_acquis` AS `cp_acquis`,`sc`.`cp_n_1` AS `cp_n_1`,`sc`.`cp_pris` AS `cp_pris`,((`sc`.`cp_acquis` + `sc`.`cp_n_1`) - `sc`.`cp_pris`) AS `cp_restant`,`sc`.`rtt_acquis` AS `rtt_acquis`,`sc`.`rtt_pris` AS `rtt_pris`,(`sc`.`rtt_acquis` - `sc`.`rtt_pris`) AS `rtt_restant`,`sc`.`date_maj` AS `date_maj` from (`solde_conges` `sc` join `personnel` `p` on((`sc`.`personnel_id` = `p`.`id`))) where (`p`.`statut` = 'ACTIF') */;
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
/*!50001 SET character_set_client      = utf8mb4 */;
/*!50001 SET character_set_results     = utf8mb4 */;
/*!50001 SET collation_connection      = utf8mb4_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_stats_absences` AS select `p`.`id` AS `personnel_id`,concat(`p`.`prenom`,' ',`p`.`nom`) AS `nom_complet`,year(`da`.`date_debut`) AS `annee`,`ta`.`libelle` AS `type_absence`,count(0) AS `nb_demandes`,sum(`da`.`nb_jours`) AS `total_jours`,sum((case when (`da`.`statut` = 'VALIDEE') then `da`.`nb_jours` else 0 end)) AS `jours_valides`,sum((case when (`da`.`statut` = 'EN_ATTENTE') then `da`.`nb_jours` else 0 end)) AS `jours_en_attente` from ((`demande_absence` `da` join `personnel` `p` on((`da`.`personnel_id` = `p`.`id`))) join `type_absence` `ta` on((`da`.`type_absence_id` = `ta`.`id`))) where (`p`.`statut` = 'ACTIF') group by `p`.`id`,year(`da`.`date_debut`),`ta`.`libelle` */;
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

-- Dump completed on 2025-12-02 11:04:08
