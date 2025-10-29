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
-- Table structure for table `absences`
--

DROP TABLE IF EXISTS `absences`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `absences` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `type_absence` enum('CongePaye','RTT','SansSolde','Maladie','AccidentTravail','CongeNaissance','Formation','Autorisation','Autre') NOT NULL,
  `sous_type` varchar(50) DEFAULT NULL,
  `motif` varchar(120) DEFAULT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `statut` enum('En attente','Validé','Refusé','Annulé') NOT NULL DEFAULT 'En attente',
  `source` enum('Demande','SaisieRH','Automatique') NOT NULL DEFAULT 'Demande',
  `commentaire` text,
  `created_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` timestamp NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `absences`
--

LOCK TABLES `absences` WRITE;
/*!40000 ALTER TABLE `absences` DISABLE KEYS */;
/*!40000 ALTER TABLE `absences` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `atelier`
--

DROP TABLE IF EXISTS `atelier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `atelier` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
-- Table structure for table `compteur_conges`
--

DROP TABLE IF EXISTS `compteur_conges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `compteur_conges` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `annee` year NOT NULL,
  `cp_acquis` decimal(5,1) DEFAULT '0.0',
  `cp_pris` decimal(5,1) DEFAULT '0.0',
  `cp_restant` decimal(5,1) GENERATED ALWAYS AS ((`cp_acquis` - `cp_pris`)) STORED,
  `rtt_acquis` decimal(5,1) DEFAULT '0.0',
  `rtt_pris` decimal(5,1) DEFAULT '0.0',
  `rtt_restant` decimal(5,1) GENERATED ALWAYS AS ((`rtt_acquis` - `rtt_pris`)) STORED,
  `sans_solde_pris` decimal(5,1) DEFAULT '0.0',
  `maladie_jours` decimal(5,1) DEFAULT '0.0',
  `date_mise_a_jour` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_operateur_annee` (`operateur_id`,`annee`),
  KEY `idx_annee` (`annee`),
  CONSTRAINT `fk_compteur_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `compteur_conges`
--

LOCK TABLES `compteur_conges` WRITE;
/*!40000 ALTER TABLE `compteur_conges` DISABLE KEYS */;
/*!40000 ALTER TABLE `compteur_conges` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `conges`
--

DROP TABLE IF EXISTS `conges`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `conges` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `type_conge` enum('CP','RTT','Sans solde','Maladie','Arrêt de travail') NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `nombre_jours` decimal(4,1) NOT NULL COMMENT 'Calculé automatiquement',
  `statut` enum('En attente','Validé','Refusé','En cours','Terminé') DEFAULT 'En attente',
  `date_demande` datetime DEFAULT CURRENT_TIMESTAMP,
  `valideur_id` int DEFAULT NULL COMMENT 'ID de la personne qui valide',
  `date_validation` datetime DEFAULT NULL,
  `motif_refus` text,
  `commentaire` text,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_type` (`type_conge`),
  KEY `idx_statut` (`statut`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_conges_operateur_annee` (`operateur_id`,`date_debut`),
  CONSTRAINT `fk_conges_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `conges`
--

LOCK TABLES `conges` WRITE;
/*!40000 ALTER TABLE `conges` DISABLE KEYS */;
/*!40000 ALTER TABLE `conges` ENABLE KEYS */;
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
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tg_conges_calcul_jours` BEFORE INSERT ON `conges` FOR EACH ROW BEGIN
  
  SET NEW.nombre_jours = DATEDIFF(NEW.date_fin, NEW.date_debut) + 1;
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
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tg_conges_update_compteur` AFTER UPDATE ON `conges` FOR EACH ROW BEGIN
  IF NEW.statut = 'Valid�' AND OLD.statut != 'Valid�' THEN
    IF NEW.type_conge = 'CP' THEN
      UPDATE compteur_conges 
      SET cp_pris = cp_pris + NEW.nombre_jours
      WHERE operateur_id = NEW.operateur_id 
        AND annee = YEAR(NEW.date_debut);
    ELSEIF NEW.type_conge = 'RTT' THEN
      UPDATE compteur_conges 
      SET rtt_pris = rtt_pris + NEW.nombre_jours
      WHERE operateur_id = NEW.operateur_id 
        AND annee = YEAR(NEW.date_debut);
    END IF;
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

--
-- Table structure for table `contrat`
--

DROP TABLE IF EXISTS `contrat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `contrat` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `type_contrat` enum('Stagiaire','Apprentissage','Intérimaire','Mise à disposition GE','Etranger hors UE','Temps partiel','CDI','CDD','CIFRE') NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `etp` decimal(3,2) DEFAULT '1.00' COMMENT 'Équivalent Temps Plein',
  `categorie` enum('Ouvrier','Ouvrier qualifié','Employé','Agent de maîtrise','Cadre') DEFAULT NULL,
  `emploi` varchar(100) DEFAULT NULL,
  `salaire` decimal(10,2) DEFAULT NULL,
  `actif` tinyint(1) DEFAULT '1',
  `nom_tuteur` varchar(100) DEFAULT NULL,
  `prenom_tuteur` varchar(100) DEFAULT NULL,
  `ecole` varchar(255) DEFAULT NULL,
  `nom_ett` varchar(255) DEFAULT NULL,
  `adresse_ett` text,
  `nom_ge` varchar(255) DEFAULT NULL,
  `adresse_ge` text,
  `date_autorisation_travail` date DEFAULT NULL,
  `date_demande_autorisation` date DEFAULT NULL,
  `type_titre_autorisation` varchar(255) DEFAULT NULL,
  `numero_ordre` varchar(50) DEFAULT NULL,
  `date_limite_autorisation` date DEFAULT NULL,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_type_contrat` (`type_contrat`),
  KEY `idx_actif` (`actif`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_contrat_dates_actif` (`date_debut`,`date_fin`,`actif`),
  CONSTRAINT `fk_contrat_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `type_declaration` enum('Absence','Arrêt maladie','Accident de travail','Accident de trajet') NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `date_declaration` datetime DEFAULT CURRENT_TIMESTAMP,
  `motif` text,
  `justificatif_fourni` tinyint(1) DEFAULT '0',
  `chemin_justificatif` varchar(500) DEFAULT NULL,
  `commentaire` text,
  `lieu_accident` varchar(255) DEFAULT NULL,
  `circonstances` text,
  `temoin_nom` varchar(100) DEFAULT NULL,
  `temoin_prenom` varchar(100) DEFAULT NULL,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_type` (`type_declaration`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_date_declaration` (`date_declaration`),
  CONSTRAINT `fk_declaration_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `declaration`
--

LOCK TABLES `declaration` WRITE;
/*!40000 ALTER TABLE `declaration` DISABLE KEYS */;
/*!40000 ALTER TABLE `declaration` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `formation`
--

DROP TABLE IF EXISTS `formation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `formation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `operateur_id` int NOT NULL,
  `intitule` varchar(255) NOT NULL,
  `organisme` varchar(255) DEFAULT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date NOT NULL,
  `duree_heures` decimal(6,2) DEFAULT NULL,
  `statut` enum('Planifiée','En cours','Terminée','Annulée') DEFAULT 'Planifiée',
  `certificat_obtenu` tinyint(1) DEFAULT '0',
  `cout` decimal(10,2) DEFAULT NULL,
  `commentaire` text,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_statut` (`statut`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_formation_operateur_dates` (`operateur_id`,`date_debut`,`date_fin`),
  CONSTRAINT `fk_formation_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
  `action` varchar(255) NOT NULL,
  `operateur_id` int DEFAULT NULL,
  `poste_id` int DEFAULT NULL,
  `description` text,
  PRIMARY KEY (`id`),
  KEY `operateur_id` (`operateur_id`),
  KEY `poste_id` (`poste_id`),
  CONSTRAINT `historique_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `historique_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `historique`
--

LOCK TABLES `historique` WRITE;
/*!40000 ALTER TABLE `historique` DISABLE KEYS */;
/*!40000 ALTER TABLE `historique` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operateur_infos`
--

DROP TABLE IF EXISTS `operateur_infos`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `operateur_infos` (
  `operateur_id` int NOT NULL,
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
  `commentaire` text,
  PRIMARY KEY (`operateur_id`),
  UNIQUE KEY `uk_operateur_infos` (`operateur_id`),
  KEY `idx_email` (`email`),
  KEY `idx_cp_adresse` (`cp_adresse`),
  KEY `idx_ville_adresse` (`ville_adresse`),
  CONSTRAINT `fk_infos_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operateur_infos`
--

LOCK TABLES `operateur_infos` WRITE;
/*!40000 ALTER TABLE `operateur_infos` DISABLE KEYS */;
/*!40000 ALTER TABLE `operateur_infos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operateurs`
--

DROP TABLE IF EXISTS `operateurs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `operateurs` (
  `id` int NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) DEFAULT NULL,
  `prenom` varchar(255) DEFAULT NULL,
  `statut` varchar(255) DEFAULT NULL,
  `matricule` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_matricule` (`matricule`)
) ENGINE=InnoDB AUTO_INCREMENT=107 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operateurs`
--

LOCK TABLES `operateurs` WRITE;
/*!40000 ALTER TABLE `operateurs` DISABLE KEYS */;
INSERT INTO `operateurs` VALUES (1,'ACEDO','Sebastien','INACTIF','M000001'),(2,'AGUERRE','Stéphane','ACTIF','M000002'),(3,'BAGDASARIANI','Eduardi','ACTIF','M000003'),(4,'BEHEREGARAY','Jean Michel','INACTIF','M000004'),(5,'BENGOCHEA','Emmanuel','ACTIF','M000005'),(6,'BIDONDO','Anthony','ACTIF','M000006'),(7,'BIDONDO','Michael','ACTIF','M000007'),(8,'BIDONDO','Pierre','ACTIF','M000008'),(9,'BRANKAER','Alexandre','ACTIF','M000009'),(10,'CAMPANE','Jean François','ACTIF','M000010'),(11,'CARRICABURU','Alain','ACTIF','M000011'),(12,'CAZENAVE','Jean','ACTIF','M000012'),(13,'CORDANI','Jean Marie','ACTIF','M000013'),(14,'CORREIA DOS SANTOS','Jorg','ACTIF','M000014'),(15,'COSTA','Daniel','ACTIF','M000015'),(16,'COUCHINAVE','Eric','ACTIF','M000016'),(17,'COURTIES','Doryan','ACTIF','M000017'),(18,'DA COSTA','Sergio','ACTIF','M000018'),(19,'DAVIES','Edouard','INACTIF','M000019'),(20,'DELGADO','Cedric','ACTIF','M000020'),(21,'DEVAUX','David','INACTIF','M000021'),(22,'DOS SANTOS','Charly','ACTIF','M000022'),(23,'ETCHEVERRY','Frédéric','ACTIF','M000023'),(24,'FERNANDEZ','Thomas','ACTIF','M000024'),(25,'GONOT','Damien','ACTIF','M000025'),(26,'GOUVINHAS','Alexandre','ACTIF','M000026'),(27,'GUIMON','Alain','ACTIF','M000027'),(28,'LUQUET','François','ACTIF','M000028'),(29,'MARCADIEU','Cedric','ACTIF','M000029'),(30,'MARTA','Frédéric','ACTIF','M000030'),(31,'MERCIRIS','Theo','INACTIF','M000031'),(32,'MILAGE','Alban','ACTIF','M000032'),(33,'MOLUS','Sonia','ACTIF','M000033'),(34,'MONTOIS','Xabi','ACTIF','M000034'),(35,'MORIAT','Andre','INACTIF','M000035'),(36,'MOUSTROUS','Herve','ACTIF','M000036'),(37,'ORDUNA','Pierre','ACTIF','M000037'),(38,'OYHENART','Nicolas','ACTIF','M000038'),(39,'PEREZ','Xavier','ACTIF','M000039'),(40,'POCHELU','André Maurice','ACTIF','M000040'),(41,'POISSONNET','Jean Louis','ACTIF','M000041'),(42,'POUTOU','Eldon Tresor','ACTIF','M000042'),(43,'RICE','Matthew','ACTIF','M000043'),(44,'SALLETTE','Frédéric','ACTIF','M000044'),(45,'SARALEGUI','Eric','ACTIF','M000045'),(46,'SERVANT','Mikaël','ACTIF','M000046'),(47,'SICRE','Pierre','ACTIF','M000047'),(48,'TRADERE','Jonathan','ACTIF','M000048'),(49,'UNANUA','Dominique','ACTIF','M000049'),(50,'URRUTIA','Laurent','ACTIF','M000050'),(51,'VASSEUR','Joffrey','ACTIF','M000051'),(52,'VERGE','Olivier','ACTIF','M000052'),(76,'VARIN','Fabien','ACTIF','M000076'),(99,'ETCHEVERRIA','Joaquim','ACTIF','M000099'),(100,'LAURENT','Alain','ACTIF','M000100');
/*!40000 ALTER TABLE `operateurs` ENABLE KEYS */;
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
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER `tr_operateurs_matricule` BEFORE INSERT ON `operateurs` FOR EACH ROW BEGIN
  DECLARE next_id BIGINT;

  
  SELECT AUTO_INCREMENT
  INTO next_id
  FROM information_schema.TABLES
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'operateurs'
  LIMIT 1;

  IF NEW.matricule IS NULL OR NEW.matricule = '' THEN
    SET NEW.matricule = CONCAT('M', LPAD(next_id, 6, '0'));
  END IF;
END */;;
DELIMITER ;
/*!50003 SET sql_mode              = @saved_sql_mode */ ;
/*!50003 SET character_set_client  = @saved_cs_client */ ;
/*!50003 SET character_set_results = @saved_cs_results */ ;
/*!50003 SET collation_connection  = @saved_col_connection */ ;

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
  CONSTRAINT `polyvalence_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `polyvalence_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `polyvalence_chk_1` CHECK ((`niveau` between 1 and 4))
) ENGINE=InnoDB AUTO_INCREMENT=18315 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `polyvalence`
--

LOCK TABLES `polyvalence` WRITE;
/*!40000 ALTER TABLE `polyvalence` DISABLE KEYS */;
INSERT INTO `polyvalence` VALUES (17439,1,5,3,'2024-06-17','2034-06-15'),(17440,1,31,3,'2023-09-29','2033-09-26'),(17441,2,5,3,'2022-10-18','2032-10-15'),(17442,2,8,3,'2020-11-02','2030-10-31'),(17443,2,11,3,'2021-09-29','2031-09-29'),(17444,2,13,3,'2021-09-29','2031-09-29'),(17445,2,19,3,'2020-11-02','2030-10-31'),(17446,2,20,3,'2021-09-29','2031-09-29'),(17447,2,21,3,'2021-09-29','2031-09-29'),(17448,2,32,3,'2020-11-02','2030-10-31'),(17449,3,2,3,'2024-09-27','2034-09-25'),(17450,3,5,3,'2024-09-27','2034-09-25'),(17451,4,9,4,'2020-11-02','2030-10-31'),(17452,4,14,4,'2020-11-02','2030-10-31'),(17453,4,33,4,'2020-11-02','2030-10-31'),(17454,5,6,3,'2019-11-25','2029-11-22'),(17455,5,8,3,'2021-09-30','2031-09-30'),(17456,5,15,3,'2020-02-13','2030-02-11'),(17457,5,19,3,'2019-11-26','2029-11-23'),(17458,5,23,3,'2021-02-18','2031-02-17'),(17459,6,1,4,'2024-06-14','2034-06-12'),(17460,6,5,4,'2024-06-14','2034-06-12'),(17461,6,28,4,'2024-06-14','2034-06-12'),(17462,6,29,4,'2022-10-24','2032-10-21'),(17463,6,30,4,'2022-10-24','2032-10-21'),(17464,6,31,4,'2022-10-24','2032-10-21'),(17465,6,32,4,'2022-04-20','2032-04-19'),(17466,6,33,4,'2023-10-24','2033-10-31'),(17467,7,1,4,'2020-11-02','2030-10-31'),(17468,7,2,4,'2020-11-02','2030-10-31'),(17469,7,4,4,'2020-11-02','2030-10-31'),(17470,7,5,4,'2020-11-02','2030-10-31'),(17471,7,6,4,'2020-11-02','2030-10-31'),(17472,7,7,4,'2020-11-02','2030-10-31'),(17473,7,10,4,'2024-10-10','2034-10-09'),(17474,7,11,4,'2020-11-02','2030-10-31'),(17475,7,12,4,'2021-11-24','2031-11-24'),(17476,7,13,4,'2021-11-24','2031-11-24'),(17477,7,16,4,'2023-10-23','2033-10-20'),(17478,7,17,4,'2020-11-02','2030-10-31'),(17479,7,18,4,'2021-11-24','2031-11-24'),(17480,7,20,4,'2021-11-24','2031-11-24'),(17481,7,21,4,'2021-11-24','2031-11-24'),(17482,7,22,4,'2021-11-24','2031-11-24'),(17483,7,25,4,'2020-11-02','2030-10-31'),(17484,7,26,4,'2020-11-02','2030-10-31'),(17485,7,27,4,'2020-11-02','2030-10-31'),(17486,7,28,4,'2020-11-02','2030-10-31'),(17487,7,30,4,'2023-10-23','2033-10-20'),(17488,7,33,4,'2023-10-23','2033-10-20'),(17489,8,1,4,'2020-11-10','2030-11-08'),(17490,8,2,4,'2020-11-10','2030-11-08'),(17491,8,5,4,'2020-11-10','2030-11-08'),(17492,8,11,4,'2021-09-29','2031-09-29'),(17493,8,12,4,'2021-09-29','2031-09-29'),(17494,8,13,4,'2021-09-29','2031-09-29'),(17495,8,16,4,'2023-10-23','2033-10-20'),(17496,8,17,4,'2021-02-02','2031-01-31'),(17497,8,18,4,'2021-09-29','2031-09-29'),(17498,8,20,4,'2021-09-29','2031-09-29'),(17499,8,21,4,'2021-09-29','2031-09-29'),(17500,8,22,4,'2021-09-29','2031-09-29'),(17501,8,29,4,'2019-10-15','2029-10-12'),(17502,8,30,4,'2019-10-15','2025-11-28'),(17503,8,31,4,'2019-10-15','2029-10-12'),(17504,8,32,4,'2019-10-15','2029-10-12'),(17505,8,33,4,'2019-10-14','2029-10-11'),(17506,9,9,3,'2019-11-25','2029-11-22'),(17507,9,33,3,'2019-07-24','2029-07-23'),(17508,10,4,3,'2022-10-18','2032-10-15'),(17509,10,5,3,'2022-10-19','2032-10-18'),(17510,10,6,3,'2025-01-31','2035-01-31'),(17511,11,5,3,'2024-06-17','2034-06-15'),(17512,11,13,3,'2023-05-30','2033-05-27'),(17513,11,22,3,'2023-05-13','2033-05-10'),(17514,11,30,3,'2024-04-12','2034-04-10'),(17515,12,1,4,'2023-01-11','2033-01-10'),(17516,12,2,4,'2021-10-01','2031-09-29'),(17517,12,3,4,'2023-10-24','2033-10-21'),(17518,12,4,4,'2020-10-19','2030-10-17'),(17519,12,5,4,'2020-10-19','2030-10-17'),(17520,12,6,4,'2020-10-19','2030-10-17'),(17521,12,7,4,'2024-07-05','2034-07-03'),(17522,12,28,4,'2024-07-05','2034-07-03'),(17523,13,1,3,'2019-07-17','2029-07-16'),(17524,13,2,3,'2019-07-17','2029-07-16'),(17525,13,17,3,'2019-07-16','2029-07-13'),(17526,14,33,3,'2021-11-16','2031-11-14'),(17527,15,1,4,'2020-11-02','2030-10-31'),(17528,15,2,4,'2020-11-02','2030-10-31'),(17529,15,3,4,'2020-11-02','2030-10-31'),(17530,15,4,4,'2020-11-02','2030-10-31'),(17531,15,5,4,'2020-11-02','2030-10-31'),(17532,15,6,4,'2020-11-02','2030-10-31'),(17533,15,7,4,'2020-11-02','2030-10-31'),(17534,15,11,4,'2020-11-02','2030-10-31'),(17535,15,17,4,'2020-11-02','2030-10-31'),(17536,15,28,4,'2020-11-02','2030-10-31'),(17537,16,2,3,'2019-09-17','2029-09-14'),(17538,16,3,3,'2019-07-17','2029-07-16'),(17539,16,5,3,'2019-07-17','2029-07-16'),(17540,16,6,3,'2023-10-23','2033-10-20'),(17541,16,11,3,'2019-07-17','2029-07-16'),(17542,16,25,3,'2020-10-19','2030-10-17'),(17543,16,28,3,'2020-10-19','2030-10-17'),(17544,17,1,4,'2024-06-17','2034-06-15'),(17545,17,5,4,'2024-06-17','2034-06-14'),(17546,17,28,4,'2024-06-17','2034-06-14'),(17547,17,29,4,'2021-03-15','2031-03-13'),(17548,17,30,4,'2021-03-03','2031-03-03'),(17549,17,31,4,'2019-09-17','2029-09-14'),(17550,17,32,4,'2021-03-03','2031-03-03'),(17551,17,33,4,'2021-09-21','2031-09-19'),(17552,18,1,3,'2023-05-30','2033-05-27'),(17553,19,1,3,'2024-06-14','2034-06-12'),(17554,19,8,3,'2022-09-19','2032-09-16'),(17555,19,29,3,'2023-01-30','2033-01-27'),(17556,20,1,3,'2024-09-10','2034-09-08'),(17557,20,2,3,'2020-10-19','2030-10-17'),(17558,20,4,3,'2019-05-06','2029-05-03'),(17559,20,5,3,'2019-05-06','2029-05-03'),(17560,20,6,3,'2020-03-16','2030-03-14'),(17561,20,25,3,'2020-10-19','2030-10-17'),(17562,20,28,3,'2024-08-01','2034-07-31'),(17563,21,2,3,'2022-04-26','2032-04-23'),(17564,21,5,3,'2024-04-26','2034-04-24'),(17565,21,25,3,'2024-11-25','2034-11-23'),(17566,21,28,2,'2024-11-25','2025-01-24'),(17567,22,1,3,'2024-06-17','2034-06-15'),(17568,22,29,3,'0203-09-29','2033-09-26'),(17569,22,31,3,'2021-09-21','2031-09-19'),(17570,23,9,4,'2020-11-02','2030-10-31'),(17571,23,14,4,'2020-11-02','2030-10-31'),(17572,23,25,4,'2024-07-05','2034-07-03'),(17573,23,28,4,'2024-07-05','2034-07-03'),(17574,23,33,4,'2020-11-02','2030-10-31'),(17575,24,5,3,'2022-10-18','2032-10-15'),(17576,24,8,3,'2020-10-20','2030-10-18'),(17577,24,19,3,'2020-10-20','2030-10-18'),(17578,24,25,3,'2024-09-02','2034-08-31'),(17579,24,28,3,'2024-09-02','2034-08-31'),(17580,25,1,4,'2022-07-01','2032-06-28'),(17581,25,10,4,'2021-03-03','2031-03-03'),(17582,25,11,4,'2022-07-01','2032-06-28'),(17583,25,13,4,'2021-03-03','2031-03-03'),(17584,25,16,4,'2023-10-23','2033-10-20'),(17585,25,17,4,'2021-03-03','2031-03-03'),(17586,25,18,4,'2022-07-01','2032-06-28'),(17587,25,20,4,'2023-10-23','2033-10-20'),(17588,25,21,4,'2023-10-23','2033-10-20'),(17589,25,22,4,'2023-10-23','2033-10-20'),(17590,25,29,4,'2021-03-03','2031-03-03'),(17591,25,30,4,'2023-10-23','2033-10-20'),(17592,25,32,4,'2023-10-23','2033-10-20'),(17593,25,33,4,'2023-10-23','2033-10-20'),(17594,26,6,4,'2022-04-02','2032-03-30'),(17595,26,8,4,'2022-04-02','2032-03-30'),(17596,26,15,4,'2022-04-02','2032-03-30'),(17597,26,19,4,'2022-04-02','2032-03-30'),(17598,26,28,4,'2024-07-05','2034-07-03'),(17599,27,2,3,'2020-11-02','2030-10-31'),(17600,27,4,3,'2019-07-11','2029-07-09'),(17601,27,5,3,'2019-08-28','2029-08-27'),(17602,27,6,3,'2020-11-02','2030-10-31'),(17603,27,7,3,'2020-11-02','2030-10-31'),(17604,27,8,3,'2020-11-02','2030-10-31'),(17605,27,11,3,'2020-11-02','2030-10-31'),(17606,27,13,3,'2023-10-23','2033-10-20'),(17607,27,15,3,'2020-11-02','2030-10-31'),(17608,27,17,3,'2020-11-02','2030-10-31'),(17609,27,19,3,'2020-11-02','2030-10-31'),(17610,27,22,3,'2023-10-23','2033-10-20'),(17611,27,28,3,'2020-11-02','2030-10-31'),(17612,28,9,4,'2024-11-25','2034-11-23'),(17613,28,10,4,'2022-04-25','2032-04-22'),(17614,28,11,4,'2022-07-01','2032-06-28'),(17615,28,12,4,'2022-10-19','2032-10-18'),(17616,28,13,4,'2022-04-25','2032-04-22'),(17617,28,14,4,'2024-11-25','2034-11-23'),(17618,28,16,4,'2023-10-24','2033-10-21'),(17619,28,17,4,'2022-04-25','2032-04-22'),(17620,28,18,4,'2023-10-24','2033-10-21'),(17621,28,20,4,'2022-04-25','2032-04-22'),(17622,28,21,4,'2022-07-01','2032-06-28'),(17623,28,22,4,'2023-10-24','2033-10-21'),(17624,28,28,4,'2024-07-08','2034-07-06'),(17625,29,33,3,'2023-09-27','2033-09-26'),(17626,30,19,3,'2023-03-06','2033-03-03'),(17627,30,28,3,'2024-09-02','2034-08-31'),(17628,31,5,3,'2024-06-13','2034-06-12'),(17629,31,32,3,'2023-10-11','2033-10-10'),(17630,32,5,3,'2022-10-19','2032-10-18'),(17631,32,6,3,'2023-10-23','2033-10-20'),(17632,32,8,3,'2021-05-20','2031-05-19'),(17633,32,19,3,'2022-10-19','2032-10-18'),(17634,32,28,3,'2024-07-08','2034-07-06'),(17635,33,23,3,'2020-12-03','2030-12-02'),(17636,33,24,3,'2020-12-03','2030-12-02'),(17637,33,25,3,'2021-09-13','2031-09-11'),(17638,33,27,3,'2021-09-13','2031-09-11'),(17639,33,28,3,'2024-07-05','2034-07-03'),(17640,34,4,3,'2024-09-02','2034-08-31'),(17641,34,5,3,'2024-09-02','2034-08-31'),(17642,34,6,3,'2024-11-25','2034-11-23'),(17643,35,8,3,'2023-09-27','2033-09-26'),(17644,35,19,3,'2023-06-20','2033-06-17'),(17645,35,25,3,'2024-09-02','2034-08-31'),(17646,35,28,3,'2024-07-05','2034-07-03'),(17647,36,5,3,'2020-11-13','2030-11-11'),(17648,36,31,3,'2019-08-29','2029-08-27'),(17649,37,7,3,'2020-10-19','2030-10-17'),(17650,37,25,3,'2020-10-19','2030-10-17'),(17651,37,26,3,'2020-10-19','2030-10-17'),(17652,37,27,3,'2020-10-19','2030-10-17'),(17653,37,28,3,'2020-10-19','2030-10-17'),(17654,38,9,3,'2020-10-19','2030-10-17'),(17655,38,14,3,'2020-10-19','2030-10-17'),(17656,38,25,3,'2020-10-19','2030-10-17'),(17657,39,2,3,'2020-11-02','2030-10-31'),(17658,39,3,3,'2020-11-02','2030-10-31'),(17659,39,5,3,'2020-11-02','2030-10-31'),(17660,39,11,3,'2022-04-25','2032-04-22'),(17661,39,12,3,'2023-10-23','2033-10-20'),(17662,39,16,3,'2023-10-23','2033-10-20'),(17663,39,18,3,'2022-04-25','2032-04-22'),(17664,39,20,3,'2022-04-25','2032-04-22'),(17665,39,21,3,'2022-04-25','2032-04-22'),(17666,39,25,3,'2024-06-14','2034-06-12'),(17667,39,28,3,'2024-06-14','2034-06-12'),(17668,39,30,3,'2020-11-02','2030-10-31'),(17669,39,31,3,'2020-11-02','2030-10-31'),(17670,40,2,3,'2020-11-02','2030-10-31'),(17903,40,3,3,'2020-11-02','2030-10-31'),(17904,40,4,3,'2020-11-02','2030-10-31'),(17905,40,5,3,'2020-11-02','2030-10-31'),(17906,40,28,3,'2024-06-14','2034-06-12'),(17907,40,30,3,'2020-11-02','2030-10-31'),(17908,40,31,3,'2020-11-02','2030-10-31'),(17909,40,32,3,'2020-11-02','2030-10-31'),(17910,40,33,3,'2020-11-02','2030-10-31'),(17911,41,9,3,'2022-04-04','2032-04-01'),(17912,41,14,3,'2022-04-04','2032-04-01'),(17913,41,25,3,'2024-11-25','2034-11-23'),(17914,42,1,3,'2024-06-13','2034-06-12'),(17915,42,29,3,'2023-10-23','2033-10-20'),(17916,43,11,3,'2021-09-29','2031-09-29'),(17917,43,12,3,'2021-09-29','2031-09-29'),(17918,43,16,3,'2023-10-24','2033-10-21'),(17919,43,20,3,'2021-09-29','2031-09-29'),(17920,43,21,3,'2021-09-29','2031-09-29'),(17921,43,28,3,'2024-07-08','2034-07-06'),(17922,43,30,3,'2021-09-29','2031-09-29'),(17923,43,31,3,'2021-09-29','2031-09-29'),(17924,44,2,3,'2022-10-24','2032-10-21'),(17925,44,3,3,'2022-10-24','2032-10-21'),(17926,44,5,3,'2022-10-24','2032-10-21'),(17927,44,6,3,'2022-10-24','2032-10-21'),(17928,45,2,3,'2019-09-16','2029-09-13'),(17929,45,5,3,'2019-07-30','2029-07-27'),(17930,45,30,3,'2019-09-17','2029-09-14'),(17931,46,5,3,'2024-06-14','2034-06-12'),(17932,46,30,3,'2022-07-27','2032-07-26'),(17933,47,1,4,'2020-11-02','2030-10-31'),(17934,47,2,4,'2020-11-02','2030-10-31'),(17935,47,3,4,'2020-11-02','2030-10-31'),(17936,47,4,4,'2020-11-02','2030-10-31'),(17937,47,5,4,'2020-02-11','2030-10-31'),(17938,47,6,4,'2020-11-02','2030-10-31'),(17939,47,7,4,'2020-11-02','2030-10-31'),(17940,47,11,4,'2020-11-02','2030-10-31'),(17941,47,17,4,'2020-11-02','2030-10-31'),(17942,47,28,4,'2020-11-02','2030-10-31'),(17943,47,31,4,'2020-11-02','2030-10-31'),(17944,48,1,3,'2020-11-02','2030-10-31'),(17945,48,9,3,'2023-03-09','2033-03-07'),(17946,48,29,3,'2020-11-02','2030-10-31'),(17947,49,5,3,'2022-04-03','2032-03-31'),(17948,49,6,3,'2022-04-03','2032-03-31'),(17949,49,8,3,'2024-09-11','2034-09-11'),(17950,49,15,3,'2022-04-03','2032-03-31'),(17951,49,28,3,'2025-10-15','2025-11-14'),(17952,50,15,3,'2024-07-05','2034-07-03'),(17953,51,1,4,'2020-11-02','2030-10-31'),(17954,51,2,4,'2020-11-02','2030-10-31'),(17955,51,4,4,'2020-11-02','2030-10-31'),(17956,51,5,4,'2020-11-02','2030-10-31'),(17957,51,6,4,'2020-11-02','2030-10-31'),(17958,51,28,4,'2024-06-13','2034-06-12'),(17959,51,29,4,'2020-11-02','2030-10-31'),(17960,51,30,4,'2020-11-02','2030-10-31'),(18251,51,31,4,'2020-11-02','2030-10-31'),(18252,51,32,4,'2020-12-10','2030-12-09'),(18253,51,33,4,'2020-11-02','2030-10-31'),(18254,52,9,3,'2020-11-02','2030-10-31'),(18255,52,14,3,'2020-11-02','2030-10-31'),(18271,76,31,2,'2025-09-16','2025-10-16'),(18284,12,77,4,'2025-04-07','2035-04-09'),(18289,99,5,3,'2025-10-15','2025-11-14'),(18290,99,32,3,'2025-10-15','2025-11-14'),(18291,100,32,1,'2025-10-15','2025-11-14'),(18293,2,28,3,NULL,'2025-11-19'),(18299,15,77,4,NULL,'2025-11-27'),(18300,16,77,3,NULL,'2025-11-27'),(18301,20,77,3,NULL,'2025-11-27'),(18302,28,77,4,NULL,'2025-11-27'),(18303,28,7,4,NULL,'2025-11-27'),(18304,34,7,3,NULL,'2025-11-27'),(18305,34,77,3,NULL,'2025-11-27'),(18306,44,77,3,NULL,'2025-11-27'),(18307,47,77,4,NULL,'2025-11-27'),(18308,16,7,3,NULL,'2025-11-27'),(18309,20,7,3,NULL,'2025-11-27'),(18310,32,25,3,NULL,'2025-11-27'),(18311,44,7,3,NULL,'2025-11-27'),(18312,51,3,4,NULL,'2025-11-27'),(18313,8,30,3,NULL,'2025-11-28'),(18314,8,30,4,NULL,'2025-11-28');
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
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `postes` (
  `id` int NOT NULL AUTO_INCREMENT,
  `poste_code` varchar(50) NOT NULL,
  `besoins_postes` int NOT NULL DEFAULT '0',
  `visible` tinyint(1) DEFAULT '1',
  `atelier_id` int DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `fk_atelier` (`atelier_id`),
  CONSTRAINT `fk_atelier` FOREIGN KEY (`atelier_id`) REFERENCES `atelier` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=82 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
-- Table structure for table `tranche_age`
--

DROP TABLE IF EXISTS `tranche_age`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `tranche_age` (
  `id` int NOT NULL AUTO_INCREMENT,
  `libelle` varchar(50) NOT NULL,
  `age_min` int NOT NULL,
  `age_max` int DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=5 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
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
-- Temporary view structure for view `v_conges_actifs`
--

DROP TABLE IF EXISTS `v_conges_actifs`;
/*!50001 DROP VIEW IF EXISTS `v_conges_actifs`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_conges_actifs` AS SELECT 
 1 AS `id`,
 1 AS `matricule`,
 1 AS `operateur`,
 1 AS `type_conge`,
 1 AS `date_debut`,
 1 AS `date_fin`,
 1 AS `nombre_jours`,
 1 AS `statut`,
 1 AS `date_demande`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_operateurs_complet`
--

DROP TABLE IF EXISTS `v_operateurs_complet`;
/*!50001 DROP VIEW IF EXISTS `v_operateurs_complet`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_operateurs_complet` AS SELECT 
 1 AS `id`,
 1 AS `matricule`,
 1 AS `nom`,
 1 AS `prenom`,
 1 AS `statut`,
 1 AS `sexe`,
 1 AS `date_naissance`,
 1 AS `age`,
 1 AS `tranche_age`,
 1 AS `date_entree`,
 1 AS `email`,
 1 AS `telephone`,
 1 AS `contrat_actuel`,
 1 AS `categorie`,
 1 AS `etp`*/;
SET character_set_client = @saved_cs_client;

--
-- Temporary view structure for view `v_solde_conges`
--

DROP TABLE IF EXISTS `v_solde_conges`;
/*!50001 DROP VIEW IF EXISTS `v_solde_conges`*/;
SET @saved_cs_client     = @@character_set_client;
/*!50503 SET character_set_client = utf8mb4 */;
/*!50001 CREATE VIEW `v_solde_conges` AS SELECT 
 1 AS `matricule`,
 1 AS `operateur`,
 1 AS `annee`,
 1 AS `cp_acquis`,
 1 AS `cp_pris`,
 1 AS `cp_restant`,
 1 AS `rtt_acquis`,
 1 AS `rtt_pris`,
 1 AS `rtt_restant`*/;
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
  `type_validite` enum('RQTH','OETH') NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `periodicite` enum('Périodique','Permanent') DEFAULT 'Périodique',
  `taux_incapacite` decimal(5,2) DEFAULT NULL COMMENT 'Pourcentage pour RQTH',
  `document_justificatif` varchar(255) DEFAULT NULL,
  `commentaire` text,
  `date_creation` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `date_modification` timestamp NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_type` (`type_validite`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  CONSTRAINT `fk_validite_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `validite`
--

LOCK TABLES `validite` WRITE;
/*!40000 ALTER TABLE `validite` DISABLE KEYS */;
/*!40000 ALTER TABLE `validite` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Final view structure for view `v_conges_actifs`
--

/*!50001 DROP VIEW IF EXISTS `v_conges_actifs`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_conges_actifs` AS select `c`.`id` AS `id`,`o`.`matricule` AS `matricule`,concat(`o`.`nom`,' ',`o`.`prenom`) AS `operateur`,`c`.`type_conge` AS `type_conge`,`c`.`date_debut` AS `date_debut`,`c`.`date_fin` AS `date_fin`,`c`.`nombre_jours` AS `nombre_jours`,`c`.`statut` AS `statut`,`c`.`date_demande` AS `date_demande` from (`conges` `c` join `operateurs` `o` on((`c`.`operateur_id` = `o`.`id`))) where ((`c`.`statut` in ('En attente','Valid�','En cours')) and (`c`.`date_fin` >= curdate())) order by `c`.`date_debut` */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_operateurs_complet`
--

/*!50001 DROP VIEW IF EXISTS `v_operateurs_complet`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_operateurs_complet` AS select `o`.`id` AS `id`,`o`.`matricule` AS `matricule`,`o`.`nom` AS `nom`,`o`.`prenom` AS `prenom`,`o`.`statut` AS `statut`,`oi`.`sexe` AS `sexe`,`oi`.`date_naissance` AS `date_naissance`,timestampdiff(YEAR,`oi`.`date_naissance`,curdate()) AS `age`,(case when (timestampdiff(YEAR,`oi`.`date_naissance`,curdate()) <= 25) then '0-25 ans' when (timestampdiff(YEAR,`oi`.`date_naissance`,curdate()) <= 45) then '26-45 ans' when (timestampdiff(YEAR,`oi`.`date_naissance`,curdate()) <= 54) then '46-54 ans' else '55 ans et +' end) AS `tranche_age`,`oi`.`date_entree` AS `date_entree`,`oi`.`email` AS `email`,`oi`.`telephone` AS `telephone`,`c`.`type_contrat` AS `contrat_actuel`,`c`.`categorie` AS `categorie`,`c`.`etp` AS `etp` from ((`operateurs` `o` left join `operateur_infos` `oi` on((`o`.`id` = `oi`.`operateur_id`))) left join `contrat` `c` on(((`o`.`id` = `c`.`operateur_id`) and (`c`.`actif` = true)))) */;
/*!50001 SET character_set_client      = @saved_cs_client */;
/*!50001 SET character_set_results     = @saved_cs_results */;
/*!50001 SET collation_connection      = @saved_col_connection */;

--
-- Final view structure for view `v_solde_conges`
--

/*!50001 DROP VIEW IF EXISTS `v_solde_conges`*/;
/*!50001 SET @saved_cs_client          = @@character_set_client */;
/*!50001 SET @saved_cs_results         = @@character_set_results */;
/*!50001 SET @saved_col_connection     = @@collation_connection */;
/*!50001 SET character_set_client      = cp850 */;
/*!50001 SET character_set_results     = cp850 */;
/*!50001 SET collation_connection      = cp850_general_ci */;
/*!50001 CREATE ALGORITHM=UNDEFINED */
/*!50013 DEFINER=`root`@`localhost` SQL SECURITY DEFINER */
/*!50001 VIEW `v_solde_conges` AS select `o`.`matricule` AS `matricule`,concat(`o`.`nom`,' ',`o`.`prenom`) AS `operateur`,`cc`.`annee` AS `annee`,`cc`.`cp_acquis` AS `cp_acquis`,`cc`.`cp_pris` AS `cp_pris`,`cc`.`cp_restant` AS `cp_restant`,`cc`.`rtt_acquis` AS `rtt_acquis`,`cc`.`rtt_pris` AS `rtt_pris`,`cc`.`rtt_restant` AS `rtt_restant` from (`compteur_conges` `cc` join `operateurs` `o` on((`cc`.`operateur_id` = `o`.`id`))) where (`cc`.`annee` = year(curdate())) */;
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

-- Dump completed on 2025-10-29 14:22:27
