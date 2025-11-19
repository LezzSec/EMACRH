/*M!999999\- enable the sandbox mode */ 
-- MariaDB dump 10.19  Distrib 10.11.14-MariaDB, for debian-linux-gnu (x86_64)
--
-- Host: localhost    Database: gestionrh
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
-- Table structure for table `Classeur1`
--

DROP TABLE IF EXISTS `Classeur1`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `Classeur1` (
  `NOMFAMILLE` varchar(255) DEFAULT NULL,
  `PRENOM` varchar(255) DEFAULT NULL,
  `SEXE` varchar(50) DEFAULT NULL,
  `NAISDT` varchar(50) DEFAULT NULL,
  `ENTREEGROUPEDT` varchar(100) DEFAULT NULL,
  `EMAIL` varchar(320) DEFAULT NULL,
  `GSM` varchar(100) DEFAULT NULL,
  `ADRCPL1_0001` varchar(255) DEFAULT NULL,
  `CPOSTAL_0001` varchar(50) DEFAULT NULL,
  `VIL_0001` varchar(150) DEFAULT NULL,
  `PAY_0001` varchar(150) DEFAULT NULL,
  `COMNAIS` varchar(150) DEFAULT NULL,
  `CODEPAYSNAIS` varchar(150) DEFAULT NULL,
  `DEPARNAIS` varchar(50) DEFAULT NULL,
  `CODEPAYSNATION` varchar(150) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `Classeur1`
--

LOCK TABLES `Classeur1` WRITE;
/*!40000 ALTER TABLE `Classeur1` DISABLE KEYS */;
INSERT INTO `Classeur1` VALUES
('AMAT                                                                            ','ROMAIN              ','1','1999-08-04','2019-08-19','romainamat@hotmail.fr                                                           ','06 51 86 34 02      ','                                                  ','64130     ','MAULEON                                           ','FR ','OLORON STE MARIE          ','FR ','64','FR '),
('PERARO                                                                          ','MICKAEL             ','1','1994-02-26','2015-08-10','myke-tkt@live.fr                                                                ','06 59 16 65 24      ','                                                  ','64130     ','VIODOS - ABENSE DE BAS                            ','FR ','SAINT DIE                 ','FR ','88','FR '),
('AGUERRE                                                                         ','STEPHANE            ','1','1970-08-08','2014-01-27','steph.esteban08@yahoo.com                                                       ','07 80 38 72 37      ','                                                  ','64270     ','CARRESSE                                          ','FR ','SALIES DE BEARN           ','FR ','64','FR '),
('ARNAL                                                                           ','JEAN MARIE          ','1','1965-05-03','2003-07-01','jeanmariearnal@yahoo.com                                                        ','                    ','380 Route d\'Idaux                                 ','64130     ','IDAUX-MENDY                                       ','FR ','MAULEON LICHARRE          ','FR ','64','FR '),
('BAILLY                                                                          ','XAVIER              ','1','1971-10-14','2012-10-08','                                                                                ','07 81 91 22 24      ','Quartier Ukuarte Zocoua                           ','64130     ','GARINDEIN                                         ','FR ','NOGENT SUR MARNE          ','FR ','94','FR '),
('BEHEREGARAY                                                                     ','JEAN MICHEL         ','1','1965-02-05','1991-03-06','natetjm.b@orange.fr                                                             ','06 78 23 87 95      ','34 Impasse Chapar                                 ','64130     ','VIODOS                                            ','FR ','MAULEON                   ','FR ','64','FR '),
('BENGOCHEA                                                                       ','EMMANUEL            ','1','1970-07-09','1991-03-20','emmanuel.bengochea@sfr.fr                                                       ','07 86 40 32 53      ','BOURG                                             ','64470     ','SAUGIS                                            ','FR ','MAULEON                   ','FR ','64','FR '),
('BERCAITS                                                                        ','FRANCOIS            ','1','1959-03-24','2011-02-01','                                                                                ','                    ','PORTE DES PYRENEES                                ','64400     ','OLORON SAINTE MARIE                               ','FR ','PAU                       ','FR ','64','FR '),
('BERHO                                                                           ','INAKI               ','1','1985-08-23','2020-01-20','inakiberho@outlook.fr                                                           ','06 27 53 81 14      ','165 ROUTE DE SABRENIA                             ','64120     ','AMENDEUIX ONEIX                                   ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('BERROGAIN                                                                       ','JEAN BAPTISTE       ','1','1965-06-09','1987-11-09','batitte@gmail.com                                                               ','                    ','                                                  ','64130     ','CHERAUTE                                          ','FR ','MAULEON                   ','FR ','64','FR '),
('BERTHE                                                                          ','OPHELIE             ','2','1981-06-01','2020-01-20','ophelie_berthe@orange.fr                                                        ','07.85.53.94.73      ','LE BOURG                                          ','64130     ','IDAUX MENDY                                       ','FR ','CHAMBRAY LES TOURS        ','FR ','37','FR '),
('BIDONDO                                                                         ','MICKAEL             ','1','1996-07-17','2016-08-16','mickael6417@gmail.com                                                           ','06 75 47 19 55      ','                                                  ','64130     ','VIODOS - ABENSE DE BAS                            ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('BIDONDO                                                                         ','PIERRE              ','1','1966-10-28','1991-04-12','bidondo.pierre@orange.fr                                                        ','06 19 36 04 41      ','32 Impasse Sainte-Barbe                           ','64130     ','VIODOS - ABSENSE DE BAS                           ','FR ','UHART CIZE                ','FR ','64','FR '),
('BOULDOIRES                                                                      ','MATHIEU             ','1','1999-01-05','2019-09-02','matthieu.bouldoires44@gmail.com                                                 ','06 25 39 03 78      ','                                                  ','44560     ','PAIMBOEUF                                         ','FR ','SAINT NAZAIRE             ','FR ','44','FR '),
('BRANKAER                                                                        ','ALEXANDRE           ','1','1992-02-03','2015-06-22','alex.b64130@hotmail.fr                                                          ','06 29 15 70 77      ','                                                  ','64130     ','MAULEON                                           ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('CAMY                                                                            ','ALAIN               ','1','1960-02-15','1991-02-04','etchola.gure@orange.fr                                                          ','06 72 10 99 11      ','MAISON GURE ETCHOLA                               ','64130     ','GARINDEIN                                         ','FR ','MAULEON                   ','FR ','64','FR '),
('CASTEX                                                                          ','LAURENT             ','1','1961-06-28','2020-01-06','laurentcastex@sfr.fr                                                            ','07 79 61 78 27      ','550 ROUTE DE BAYONNE                              ','64390     ','GUINARTHE                                         ','FR ','MONTREUIL SOUS BOIS       ','FR ','75','FR '),
('CORDANI                                                                         ','JEANMARIE           ','1','1976-06-01','2015-04-07','jeanmarie.cordani@free.fr                                                       ','06 45 01 70 62      ','5 BOULEVARD GAMBETTA                              ','64130     ','MAULEON                                           ','FR ','GONESSE                   ','FR ','95','FR '),
('CORREIA DOS SANTOS                                                              ','JORGE               ','1','1969-09-03','2015-08-31','correiadossantosgeorges@gmail.com                                               ','                    ','LOT DE MENDITTE                                   ','64130     ','GARINDEIN                                         ','FR ','MARINHA GRANDE            ','PT ','  ','PT '),
('COSTA                                                                           ','DANIEL              ','1','1979-06-10','2003-11-24','d.danycos@gmail.com                                                             ','06 73 00 22 23      ','3 LOT BASTERREIX                                  ','64130     ','MAULEON                                           ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('COURTIES                                                                        ','DORYAN              ','1','1982-03-20','2019-08-19','courtiesdoryan@gmail.com                                                        ','06 30 03 16 07      ','10 PLACE DU FOIRAIL                               ','64190     ','NAVARRENX                                         ','FR ','NICE                      ','FR ','06','FR '),
('DAGUERRE                                                                        ','PATRICK             ','1','1979-05-05','2007-09-03','patdag64@hotmail.fr                                                             ','06 08 87 53 87      ','4 ROUTE DE PEYRET                                 ','64390     ','BARRAUTE-CAMU                                     ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('DAUBAS                                                                          ','GEORGES             ','1','1960-09-16','2016-10-24','tokiedermaule@outlook.fr                                                        ','06 84 26 68 32      ','MAISON TOKI EDER                                  ','64130     ','MAULEON                                           ','FR ','ARAMITS                   ','FR ','64','FR '),
('DELGADO                                                                         ','CEDRIC              ','1','1981-12-16','2019-03-12','cedricdelgado@yahoo.fr                                                          ','                    ','36 Rue de BELA                                    ','64130     ','MAULEON                                           ','FR ','PERPIGNAN                 ','FR ','66','FR '),
('DUHALDE                                                                         ','PIERRE              ','1','1961-01-28','2006-07-31','                                                                                ','06 23 74 02 15      ','7 BIS DE LA SOULE                                 ','64130     ','CHERAUTE                                          ','FR ','MAULEON LICHARRE          ','FR ','64','FR '),
('ERRECART                                                                        ','SERGE               ','1','1969-06-13','2015-01-12','sergioerrecart5@gmail.com                                                       ','06 47 93 55 59      ','117 CHEMIN DE PARENTIES                           ','64390     ','GUINARTHE                                         ','FR ','MAULEON LICHARRE          ','FR ','64','FR '),
('ETCHEVERRY                                                                      ','FREDERIC            ','1','1982-09-21','2015-01-12','etcheverryfrederic.5@gmail.com                                                  ','06 77 49 47 61      ','2 Impasse DARRIGRAND                              ','64130     ','VIODOS - ABENSE DE BAS                            ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('FERNANDES                                                                       ','MARIE               ','2','1961-05-31','2007-01-29','                                                                                ','                    ','                                                  ','64130     ','MAULEON                                           ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('GODFRIN                                                                         ','DAVID               ','1','1987-07-16','2010-10-04','64.godfrin@gmail.com                                                            ','                    ','28 LOTISSEMENT MENDY ALDE                         ','64130     ','MAULEON                                           ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('GOUVERT                                                                         ','CAROLINE            ','2','1984-11-26','2007-03-05','carogouvert@hotmail.com                                                         ','06.86.97.80.72      ','                                                  ','64130     ','MAULEON                                           ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('GUIMON                                                                          ','ALAIN               ','1','1970-12-23','1991-02-26','alain.guimon@orange.fr                                                          ','                    ','MAISON LASTETXIA                                  ','64130     ','MONCAYOLL                                         ','FR ','MAULEON                   ','FR ','64','FR '),
('HEUGAS                                                                          ','JEREMY              ','1','1984-01-08','2010-09-15','jheugas@gmail.com                                                               ','06 18 91 79 14      ','4 Bis Route de LAHITAU                            ','64390     ','BARRAUTE-CAMU                                     ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('IGLESIAS                                                                        ','LUDOVIC             ','1','1991-01-02','2020-01-13','                                                                                ','06 14 23 15 19      ','RESIDENCE O RUE JORGE SEMPRUN                     ','64150     ','MOURENX                                           ','FR ','ORTHEZ                    ','FR ','64','FR '),
('ITURRIA                                                                         ','LOIC                ','1','1996-07-10','2017-07-24','loic.iturria@gmail.com                                                          ','06 20 28 49 50      ','QUARTIER MIZ MAISON OHANTZEA                      ','64240     ','BONLOC                                            ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('JIMENEZ                                                                         ','ANDRE               ','1','1961-03-01','2002-02-20','                                                                                ','06 43 00 98 52      ','LOT TARTACHU                                      ','64130     ','GOTEIN LIBA FRANCE                                ','FR ','MAULEON                   ','FR ','64','FR '),
('JOUMAH                                                                          ','HASSAN              ','1','1961-05-25','2007-10-09','vandredy@hotmail.fr                                                             ','06 75 99 00 84      ','608 Route de Saint Palais                         ','64130     ','VIODOS ABENSE DE BAS                              ','FR ','HAOUCH ARAB               ','SY ','  ','FR '),
('KERN                                                                            ','BERNARD             ','1','1969-10-01','2015-08-24','chtiom59@hotmail.fr                                                             ','06 81 67 81 09      ','Chez M. Mme DELNSSE                               ','59150     ','WATTRELOS                                         ','FR ','TOURCOING                 ','FR ','59','FR '),
('LAC PEYRAS                                                                      ','PASCALE             ','2','1964-02-25','1991-12-02','pascale.lac-peyras@orange.fr                                                    ','                    ','                                                  ','64510     ','BORDES                                            ','FR ','PAU                       ','FR ','64','FR '),
('LAGOURGUE                                                                       ','DIDIER              ','1','1969-07-24','2013-01-07','                                                                                ','07 87 68 40 84      ','16 CITE BERGES                                    ','64270     ','CARRESSE                                          ','FR ','SALIES DE BEARN           ','FR ','64','FR '),
('LARRABURU                                                                       ','PASCALE             ','2','1969-10-10','2015-09-01','larraburu.pascale@neuf.fr                                                       ','06 81 34 12 69      ','9 CitÃ© Saint-Jean                                 ','64130     ','MAULEON                                           ','FR ','MAULEON                   ','FR ','64','FR '),
('LORDON                                                                          ','JEANBAPTISTE        ','1','1962-12-23','1987-11-09','jeanbaptiste.lordon@sfr.fr                                                      ','                    ','ARRAST LARREBIEU                                  ','64130     ','ARRAST LARI                                       ','FR ','SALIES DE BEARN           ','FR ','64','FR '),
('MAFFRAND                                                                        ','ALEXIS              ','1','1995-07-28','2019-03-04','                                                                                ','06 15 67 85 97      ','                                                  ','64130     ','MAULEON                                           ','FR ','BAYONNE                   ','FR ','64','FR '),
('MARQUES                                                                         ','PAULINE             ','2','1995-08-03','2019-06-04','                                                                                ','06 49 08 08 42      ','                                                  ','64400     ','GEUS D OLORON                                     ','FR ','PAU                       ','FR ','64','FR '),
('MENDRIBIL                                                                       ','ALAIN               ','1','1961-05-17','1994-10-13','                                                                                ','06 33 27 73 12      ','2 CHEMIN DU LAVOIR                                ','64190     ','ARAUX                                             ','FR ','NAVARRENX                 ','FR ','64','FR '),
('MOLUS                                                                           ','SONIA               ','2','1980-11-23','2020-01-06','soniamolus80@gmail.com                                                          ','06 89 29 05 06      ','197 Rue Errekaltia                                ','64130     ','ESPES UNDUREIN                                    ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('MOUSTROUS                                                                       ','HERVE               ','1','1971-10-09','2019-03-05','maiderkattinu@hotmail.fr                                                        ','06 82 98 58 69      ','4 LOT DE LA PLAINE                                ','64130     ','VIODOS ABENSE DE BAS                              ','FR ','MAULEON                   ','FR ','64','FR '),
('OLIVIER                                                                         ','ALBAN               ','1','1981-11-11','2015-06-01','alchris@cegetel.net                                                             ','06 60 38 38 80      ','                                                  ','64130     ','CHERAUTE                                          ','FR ','FONTENAY LE COMTE         ','FR ','85','FR '),
('PEREZ                                                                           ','XAVIER              ','1','1968-08-18','2003-07-01','perezmaria9897@neuf.fr                                                          ','06 12 01 64 18      ','68 BOULEVARD DES PYRENEES                         ','64130     ','MAULEON                                           ','FR ','PARIS                     ','FR ','75','FR '),
('POCHELU                                                                         ','ANDRE               ','1','1968-08-07','2003-11-24','andre.pochelu@sfr.fr                                                            ','                    ','ITHORROTS OLHAIBY                                 ','64120     ','ITHORROTS OLHAIBY                                 ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('RECALT                                                                          ','HERVE               ','1','1981-10-06','2004-11-01','herve.recalt@wanadoo.fr                                                         ','06 71 92 43 20      ','MONTORY                                           ','64470     ','MONTORY                                           ','FR ','OLORON SAINTE MARTE       ','FR ','64','FR '),
('RECALT                                                                          ','JEAN PAUL           ','1','1973-03-18','1994-10-26','nanirecalt@hotmail.fr                                                           ','                    ','QUARTIER ARROQUAIN ALTIA                          ','64130     ','GARINDEIN                                         ','FR ','MAULEON                   ','FR ','64','FR '),
('REINA                                                                           ','FREDERIC            ','1','1967-10-18','2000-02-23','reina.frederic64@gmail.com                                                      ','06 77 54 43 29      ','70 BOULEVARD DES PYRENEES                         ','64130     ','MAULEON                                           ','FR ','MAULEON                   ','FR ','64','FR '),
('SALLABERRY                                                                      ','JEAN MICHEL         ','1','1969-05-09','1991-02-23','jmmaga@hotmail.fr                                                               ','07.81.34.73.86      ','56 Chemin Aizagerrea                              ','64130     ','CHERAUTE                                          ','FR ','MAULEON                   ','FR ','64','FR '),
('SARALEGUI                                                                       ','ERIC                ','1','1967-02-07','1991-03-01','eric.saralegui@free.fr                                                          ','06.11.96.35.62      ','CHATEAU DE CHERAUTE                               ','64130     ','CHERAUTE                                          ','FR ','MAULEON                   ','FR ','64','FR '),
('SARDA                                                                           ','MANON               ','2','1995-10-26','2019-11-12','manonsarda@hotmail.com                                                          ','07 87 69 26 37      ','Quartier Urcuray                                  ','64240     ','HASPARREN                                         ','FR ','FOIX                      ','FR ','09','FR '),
('SEBILO                                                                          ','ALLAN               ','1','1991-09-27','2019-08-05','                                                                                ','                    ','RUE LES BERGES DU JOOS                            ','64400     ','SAINT GOIN                                        ','FR ','NANTES                    ','FR ','44','FR '),
('SICRE                                                                           ','PIERRE              ','1','1970-11-03','1991-04-10','claveriesicre.helene@neuf.fr                                                    ','                    ','MAISON ARGICHENIA                                 ','64120     ','AROUE                                             ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('SIMON                                                                           ','THOMAS              ','1','1992-08-17','2013-08-19','                                                                                ','06.52.15.22.38      ','                                                  ','64130     ','MAULEON                                           ','FR ','TOULOUSE                  ','FR ','31','FR '),
('SOUBIRAN                                                                        ','VERONIQUE           ','2','1977-02-23','2012-01-02','verosoub@yahoo.fr                                                               ','06.66.93.89.57      ','2 CitÃ© Louis BEGUERIE                             ','64130     ','MAULEON                                           ','FR ','TOULOUSE                  ','FR ','31','FR '),
('SUBLIME                                                                         ','CYRIL               ','1','1977-10-18','2014-01-06','cyrilsublime@yahoo.fr                                                           ','06.95.75.19.88      ','201 ALLEE D HARIA                                 ','64240     ','BRISCOUS                                          ','FR ','LODEVE                    ','FR ','34','FR '),
('TARDY                                                                           ','JEAN MARIE          ','1','1963-08-15','2000-04-03','rivegauche@sfr.fr                                                               ','                    ','7 CHEMIN DES FOSSES                               ','64270     ','BELLOCQ                                           ','FR ','LISLE ADAM                ','FR ','78','FR '),
('TRADERE                                                                         ','JONATHAN            ','1','1986-11-19','2017-06-19','tradere@hotmail.fr                                                              ','06.80.22.14.58      ','1 ROUTE DES PYRENEES                              ','64190     ','GESTAS                                            ','FR ','ORTHEZ                    ','FR ','64','FR '),
('VASSEUR                                                                         ','JOFFREY             ','1','1993-07-13','2013-08-19','Joffrey.Vasseur13@gmail.com                                                     ','06.35.40.80.38      ','                                                  ','64390     ','ESPIUTE                                           ','FR ','CALAIS                    ','FR ','62','FR '),
('VERGE                                                                           ','OLIVIER             ','1','1968-08-16','2004-07-01','vergefamilly@gmail.com                                                          ','06.81.44.77.37      ','MAISON CASAMAYOU                                  ','64190     ','GESTAS                                            ','FR ','SALIES DE BEARN           ','FR ','64','FR '),
('VERGE                                                                           ','REMY                ','1','1999-03-09','2017-10-30','                                                                                ','06.87.77.51.14      ','Maison Lascroudzades                              ','64270     ','Labastide Villefranche                            ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('ALTHABE                                                                         ','MICHEL              ','1','1974-09-11','2000-10-04','                                                                                ','06 19 84 05 66      ','                                                  ','64130     ','MAULEON                                           ','FR ','MAULEON                   ','FR ','64','FR '),
('ARHANCETEBEHERE                                                                 ','DIDIER              ','1','1967-04-23','1991-04-18','                                                                                ','                    ','QUARTIER GAGNECO URUPEA                           ','64130     ','ESPES UNDU                                        ','FR ','MAULEON                   ','FR ','64','FR '),
('ARROUGE                                                                         ','THOMAS              ','1','1997-12-28','2019-08-28','                                                                                ','06.01.39.30.71      ','1 AVENUE JEAN MERMOZ                              ','64400     ','GOES                                              ','FR ','PAU                       ','FR ','64','FR '),
('BERGEZ                                                                          ','FRANCK              ','1','1981-10-20','2001-11-26','bergez.laeti@icloud.com                                                         ','                    ','2158 Voie de la Soule                             ','64130     ','ESPES-UNDUREIN                                    ','FR ','MOURENX                   ','FR ','64','FR '),
('CHARMAN                                                                         ','MAXIME              ','1','1985-08-21','2008-09-22','maxime.aurelie40360@gmail.com                                                   ','06 82 48 58 72      ','845 Route de Dax                                  ','40360     ','POMAREZ                                           ','FR ','TOULOUSE                  ','FR ','31','FR '),
('COUCHINIAV                                                                      ','SONIA               ','2','1978-03-09','2003-04-01','thierry.couchinave@orange.fr                                                    ','                    ','MAISON ELISSALT                                   ','64130     ','ARRAST LARREBIEU                                  ','FR ','MAULEON                   ','FR ','64','FR '),
('COUCHINIAV                                                                      ','ERIC                ','1','1977-08-06','2013-03-04','ericcouchinave@gmail.com                                                        ','06.37.40.20.96      ','                                                  ','64400     ','GEUS D\'OLORON                                     ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('GAUCHET                                                                         ','STEVE               ','1','1991-06-12','2013-12-31','steeve.gauchet@gmail.com                                                        ','06 27 30 86 28      ','3 IMPASSE DES FOSSES                              ','64120     ','SAINT PALAIS                                      ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('GAUDIN                                                                          ','ALEXANDRA           ','2','1980-02-28','2002-11-25','                                                                                ','                    ','HAMEAU LARREBIEU                                  ','64130     ','ARRAST LARREBIEU                                  ','FR ','LIBOURNE                  ','FR ','33','FR '),
('GERONY                                                                          ','CAROLE              ','2','1976-11-04','2017-11-20','carolegerony@gmail.com                                                          ','06 28 19 67 23      ','291 Chemin RECALDE                                ','64130     ','VIODOS - ABENSE DE BAS                            ','FR ','MAULEON                   ','FR ','64','FR '),
('GESSE                                                                           ','MARIE CLAIRE        ','2','1966-01-08','2018-11-19','marie.claire.gesse@orange.fr                                                    ','06 81 28 81 81      ','16 ALLEE DES FOUGERES                             ','64400     ','AREN                                              ','FR ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('GUIRESSE                                                                        ','BRIGITTE            ','2','1961-05-04','1982-03-01','                                                                                ','06 31 81 23 31      ','AINHARP                                           ','64130     ','AINHARP                                           ','FR ','IDAUX MENDY               ','FR ','64','FR '),
('ORDUNA                                                                          ','PIERRE              ','1','1999-09-02','2020-02-03','pierre.ordu64@gmail.com                                                         ','06 28 02 62 66      ','5 LOTISSEMENT BASTERREIX                          ','64130     ','MAULEON                                           ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('EPELVA                                                                          ','FranÃ§ois            ','1','1981-05-27','2020-02-24','                                                                                ','                    ','35 Avenue de La GARE                              ','64120     ','SAINT PALAIS                                      ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('PICOT                                                                           ','FREDERIC            ','1','1977-01-12','2020-02-10','chicopicot@gmail.com                                                            ','06 95 38 36 79      ','Passage Raymond De Longueil                       ','64190     ','NAVARRENX                                         ','FR ','ORTHEZ                    ','FR ','64','FR '),
('DOS SANTOS                                                                      ','Elisa               ','2','1994-03-17','2020-03-17','elisa_santos1234@hotmail.com                                                    ','06 21 13 15 35      ','5 AllÃ©e du Petit Tres                             ','40390     ','SAINT MARTIN DE SEIGNANX                          ','   ','PARIS 14eme               ','FR ','75','FR '),
('MOUREU                                                                          ','MARIE LAURE         ','2','1976-10-13','2016-11-07','j_moureu@orange.fr                                                              ','06.11.02.61.64      ','RD 27 NÂ°1300                                      ','ANDREIN   ','64390                                             ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('CAZENAVE                                                                        ','JEAN                ','1','2002-04-22','2020-07-20','cazenavejean2@gmail.com                                                         ','07 82 90 35 78      ','6 Chemin Deus Tourouns                            ','64190     ','RIVEHAUTE                                         ','FR ','SAINT PALAIS              ','FR ','64','FR '),
('LEPOLARD                                                                        ',' Michel                                                                ','69','1','   ','                    ','                    ','                                                                                ','   ','                                                  ','MAULEON                                           ','1985-02-26','Auxerre                   ','FR ','89'),
('POLI                                                                            ',' Saint','1,97106E+12','82','0','                    ','64008','FR ','SAINT-JEAN-PIED-DE PORT                           ','                                                  ','                                                  ','1','1997-10-18','Bayonne                   ','FR '),
('DENECKER                                                                        ','Charlotte           ','2','1989-08-20','2019-11-12','charlotte.denecker@gmail.com                                          ','06 28 43 22 63      ','95 Avenue de Rangueil                             ','31400     ','TOULOUSE                                          ','FR ','Mourenx                   ','FR ','64','FR '),
('HEGUIABEHERE                                                                    ','Alexandre           ','1','1996-03-05','','alexandre-heguiabehere@laposte.net                                              ','                    ','18 Rue des PyrÃ©nÃ©es                               ','64190     ','SUS                                               ','   ','Oloron Sainte Marie       ','FR ','64','FR '),
('REMON                                                                           ','Florian             ','1','1991-04-04','','flairssfmr@hotmail.fr                                                           ','06 31 82 03 80      ','Appartement 1                                     ','64130     ','MAULEON                                           ','   ','Saint-Palais              ','FR ','64','FR '),
('FERNANDEZ                                                                       ','Thomas              ','1','1996-12-09','','thomasfernandez64@icloud.com                                                    ','06 22 76 17 64      ','15 Rue LABAT                                      ','64130     ','MAULEON                                           ','   ','Pau                       ','FR ','64','FR '),
('BARAT                                                                           ','Romain              ','1','1974-01-25','2019-11-12','romainbarat4@gmail.com                                                ','06 82 37 06 31      ','42 Rue des Vignes                                 ','64230     ','DENGUIN                                           ','FR ','Pamiers                   ','FR ','09','FR '),
('DUTTER                                                                          ','Muriel              ','2','1975-06-06','2020-10-01','mumys64@yahoo.fr                                                      ','06 15 79 50 99      ','4 Route de la Soule                               ','64190     ','PRECHACQ JOSBAIG                                  ','FR ','Oloron Sainte Marie       ','FR ','64','FR '),
('OYHENART                                                                        ','Nicolas             ','1','1997-09-12','','nico.oyhenart@gmail.com                                                         ','                    ','50 Impasse Chapar                                 ','64130     ','VIODOS - ABENSE-DE-BAS                            ','FR ','Oloron Sainte Marie       ','FR ','64','FR '),
('BERRETEROT                                                                      ','Julien              ','1','1987-03-24','','                                                                                ','                    ','Chemin LASCORRY                                   ','64130     ','VIODOS - ABENSE DE BAS                            ','   ','Saint-Palais              ','FR ','64','FR '),
('GONOT                                                                           ','Damien              ','1','1999-06-08','','egonot@club-internet.fr                                                         ','06 15 01 96 64      ','Route de Lambarre                                 ','64130     ','GARINDEIN                                         ','FR ','Saint-Palais              ','FR ','64','FR '),
('CAPURET                                                                         ','Anthony             ','1','1994-12-29','','anthony.capuret64130@gmail.com                                                  ','0768593398          ','8 Rue Maurice RAVEL                               ','64130     ','MAULEON                                           ','   ','Pau                       ','FR ','64','FR '),
('RABINEAU                                                                        ','Nicolas             ','1','1997-06-06','2021-01-04','rabineau.nicolas55@gmail.com                                          ','06 88 64 18 68      ','17 Rue des MIMOSAS                                ','64230     ','LESCAR                                            ','FR ','Nancy                     ','FR ','54','FR '),
('DESLANDES                                                                       ','Laurent             ','1','1968-07-30','2021-01-11','laurent.deslandes32@gmail.com                                         ','06 65 30 35 08      ','41 Rue Saint-Germain                              ','64190     ','NAVARRENX                                         ','   ','Tournan En Brie           ','FR ','77','FR '),
('ERBIN                                                                           ','Julien              ','1','2000-11-15','','                                                                                ','06 84 83 55 10      ','8 Chemin Serbielle                                ','64190     ','ANGOUS                                            ','   ','Pau                       ','FR ','64','FR '),
('LEPOLARD                                                                        ','Baptiste            ','1','1990-10-16','','lepolard.baptiste@gmail.com                                                     ','07 88 38 60 37      ','1 Chemin de l\'Usine                               ','64130     ','VIODOS ABENSE DE BAS                              ','   ','Auxerre                   ','FR ','89','FR '),
('AREN                                                                            ','Pierre              ','1','1997-05-12','','pierrearen@icloud.com                                                           ','06 19 74 53 83      ','31 Rue des FrÃ¨res Barenne                         ','64130     ','MAULEON                                           ','   ','Oloron-Sainte-Marie       ','FR ','64','FR '),
('LAUGA                                                                           ','FrÃ©dÃ©ric            ','1','1988-08-20','','laugafrederic64@orange.fr                                                       ','06 09 96 88 37      ','Lotissement Les Monts                             ','64130     ','LICHOS                                            ','   ','Saint-Palais              ','FR ','64','FR '),
('CAMPANE                                                                         ','Lionel              ','1','1982-07-22','','lionel.campane@hotmail.fr                                                       ','06 70 71 26 30      ','Quartier MAIGHIA                                  ','64130     ','CHARRITTE DE BAS                                  ','   ','Bayonne                   ','FR ','64','FR '),
('DUMOLLARD                                                                       ','Thierry             ','1','1968-05-07','','thierry64150@gmail.com                                                          ','06 37 28 01 26      ','5 Impasse du CastÃ©ra                              ','64150     ','MOURENX                                           ','   ','Lourdes                   ','FR ','65','FR '),
('JELASSI                                                                         ','JoÃ«l-Jean           ','1','1979-05-09','','joel.jelassi@gmail.com                                                          ','06 68 63 04 02      ','4 Rue d\'Iraty                                     ','64130     ','MAULEON                                           ','FR ','MaulÃ©on                   ','FR ','64','FR '),
('MILAGE                                                                          ','Alban               ','1','2002-08-26','','milage.alban@gmail.com                                                          ','06 85 98 38 73      ','31 Route de CAMOUREST                             ','64190     ','NABAS                                             ','   ','SAINT-PALAIS              ','FR ','64','FR '),
('DUMUR-LOURTEAU                                                                  ','Vincent             ','1','1996-10-14','','vincentdumurpro@gmail.com                                                       ','06 74 34 74 13      ','3 Chemin LAPAGESSE                                ','64130     ','VIODOS - ABENSE DE BAS                            ','   ','Oloron Sainte Marie       ','FR ','64','FR '),
('RAMONTEU-CHIROS                                                                 ','Ludovic             ','1','1982-09-02','','ludovic.ramonteu@gmail.com                                                      ','06 76 80 08 63      ','7 Chemin du Bois                                  ','64400     ','SAINT-GOIN                                        ','   ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('HAVY                                                                            ','Floriant            ','1','2002-01-03','','floriancordani@outlook.fr                                                       ','0768463305          ','41 Rue des Patriotes                              ','02100     ','SAINT-QUENTIN                                     ','   ','Soissons                  ','FR ','02','FR '),
('DEVERITE                                                                        ','Jonathan            ','1','1985-01-17','','                                                                                ','                    ','85 Rue de La Navarre                              ','64130     ','MAULEON                                           ','   ','Bayonne                   ','FR ','64','FR '),
('LARROQUE                                                                        ','GUILLAUME           ','1','2002-07-17','2021-08-02','                                                                                ','                    ','Bourg                                             ','64130     ','IDAUX MENDY                                       ','   ','Oloron                    ','FR ','64','FR '),
('DOS SANTOS                                                                      ','CHARLY              ','1','1992-07-24','2021-08-16','dossantos.charly64@gmail.com                                                    ','                    ','8 quartier CIBI                                   ','64130     ','BERROGAIN- LARUNS                                 ','   ','Marcq en baroeul          ','FR ','59','FR '),
('RICE                                                                            ','MATTHEW             ','1','1971-09-25','2021-08-16','ricematt64@gmail.com                                                            ','                    ','245 RUE PRINCIPALE                                ','64270     ','BERGOUEY VILLENAVE                                ','FR ','BELPER                    ','EN ','  ','   '),
('PEYROU                                                                          ','Maxime              ','1','1991-01-28','','sandrine.peyrou@neuf.fr                                                         ','06 26 49 19 77      ','RN 134                                            ','64870     ','ESCOUT                                            ','   ','Oloron Sainte Marie       ','FR ','64','FR '),
('LASCOUMES                                                                       ','MARIE               ','2','1981-05-15','2021-08-16','marielascoumes@gmail.com                                                        ','                    ','1045 Route de Saint Palais                        ','64130     ','VIODOS - ABENSE DE BAS                            ','   ','BAYONNE                   ','FR ','64','FR '),
('SALMON                                                                          ','Quentin             ','1','2003-01-01','','quentin.salmon15@gmail.com                                                      ','06 52 04 23 94      ','28 Route de La Plaine                             ','64190     ','PRECHACQ-NAVARRENX                                ','   ','FougÃ¨res                  ','FR ','35','FR '),
('EL HAMOUCHI                                                                     ','Mohamed             ','1','1973-08-23','','elhamouchi64400@gmail.com                                                       ','07 83 11 08 25      ','6 Rue des Gaves                                   ','64150     ','MOURENX                                           ','   ','TAZA                      ','MA ','99','FR '),
('CHAMMAM                                                                         ','Marwa               ','2','1993-11-05','','marwachammam@gmail.com                                                          ','07 53 30 72 95      ','1 Rue Jacqueline AURIOL                           ','40100     ','DAX                                               ','   ','WEDHREF                   ','TN ','99','TN '),
('REBIERE                                                                         ',' Romain                                                                    ','51','1','   ','                    ','                    ','                                                                                ','FR ','                                                  ','PAU                                               ','1996-09-01','BORDEAUX                  ','FR ','33'),
('DENNEMONT                                                                       ','Valentin            ','1','2002-06-07','','val97477@gmail.com                                                              ','06 65 41 93 08      ','Chez Mme OcÃ©ane PLANTE                            ','64130     ','Mauleon                                           ','   ','Rochefort                 ','FR ','17','FR '),
('COURTIES                                                                        ',' Marc                                                                      ','3','1','   ','                    ','                    ','                                                                                ','   ','                                                  ','LABASTIDE-VILLEFRANCHE                            ','1994-08-06','Bayonne                   ','FR ','64'),
('GOUVINHAS                                                                       ','Alexandre           ','1','1984-09-05','','gouvinhasreal@live.fr                                                           ','06 77 43 11 94      ','Lotissement Lou Thouroun                          ','64130     ','LICHOS                                            ','   ','Oloron Sainte Marie       ','FR ','64','FR '),
('LUQUET                                                                          ','FranÃ§ois            ','1','1996-10-21','','foluquet@gmail.com                                                              ','06 46 52 69 14      ','300 Route de BOUILLOU                             ','64390     ','ANDREIN                                           ','   ','SAINT-PALAIS              ','FR ','64','FR '),
('POISSONNET                                                                      ','Jean-Louis          ','1','1973-11-13','','jeanlouispoissonnet@orange.fr                                                   ','06 38 43 81 46      ','Chemin ELISSAGUE                                  ','64130     ','CHARRITTE DE BAS                                  ','   ','MAULEON                   ','FR ','64','FR '),
('BIDONDO                                                                         ','Anthony             ','1','1998-02-20','','bidondo.anthony@gmail.com                                                       ','07 50 30 30 53      ','3015 Route Pays de Soule                          ','64130     ','ESPES-UNDUREIN                                    ','   ','SAINT-PALAIS              ','FR ','64','FR '),
('UNANUA                                                                          ','Dominique           ','1','1978-09-11','','unanuad@gmail.com                                                               ','06 48 94 99 83      ','14 Rue Jaureguiberry                              ','64130     ','MAULEON                                           ','FR ','BIARRITZ                  ','FR ','64','FR '),
('DEVAUX                                                                          ','David               ','1','1970-03-21','','devauxdavid64@gmail.com                                                         ','07 49 77 38 35      ','279 Rue des Trois Croix                           ','64130     ','ESPES-UNDUREIN                                    ','   ','SAINT-DENIS               ','FR ','93','FR '),
('GONZALEZ MERG                                                                   ','Paulo Cristiano     ','1','1972-03-25','','crismerg@hotmail.com                                                            ','07 84 24 24 81      ','1 Av. de l\'Hippodrome                             ','64130     ','MAULEON                                           ','   ','Portugal                  ','PT ','99','PT '),
('LOUREIRO                                                                        ','Michel              ','1','1976-06-01','','                                                                                ','06 30 89 38 54      ','Route de Hameau                                   ','64130     ','ESPES-UNDUREIN                                    ','   ','OLORON-SAINTE-MARIE       ','FR ','64','FR '),
('SERVANT                                                                         ','MikaÃ«l              ','1','1999-09-02','','servantmikael340@gmail.com                                                     ','06 84 75 75 95      ','3 Lot. CHOY                                       ','64270     ','TROIS-VILLES                                      ','FR ','Saint-Palais              ','FR ','64','FR '),
('FERNANDEZ                                                                       ','Yohan               ','1','1991-06-23','','lindsaycallenaere@outlook.com                                                   ','                    ','44 Rue Principale                                 ','64130     ','VIODOS - ABSENSE DE BAS                           ','   ','PAU                       ','FR ','64','FR '),
('PELEGRINELLI                                                                    ','Damien              ','1','1978-10-24','','damien.pelegrinelli@orange.fr                                                   ','                    ','                                                  ','64130     ','MENDITTE                                          ','   ','MAULEON                   ','FR ','64','FR '),
('DAVIES                                                                          ','Edouard             ','1','1974-01-23','','piperade64@gmail.com                                                            ','                    ','27 Rue Cujas                                      ','64400     ','OLORON SAINTE MARIE                               ','   ','SAINT-CYR-L\'ECOLE         ','FR ','78','FR '),
('SALLETTE                                                                        ','FrÃ©dÃ©ric            ','1','1971-05-07','','frederic.sallette@wanadoo.fr                                                  ','06 82 09 51 78      ','211 Chemin Lajussa                                ','64390     ','BURGARONNE                                        ','FR ','SAINT-PALAIS              ','FR ','64','FR '),
('COURTIES                                                                        ','ClÃ©rik              ','1','1997-01-31','','clerik.courties@gmail.com                                                      ','                    ','15 Rue de Devant                                  ','64270     ','LABASTIDE-VILLEFRANCHE                            ','   ','BAYONNE                   ','FR ','64','FR '),
('DUCHAMP                                                                         ','Lionel              ','1','1970-08-09','','lducham32@gmail.com                                                             ','                    ','15 Route de Gestas                                ','64390     ','ESPIUTE                                           ','   ','SAINT-ETIENNE             ','FR ','42','FR '),
('SAIZ FERNANDEZ                                                                  ','KÃ©vin               ','1','1991-01-15','','tisabelle33@outllok.fr                                                         ','                    ','5 Route de La Plaine                              ','64190     ','ARAUX                                             ','   ','GONESSE                   ','FR ','95','FR '),
('ETCHEVERRY                                                                      ','Fabien              ','1','1994-09-15','','etcheverryfabien00@gmail.com                                                    ','                    ','115 Chemin Urbizy                                 ','64990     ','MOUGUERRE                                         ','   ','Bayonne                   ','FR ','64','FR '),
('TARDY                                                                           ','Maxime              ','1','1995-10-26','','rivehautien@gmail.com                                                           ','                    ','15 Rue du Lavoir                                  ','64190     ','RIVEHAUTE                                         ','   ','Oloron Sainte Marie       ','FR ','64','FR '),
('CAMPANE                                                                         ','Jean-FranÃ§ois       ','1','1966-05-24','','jfcampane@outlook.fr                                                           ','                    ','Maison Etchegoyhen                                ','64470     ','CAMOU - CIHIGUE                                   ','   ','Paris 14Ã¨me               ','FR ','75','FR '),
('BERGERON                                                                        ','Marie-NoÃ«le         ','2','1971-12-07','2023-01-16','mnbergeron@yahoo.fr                                                  ','06 25 61 62 81      ','85 Route de Condou                                ','64370     ','MESPLEDE                                          ','   ','Orthez                    ','FR ','64','FR '),
('MUNOZ TERES                                                                     ','Vanessa             ','2','1992-09-30','','vanessamt92@gmail.com                                                           ','06 78 61 74 66      ','4 Av. Alsace-Lorraine                             ','64130     ','MAULEON                                           ','FR ','VILLAFRANCA               ','ES ','99','ES '),
('DA COSTA-RAMOS                                                                  ','Sergio              ','1','1975-03-17','','sergio.dacosta@orange.fr                                                        ','06 24 07 38 98      ','12 QUARTIER CIBI                                  ','64130     ','BERROGAIN-LARUNS                                  ','   ','MAULEON                   ','FR ','64','FR '),
('CARRICABURU                                                                     ','Alain               ','1','1986-07-23','','alain.carricaburu@outlook.fr                                                    ','06 79 96 31 04      ','                                                  ','64190     ','GURS                                              ','   ','OLORON SAINTE MARIE       ','FR ','64','FR '),
('CHARDIN                                                                         ','KÃ©vin               ','1','1990-12-28','','cfpalette@gmail.com                                                             ','06 03 30 71 14      ','Lot. MONSEGUR                                     ','64470     ','TARDETS                                           ','   ','ECHIROLLES                ','FR ','38','FR '),
('MARTA                                                                           ','FrÃ©dÃ©ric            ','1','1967-10-27','','arbolak@orange.fr                                                               ','06 17 78 49 75      ','                                                  ','64130     ','MAULEON                                           ','   ','AGEN                      ','FR ','47','FR '),
('ACEDO                                                                           ','SÃ©bastien           ','1','1993-09-17','','sebacedo64130@gmail.com                                                         ','06 26 67 72 59      ','                                                  ','64190     ','NABAS                                             ','   ','Bayonne                   ','FR ','64','FR '),
('LOUSTALOT                                                                       ','MarlÃ¨ne             ','2','1974-04-22','','morelmarlene@orange.fr                                                          ','06 10 71 81 94      ','12 Quartier CIBI                                  ','64130     ','BERROGAIN-LARUNS                                  ','   ','Pau                       ','FR ','64','FR '),
('BRANA                                                                           ','Jean-Paul           ','1','1971-12-27','','branajeanpaul@gmail.com                                                         ','06 79 16 32 98      ','6 Impasse du Tram                                 ','64190     ','CASTETNAU-CAMBLONG                                ','   ','NAVARRENX                 ','FR ','64','FR '),
('ETCHEBERRIBORDE                                                                 ','Julie               ','2','2002-09-23','','jetcheberriborde@gmail.com                                                      ','06 78 27 95 07      ','355 Chemin MATAXOT                                ','64130     ','IDAUX-MENDY                                       ','   ','SAINT-PALAIS              ','FR ','64','FR '),
('DA COSTA SILVA                                                                  ','Sonia               ','2','1978-04-30','','                                                                                ','                    ','RÃ©sidence Berges du Gave - Appart.22              ','64130     ','MAULEON                                           ','   ','CHAVES                    ','PT ','99','PT '),
('MOSQUEDA                                                                        ','Martin              ','1','2001-02-12','','                                                                                ','                    ','31 Rue des FrÃ¨res Barenne                         ','64130     ','MAULEON                                           ','   ','CHACO                     ','AR ','99','AR '),
('GELARD                                                                          ','Alain               ','1','1965-05-27','','                                                                                ','06 83 68 08 24      ','4 Rue Labourdette                                 ','64190     ','SUS                                               ','   ','ORTHEZ                    ','FR ','64','FR '),
('IDIART                                                                          ','CÃ©line              ','2','1976-04-24','','celine.idiart@orange.fr                                                         ','07 67 08 30 66      ','3 Rue MarÃ©chal Leclerc                            ','64130     ','MAULEON                                           ','   ','SAINT-PALAIS              ','FR ','64','FR '),
('MORIAT                                                                          ','AndrÃ©               ','1','1975-06-11','','andremoriat@sfr.fr                                                              ','06 16 23 82 94      ','220 Route de Sauveterre                           ','64300     ','ORTHEZ                                            ','FR ','LE PUY EN VELAY           ','FR ','43','FR '),
('ETCHEVERRY                                                                      ','Adrien              ','1','1991-03-07','','adrien.etcheverry.64@gmail.com                                                  ','06 74 59 78 22      ','Maison Etchettoua                                 ','64130     ','CHARRITTE DE BAS                                  ','   ','BORDEAUX                  ','FR ','33','FR '),
('MICHAUT                                                                         ','Bettan              ','1','2008-10-20','','bettan.michaut@gmail.com                                                        ','06 46 87 18 15      ','20 Chemin de l\'Osinbidea                          ','64470     ','TARDETS SORHOLUS                                  ','   ','OLORON-SAINTE-MARIE       ','FR ','64','FR '),
('POUTOU                                                                          ','Eldon               ','1','1986-07-21','','epoutou@yahoo.com                                                               ','06 71 55 07 38      ','48 Rue Mendi Alde                                 ','64130     ','MAULEON                                           ','FR ','BANGUI                    ','CF ','99','CF '),
('MERCIRIS                                                                        ','ThÃ©o                ','1','2001-02-04','','theomerciris3@gmail.com                                                         ','06 28 80 61 02      ','1 Rue du FORT                                     ','64130     ','MAULEON                                           ','   ','Chartres                  ','FR ','28','FR '),
('MARCADIEU                                                                       ','CÃ©dric              ','1','1985-04-10','','labrique40@outlook.fr                                                           ','06 85 58 98 56      ','7 Route de Saint-Palais                           ','64130     ','VIODOS ABENSE DE BAS                              ','   ','BAYONNE                   ','FR ','64','FR '),
('THIERY                                                                          ','Adrien              ','1','1981-10-24','','thieryadrien24@gmail.com                                                        ','06 33 71 82 67      ','41 Chemin d\'Etxegoihenea                          ','64470     ','CAMOU-CIHIGUE                                     ','FR ','DAX                       ','FR ','40','FR '),
('REVIDIEGO                                                                       ','Isabelle            ','2','1983-04-22','','isathiery@outlook.fr                                                            ','07 81 08 00 35      ','Impasse les Berges du Joos                        ','64400     ','SAINT-GOIN                                        ','FR ','TOULOUSE                  ','FR ','31','FR '),
('SAUVE                                                                           ','AmaÃ¯a               ','2','2004-05-11','','amaia.sauve@gmail.com                                                           ','07 83 08/ 24 18     ','7 Chemin de BÃ©rÃ©renx                              ','64190     ','NAVARRENX                                         ','   ','OLORON-SAINTE-MARIE       ','FR ','64','FR '),
('MONTOIS                                                                         ','Xabi                ','1','2006-11-24','','xabimontois641@gmail.com                                                        ','06 26 14 50 90      ','15 Route de Magnoua                               ','64190     ','RIVEHAUTE                                         ','   ','SAINT-PALAIS              ','FR ','64','FR '),
('URRUTIA                                                                         ','Laurent             ','1','1973-03-22','','                                                                                ','                    ','                                                  ','          ','                                                  ','   ','UHART-CIZE                ','FR ','64','FR '),
('LAJOURNADE                                                                      ','Antoine             ','1','2004-02-03','','antlajourande@gmail.com                                                         ','06 40 14 45 22      ','100 Chemin de Bixta Eder                          ','64120     ','ARBOUET-SUSSAUTE                                  ','   ','SAINT-PALAIS              ','FR ','64','FR '),
('BAGDASARIANI                                                                    ','Eduardi             ','1','1994-04-01','','eduardbagdasarian798@gmail.com                                                  ','07 69 65 95 29      ','6 Rue BELA                                        ','64130     ','MAULEON                                           ','   ','TBILISI                   ','GE ','99','GE '),
('BANQUET                                                                         ','Marine              ','2','1990-11-12','','marine.v.banquet@gmail.com                                                      ','0 51 87 20 23       ','19 Rue du Bourg                                   ','64320     ','IDRON                                             ','FR ','VICHY                     ','FR ','03','FR '),
('FRETAY                                                                          ','Sabrina             ','2','2004-03-10','','sabrinafretay@gmail.com                                                         ','07 71 22 60 90      ','180 Rue de la Soule                               ','64130     ','CHERAUTE                                          ','   ','Evreux                    ','FR ','27','FR '),
('COLAS                                                                           ','Martin              ','1','1997-06-06','2021-01-04','m.colas712@gmail.com                                                            ','06 17 70 08 26      ','Route de Haux                                     ','64470     ','MONTORY                                           ','FR ','Nancy                     ','FR ','54','FR '),
('ETCHEVERRIA                                                                     ','Joaquim             ','1','2004-06-12','','joaquimetcheverria459@gmail.com                                                 ','06 18 05 54 67      ','Maison Gaineko Borda                              ','64120     ','SAINT-JUST-IBARRE                                 ','   ','LA-TESTE-DE-BUCH          ','FR ','33','FR ');
/*!40000 ALTER TABLE `Classeur1` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `atelier`
--

DROP TABLE IF EXISTS `atelier`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `atelier` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=15 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `atelier`
--

LOCK TABLES `atelier` WRITE;
/*!40000 ALTER TABLE `atelier` DISABLE KEYS */;
INSERT INTO `atelier` VALUES
(5,'Atelier 5'),
(8,'Atelier 8'),
(9,'Atelier 9'),
(10,'Atelier 10'),
(11,'Atelier 11'),
(14,'Atelier 14');
/*!40000 ALTER TABLE `atelier` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `contrat`
--

DROP TABLE IF EXISTS `contrat`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `contrat` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `operateur_id` int(11) NOT NULL,
  `type_contrat` enum('Stagiaire','Apprentissage','Intérimaire','Mise à disposition GE','Etranger hors UE','Temps partiel','CDI','CDD','CIFRE') NOT NULL,
  `date_debut` date NOT NULL,
  `date_fin` date DEFAULT NULL,
  `etp` decimal(3,2) DEFAULT 1.00 COMMENT 'Équivalent Temps Plein',
  `categorie` enum('Ouvrier','Ouvrier qualifié','Employé','Agent de maîtrise','Cadre') DEFAULT NULL,
  `echelon` varchar(50) DEFAULT NULL,
  `emploi` varchar(100) DEFAULT NULL,
  `salaire` decimal(10,2) DEFAULT NULL,
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
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_type_contrat` (`type_contrat`),
  KEY `idx_actif` (`actif`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_contrat_dates_actif` (`date_debut`,`date_fin`,`actif`),
  CONSTRAINT `fk_contrat_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
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
  PRIMARY KEY (`id`),
  KEY `idx_operateur` (`operateur_id`),
  KEY `idx_statut` (`statut`),
  KEY `idx_dates` (`date_debut`,`date_fin`),
  KEY `idx_formation_operateur_dates` (`operateur_id`,`date_debut`,`date_fin`),
  CONSTRAINT `fk_formation_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
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
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `historique` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `date_time` datetime NOT NULL,
  `action` varchar(255) NOT NULL,
  `operateur_id` int(11) DEFAULT NULL,
  `poste_id` int(11) DEFAULT NULL,
  `description` text DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `operateur_id` (`operateur_id`),
  KEY `poste_id` (`poste_id`),
  CONSTRAINT `historique_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `historique_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `operateur_infos` (
  `operateur_id` int(11) NOT NULL,
  `sexe` varchar(50) DEFAULT NULL,
  `date_entree` date DEFAULT NULL,
  `nationalite` varchar(150) DEFAULT NULL,
  `cp_naissance` varchar(50) DEFAULT NULL,
  `ville_naissance` varchar(150) DEFAULT NULL,
  `pays_naissance` varchar(150) DEFAULT NULL,
  `date_naissance` date DEFAULT NULL,
  `adresse1` varchar(255) DEFAULT NULL,
  `adresse2` varchar(255) DEFAULT NULL,
  `cp_adresse` varchar(50) DEFAULT NULL,
  `ville_adresse` varchar(150) DEFAULT NULL,
  `pays_adresse` varchar(150) DEFAULT NULL,
  `telephone` varchar(100) DEFAULT NULL,
  `email` varchar(320) DEFAULT NULL,
  `nir_chiffre` varbinary(255) DEFAULT NULL,
  `nir_nonce` varbinary(16) DEFAULT NULL,
  `nir_tag` varbinary(16) DEFAULT NULL,
  `commentaire` text DEFAULT NULL,
  PRIMARY KEY (`operateur_id`),
  UNIQUE KEY `uk_operateur_infos` (`operateur_id`),
  KEY `idx_email` (`email`),
  KEY `idx_cp_adresse` (`cp_adresse`),
  KEY `idx_ville_adresse` (`ville_adresse`),
  CONSTRAINT `fk_infos_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operateur_infos`
--

LOCK TABLES `operateur_infos` WRITE;
/*!40000 ALTER TABLE `operateur_infos` DISABLE KEYS */;
INSERT INTO `operateur_infos` VALUES
(2,'M','2014-01-27','FR','64','SALIES DE BEARN','FR','1970-08-08',NULL,NULL,'64270','CARRESSE','FR','07 80 38 72 37','steph.esteban08@yahoo.com',NULL,NULL,NULL,NULL),
(3,'M','0000-00-00','GE','99','TBILISI','GE','1994-04-01','6 Rue BELA',NULL,'64130','MAULEON',NULL,'07 69 65 95 29','eduardbagdasarian798@gmail.com',NULL,NULL,NULL,NULL),
(4,'M','1991-03-06','FR','64','MAULEON','FR','1965-02-05','34 Impasse Chapar',NULL,'64130','VIODOS','FR','06 78 23 87 95','natetjm.b@orange.fr',NULL,NULL,NULL,NULL),
(5,'M','1991-03-20','FR','64','MAULEON','FR','1970-07-09','BOURG',NULL,'64470','SAUGIS','FR','07 86 40 32 53','emmanuel.bengochea@sfr.fr',NULL,NULL,NULL,NULL),
(6,'M','0000-00-00','FR','64','SAINT-PALAIS','FR','1998-02-20','3015 Route Pays de Soule',NULL,'64130','ESPES-UNDUREIN',NULL,'07 50 30 30 53','bidondo.anthony@gmail.com',NULL,NULL,NULL,NULL),
(8,'M','1991-04-12','FR','64','UHART CIZE','FR','1966-10-28','32 Impasse Sainte-Barbe',NULL,'64130','VIODOS - ABSENSE DE BAS','FR','06.19.36.04.41','bidondo.pierre@orange.fr',NULL,NULL,NULL,NULL),
(9,'M','2015-06-22','FR','64','OLORON SAINTE MARIE','FR','1992-02-03',NULL,NULL,'64130','MAULEON','FR','06 29 15 70 77','alex.b64130@hotmail.fr',NULL,NULL,NULL,NULL),
(11,'M','0000-00-00','FR','64','OLORON SAINTE MARIE','FR','1986-07-23',NULL,NULL,'64190','GURS',NULL,'06 79 96 31 04','alain.carricaburu@outlook.fr',NULL,NULL,NULL,NULL),
(12,'M','2020-07-20','FR','64','SAINT PALAIS','FR','2002-04-22','6 Chemin Deus Tourouns',NULL,'64190','RIVEHAUTE','FR','07 82 90 35 78','cazenavejean2@gmail.com',NULL,NULL,NULL,NULL),
(15,'M','2003-11-24','FR','64','SAINT PALAIS','FR','1979-06-10','3 LOT BASTERREIX',NULL,'64130','MAULEON','FR','06 73 00 22 23','d.danycos@gmail.com',NULL,NULL,NULL,NULL),
(17,'M','2019-08-19','FR','06','NICE','FR','1982-03-20','10 PLACE DU FOIRAIL',NULL,'64190','NAVARRENX','FR','06 30 03 16 07','courtiesdoryan@gmail.com',NULL,NULL,NULL,NULL),
(19,'M','0000-00-00','FR','78','SAINT-CYR-L\'ECOLE','FR','1974-01-23','27 Rue Cujas',NULL,'64400','OLORON SAINTE MARIE',NULL,NULL,'piperade64@gmail.com',NULL,NULL,NULL,NULL),
(20,'M','2019-03-12','FR','66','PERPIGNAN','FR','1981-12-16','36 Rue de BELA',NULL,'64130','MAULEON','FR',NULL,'cedricdelgado@yahoo.fr',NULL,NULL,NULL,NULL),
(21,'M','0000-00-00','FR','93','SAINT-DENIS','FR','1970-03-21','279 Rue des Trois Croix',NULL,'64130','ESPES-UNDUREIN',NULL,'07 49 77 38 35','devauxdavid64@gmail.com',NULL,NULL,NULL,NULL),
(22,'M','2021-08-16','FR','59','Marcq en baroeul','FR','1992-07-24','8 quartier CIBI',NULL,'64130','BERROGAIN- LARUNS',NULL,NULL,'dossantos.charly64@gmail.com',NULL,NULL,NULL,NULL),
(23,'M','2015-01-12','FR','64','OLORON SAINTE MARIE','FR','1982-09-21','2 Impasse DARRIGRAND',NULL,'64130','VIODOS - ABENSE DE BAS','FR','06 77 49 47 61','etcheverryfrederic.5@gmail.com',NULL,NULL,NULL,NULL),
(24,'M','0000-00-00','FR','64','Pau','FR','1996-12-09','15 Rue LABAT',NULL,'64130','MAULEON',NULL,'06 22 76 17 64','thomasfernandez64@icloud.com',NULL,NULL,NULL,NULL),
(25,'M','0000-00-00','FR','64','Saint-Palais','FR','1999-06-08','Route de Lambarre',NULL,'64130','GARINDEIN','FR','06 15 01 96 64','egonot@club-internet.fr',NULL,NULL,NULL,NULL),
(26,'M','0000-00-00','FR','64','Oloron Sainte Marie','FR','1984-09-05','Lotissement Lou Thouroun',NULL,'64130','LICHOS',NULL,'06 77 43 11 94','gouvinhasreal@live.fr',NULL,NULL,NULL,NULL),
(27,'M','1991-02-26','FR','64','MAULEON','FR','1970-12-23','MAISON LASTETXIA',NULL,'64130','MONCAYOLL','FR',NULL,'alain.guimon@orange.fr',NULL,NULL,NULL,NULL),
(32,'M','0000-00-00','FR','64','SAINT-PALAIS','FR','2002-08-26','31 Route de CAMOUREST',NULL,'64190','NABAS',NULL,'06 85 98 38 73','milage.alban@gmail.com',NULL,NULL,NULL,NULL),
(33,'F','2020-01-06','FR','64','OLORON SAINTE MARIE','FR','1980-11-23','197 Rue Errekaltia',NULL,'64130','ESPES UNDUREIN','FR','06.89.29.05.06','soniamolus80@gmail.com',NULL,NULL,NULL,NULL),
(34,'M','0000-00-00','FR','64','SAINT-PALAIS','FR','2006-11-24','15 Route de Magnoua',NULL,'64190','RIVEHAUTE',NULL,'06 26 14 50 90','xabimontois641@gmail.com',NULL,NULL,NULL,NULL),
(36,'M','2019-03-05','FR','64','MAULEON','FR','1971-10-09','4 LOT DE LA PLAINE',NULL,'64130','VIODOS ABENSE DE BAS','FR','06.82.98.58.69','maiderkattinu@hotmail.fr',NULL,NULL,NULL,NULL),
(37,'M','2020-02-03','FR','64','SAINT PALAIS','FR','1999-09-02','5 LOTISSEMENT BASTERREIX',NULL,'64130','MAULEON','FR','06 28 02 62 66','pierre.ordu64@gmail.com',NULL,NULL,NULL,NULL),
(38,'M','0000-00-00','FR','64','Oloron Sainte Marie','FR','1997-09-12','50 Impasse Chapar',NULL,'64130','VIODOS - ABENSE-DE-BAS','FR',NULL,'nico.oyhenart@gmail.com',NULL,NULL,NULL,NULL),
(39,'M','2003-07-01','FR','75','PARIS','FR','1968-08-18','68 BOULEVARD DES PYRENEES',NULL,'64130','MAULEON','FR','06.12.01.64.18','perezmaria9897@neuf.fr',NULL,NULL,NULL,NULL),
(43,'M','2021-08-16',NULL,NULL,'BELPER','EN','1971-09-25','245 RUE PRINCIPALE',NULL,'64270','BERGOUEY VILLENAVE','FR',NULL,'ricematt64@gmail.com',NULL,NULL,NULL,NULL),
(45,'M','1991-03-01','FR','64','MAULEON','FR','1967-02-07','CHATEAU DE CHERAUTE',NULL,'64130','CHERAUTE','FR','06.11.96.35.62','eric.saralegui@free.fr',NULL,NULL,NULL,NULL),
(47,'M','1991-04-10','FR','64','SAINT PALAIS','FR','1970-11-03','MAISON ARGICHENIA',NULL,'64120','AROUE','FR',NULL,'claveriesicre.helene@neuf.fr',NULL,NULL,NULL,NULL),
(48,'M','2017-06-19','FR','64','ORTHEZ','FR','1986-11-19','1 ROUTE DES PYRENEES',NULL,'64190','GESTAS','FR','06.80.22.14.58','tradere@hotmail.fr',NULL,NULL,NULL,NULL),
(49,'M','0000-00-00','FR','64','BIARRITZ','FR','1978-09-11','14 Rue Jaureguiberry',NULL,'64130','MAULEON','FR','06 48 94 99 83','unanuad@gmail.com',NULL,NULL,NULL,NULL),
(50,'M','0000-00-00','FR','64','UHART-CIZE','FR','1973-03-22',NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(51,'M','2013-08-19','FR','62','CALAIS','FR','1993-07-13',NULL,NULL,'64390','ESPIUTE','FR','06.35.40.80.38','Joffrey.Vasseur13@gmail.com',NULL,NULL,NULL,NULL),
(52,'M','2004-07-01','FR','64','SALIES DE BEARN','FR','1968-08-16','MAISON CASAMAYOU',NULL,'64190','GESTAS','FR','06.81.44.77.37','vergefamilly@gmail.com',NULL,NULL,NULL,NULL),
(99,'M','0000-00-00','FR','33','LA-TESTE-DE-BUCH','FR','2004-06-12','Maison Gaineko Borda',NULL,'64120','SAINT-JUST-IBARRE',NULL,'06 18 05 54 67','joaquimetcheverria459@gmail.com',NULL,NULL,NULL,NULL),
(114,'M','0000-00-00','FR','64','Bayonne','FR','1993-09-17',NULL,NULL,'64190','NABAS',NULL,'06 26 67 72 59','sebacedo64130@gmail.com',NULL,NULL,NULL,NULL),
(115,'F','0000-00-00','FR','67','THANN','FR','1988-02-22',NULL,NULL,'67000','STRASBOURG','FR',NULL,'fabre@internet.fr',NULL,NULL,NULL,NULL),
(116,'M','2000-10-04','FR','64','MAULEON','FR','1974-09-11',NULL,NULL,'64130','MAULEON','FR','06 19 84 05 66',NULL,NULL,NULL,NULL,NULL),
(117,'M','2019-08-19','FR','64','OLORON STE MARIE','FR','1999-08-04',NULL,NULL,'64130','MAULEON','FR','06 51 86 34 02','romainamat@hotmail.fr',NULL,NULL,NULL,NULL),
(118,'M','0000-00-00','FR','64','Oloron-Sainte-Marie','FR','1997-05-12','31 Rue des FrÃ¨res Barenne',NULL,'64130','MAULEON',NULL,'06 19 74 53 83','pierrearen@icloud.com',NULL,NULL,NULL,NULL),
(119,'M','1991-04-18','FR','64','MAULEON','FR','1967-04-23','QUARTIER GAGNECO URUPEA',NULL,'64130','ESPES UNDU','FR',NULL,NULL,NULL,NULL,NULL,NULL),
(120,'M','2003-07-01','FR','64','MAULEON LICHARRE','FR','1965-05-03','380 Route d\'Idaux',NULL,'64130','IDAUX-MENDY','FR',NULL,'jeanmariearnal@yahoo.com',NULL,NULL,NULL,NULL),
(121,'M','2019-08-28','FR','64','PAU','FR','1997-12-28','1 AVENUE JEAN MERMOZ',NULL,'64400','GOES','FR','06.01.39.30.71',NULL,NULL,NULL,NULL,NULL),
(122,'M','2012-10-08','FR','94','NOGENT SUR MARNE','FR','1971-10-14','Quartier Ukuarte Zocoua',NULL,'64130','GARINDEIN','FR','07.81.91.22.24',NULL,NULL,NULL,NULL,NULL),
(123,'F','0000-00-00','FR','03','VICHY','FR','1990-11-12','19 Rue du Bourg',NULL,'64320','IDRON','FR','0 51 87 20 23','marine.v.banquet@gmail.com',NULL,NULL,NULL,NULL),
(124,'M','2019-11-12','FR','09','Pamiers','FR','1974-01-25','42 Rue des Vignes',NULL,'64230','DENGUIN','FR','06 82 37 06 31','romainbarat4@gmail.com',NULL,NULL,NULL,NULL),
(125,'M','2011-02-01','FR','64','PAU','FR','1959-03-24','PORTE DES PYRENEES',NULL,'64400','OLORON SAINTE MARIE','FR',NULL,NULL,NULL,NULL,NULL,NULL),
(126,'F','2023-01-16','FR','64','Orthez','FR','1971-12-07','85 Route de Condou',NULL,'64370','MESPLEDE',NULL,'06 25 61 62 81','mnbergeron@yahoo.fr',NULL,NULL,NULL,NULL),
(127,'M','2001-11-26','FR','64','MOURENX','FR','1981-10-20','2158 Voie de la Soule',NULL,'64130','ESPES-UNDUREIN','FR',NULL,'bergez.laeti@icloud.com',NULL,NULL,NULL,NULL),
(128,'M','2020-01-20','FR','64','SAINT PALAIS','FR','1985-08-23','165 ROUTE DE SABRENIA',NULL,'64120','AMENDEUIX ONEIX','FR','0627538114','inakiberho@outlook.fr',NULL,NULL,NULL,NULL),
(129,'M','0000-00-00','FR','64','Saint-Palais','FR','1987-03-24','Chemin LASCORRY',NULL,'64130','VIODOS - ABENSE DE BAS',NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(130,'M','1987-11-09','FR','64','MAULEON','FR','1965-06-09',NULL,NULL,'64130','CHERAUTE','FR',NULL,'batitte@gmail.com',NULL,NULL,NULL,NULL),
(131,'F','2020-01-20','FR','37','CHAMBRAY LES TOURS','FR','1981-06-01','LE BOURG',NULL,'64130','IDAUX MENDY','FR','07.85.53.94.73','ophelie_berthe@orange.fr',NULL,NULL,NULL,NULL),
(132,'M','2016-08-16','FR','64','SAINT PALAIS','FR','1996-07-17',NULL,NULL,'64130','VIODOS - ABENSE DE BAS','FR','06 75 47 19 55','mickael6417@gmail.com',NULL,NULL,NULL,NULL),
(133,'M','2019-09-02','FR','44','SAINT NAZAIRE','FR','1999-01-05',NULL,NULL,'44560','PAIMBOEUF','FR','06.25.39.03.78','matthieu.bouldoires44@gmail.com',NULL,NULL,NULL,NULL),
(134,'M','0000-00-00','FR','64','NAVARRENX','FR','1971-12-27','6 Impasse du Tram',NULL,'64190','CASTETNAU-CAMBLONG',NULL,'06 79 16 32 98','branajeanpaul@gmail.com',NULL,NULL,NULL,NULL),
(135,'M','0000-00-00','FR','75','Paris 14Ã¨me','FR','1966-05-24','Maison Etchegoyhen',NULL,'64470','CAMOU - CIHIGUE',NULL,NULL,'jfcampane@outlook.fr',NULL,NULL,NULL,NULL),
(136,'M','0000-00-00','FR','64','Bayonne','FR','1982-07-22','Quartier MAIGHIA',NULL,'64130','CHARRITTE DE BAS',NULL,'06 70 71 26 30','lionel.campane@hotmail.fr',NULL,NULL,NULL,NULL),
(137,'M','1991-02-04','FR','64','MAULEON','FR','1960-02-15','MAISON GURE ETCHOLA',NULL,'64130','GARINDEIN','FR','06 72 10 99 11','etchola.gure@orange.fr',NULL,NULL,NULL,NULL),
(138,'M','0000-00-00','FR','64','Pau','FR','1994-12-29','8 Rue Maurice RAVEL',NULL,'64130','MAULEON',NULL,'0768593398','anthony.capuret64130@gmail.com',NULL,NULL,NULL,NULL),
(139,'M','2020-01-06','FR','75','MONTREUIL SOUS BOIS','FR','1961-06-28','550 ROUTE DE BAYONNE',NULL,'64390','GUINARTHE','FR','07 79 61 78 27','laurentcastex@sfr.fr',NULL,NULL,NULL,NULL),
(140,'F','0000-00-00','TN','99','WEDHREF','TN','1993-11-05','1 Rue Jacqueline AURIOL',NULL,'40100','DAX',NULL,'07 53 30 72 95','marwachammam@gmail.com',NULL,NULL,NULL,NULL),
(141,'M','0000-00-00','FR','38','ECHIROLLES','FR','1990-12-28','Lot. MONSEGUR',NULL,'64470','TARDETS',NULL,'06 03 30 71 14','cfpalette@gmail.com',NULL,NULL,NULL,NULL),
(142,'M','2008-09-22','FR','31','TOULOUSE','FR','1985-08-21','845 Route de Dax',NULL,'40360','POMAREZ','FR','06 82 48 58 72','maxime.aurelie40360@gmail.com',NULL,NULL,NULL,NULL),
(143,'M','2021-01-04','FR','54','Nancy','FR','1997-06-06','Route de Haux',NULL,'64470','MONTORY','FR','06 17 70 08 26','m.colas712@gmail.com',NULL,NULL,NULL,NULL),
(144,'M','2015-04-07','FR','95','GONESSE','FR','1976-06-01','5 BOULEVARD GAMBETTA',NULL,'64130','MAULEON','FR','0645017062','jeanmarie.cordani@free.fr',NULL,NULL,NULL,NULL),
(145,'M','2015-08-31','PT',NULL,'MARINHA GRANDE','PT','1969-09-03','LOT DE MENDITTE',NULL,'64130','GARINDEIN','FR',NULL,'correiadossantosgeorges@gmail.com',NULL,NULL,NULL,NULL),
(146,'M','2013-03-04','FR','64','OLORON SAINTE MARIE','FR','1977-08-06',NULL,NULL,'64400','GEUS D\'OLORON','FR','06.37.40.20.96','ericcouchinave@gmail.com',NULL,NULL,NULL,NULL),
(147,'F','2003-04-01','FR','64','MAULEON','FR','1978-03-09','MAISON ELISSALT',NULL,'64130','ARRAST LARREBIEU','FR',NULL,'thierry.couchinave@orange.fr',NULL,NULL,NULL,NULL),
(148,'M','0000-00-00','FR','64','BAYONNE','FR','1997-01-31','15 Rue de Devant',NULL,'64270','LABASTIDE-VILLEFRANCHE',NULL,NULL,'clerik.courties@gmail.com',NULL,NULL,NULL,NULL),
(149,'NSP','0000-00-00','64','FR','1994-08-06','Bayonne','2001-00-00',NULL,NULL,NULL,NULL,'LABASTIDE-VILLEFRANCHE',NULL,NULL,NULL,NULL,NULL,NULL),
(150,'F','0000-00-00','PT','99','CHAVES','PT','1978-04-30','RÃ©sidence Berges du Gave - Appart.22',NULL,'64130','MAULEON',NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(151,'M','0000-00-00','FR','64','MAULEON','FR','1975-03-17','12 QUARTIER CIBI',NULL,'64130','BERROGAIN-LARUNS',NULL,'06 24 07 38 98','sergio.dacosta@orange.fr',NULL,NULL,NULL,NULL),
(152,'M','2007-09-03','FR','64','SAINT PALAIS','FR','1979-05-05','4 ROUTE DE PEYRET',NULL,'64390','BARRAUTE-CAMU','FR','0608875387','patdag64@hotmail.fr',NULL,NULL,NULL,NULL),
(153,'M','2016-10-24','FR','64','ARAMITS','FR','1960-09-16','MAISON TOKI EDER',NULL,'64130','MAULEON','FR','06 84 26 68 32','tokiedermaule@outlook.fr',NULL,NULL,NULL,NULL),
(154,'F','2019-11-12','FR','64','Mourenx','FR','1989-08-20','95 Avenue de Rangueil',NULL,'31400','TOULOUSE','FR','06 28 43 22 63','charlotte.denecker@gmail.com',NULL,NULL,NULL,NULL),
(155,'M','0000-00-00','FR','17','Rochefort','FR','2002-06-07','Chez Mme OcÃ©ane PLANTE',NULL,'64130','Mauleon',NULL,'06 65 41 93 08','val97477@gmail.com',NULL,NULL,NULL,NULL),
(156,'M','2021-01-11','FR','77','Tournan En Brie','FR','1968-07-30','41 Rue Saint-Germain',NULL,'64190','NAVARRENX',NULL,'06 65 30 35 08','laurent.deslandes32@gmail.com',NULL,NULL,NULL,NULL),
(157,'M','0000-00-00','FR','64','Bayonne','FR','1985-01-17','85 Rue de La Navarre',NULL,'64130','MAULEON',NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(158,'F','0000-00-00','FR','67','STRASBOURG','FR','1977-03-08',NULL,NULL,'67200','STRASBOURG','FR','06 11 54 99 33','ssaunier@internet.fr',NULL,NULL,NULL,NULL),
(159,'F','2020-03-17','FR','75','PARIS 14eme','FR','1994-03-17','5 AllÃ©e du Petit Tres',NULL,'40390','SAINT MARTIN DE SEIGNANX',NULL,'06 21 13 15 35','elisa_santos1234@hotmail.com',NULL,NULL,NULL,NULL),
(160,'M','0000-00-00','FR','42','SAINT-ETIENNE','FR','1970-08-09','15 Route de Gestas',NULL,'64390','ESPIUTE',NULL,NULL,'lducham32@gmail.com',NULL,NULL,NULL,NULL),
(161,'M','2006-07-31','FR','64','MAULEON LICHARRE','FR','1961-01-28','7 BIS DE LA SOULE',NULL,'64130','CHERAUTE','FR','06.23.74.02.15',NULL,NULL,NULL,NULL,NULL),
(162,'M','0000-00-00','FR','65','Lourdes','FR','1968-05-07','5 Impasse du CastÃ©ra',NULL,'64150','MOURENX',NULL,'06 37 28 01 26','thierry64150@gmail.com',NULL,NULL,NULL,NULL),
(163,'M','0000-00-00','FR','64','Oloron Sainte Marie','FR','1996-10-14','3 Chemin LAPAGESSE',NULL,'64130','VIODOS - ABENSE DE BAS',NULL,'06 74 34 74 13','vincentdumurpro@gmail.com',NULL,NULL,NULL,NULL),
(164,'F','2020-10-01','FR','64','Oloron Sainte Marie','FR','1975-06-06','4 Route de la Soule',NULL,'64190','PRECHACQ JOSBAIG','FR','06 15 79 50 99','mumys64@yahoo.fr',NULL,NULL,NULL,NULL),
(165,'M','0000-00-00','FR','99','TAZA','MA','1973-08-23','6 Rue des Gaves',NULL,'64150','MOURENX',NULL,'07 83 11 08 25','elhamouchi64400@gmail.com',NULL,NULL,NULL,NULL),
(166,'M','2020-02-24','FR','64','SAINT PALAIS','FR','1981-05-27','35 Avenue de La GARE',NULL,'64120','SAINT PALAIS','FR',NULL,NULL,NULL,NULL,NULL,NULL),
(167,'M','0000-00-00','FR','64','Pau','FR','2000-11-15','8 Chemin Serbielle',NULL,'64190','ANGOUS',NULL,'06 84 83 55 10',NULL,NULL,NULL,NULL,NULL),
(168,'M','2015-01-12','FR','64','MAULEON LICHARRE','FR','1969-06-13','117 CHEMIN DE PARENTIES',NULL,'64390','GUINARTHE','FR','06.47.93.55.59','sergioerrecart5@gmail.com',NULL,NULL,NULL,NULL),
(169,'F','0000-00-00','FR','64','SAINT-PALAIS','FR','2002-09-23','355 Chemin MATAXOT',NULL,'64130','IDAUX-MENDY',NULL,'06 78 27 95 07','jetcheberriborde@gmail.com',NULL,NULL,NULL,NULL),
(170,'M','0000-00-00','FR','33','BORDEAUX','FR','1991-03-07','Maison Etchettoua',NULL,'64130','CHARRITTE DE BAS',NULL,'06 74 59 78 22','adrien.etcheverry.64@gmail.com',NULL,NULL,NULL,NULL),
(171,'M','0000-00-00','FR','64','Bayonne','FR','1994-09-15','115 Chemin Urbizy',NULL,'64990','MOUGUERRE',NULL,NULL,'etcheverryfabien00@gmail.com',NULL,NULL,NULL,NULL),
(172,'F','2007-01-29','FR','64','OLORON SAINTE MARIE','FR','1961-05-31',NULL,NULL,'64130','MAULEON','FR',NULL,NULL,NULL,NULL,NULL,NULL),
(173,'M','0000-00-00','FR','64','PAU','FR','1991-06-23','44 Rue Principale',NULL,'64130','VIODOS - ABSENSE DE BAS',NULL,NULL,'lindsaycallenaere@outlook.com',NULL,NULL,NULL,NULL),
(174,'F','0000-00-00','FR','27','Evreux','FR','2004-03-10','180 Rue de la Soule',NULL,'64130','CHERAUTE',NULL,'07 71 22 60 90','sabrinafretay@gmail.com',NULL,NULL,NULL,NULL),
(175,'M','2013-12-31','FR','64','OLORON SAINTE MARIE','FR','1991-06-12','3 IMPASSE DES FOSSES',NULL,'64120','SAINT PALAIS','FR','06 27 30 86 28','steeve.gauchet@gmail.com',NULL,NULL,NULL,NULL),
(176,'F','2002-11-25','FR','33','LIBOURNE','FR','1980-02-28','HAMEAU LARREBIEU',NULL,'64130','ARRAST LARREBIEU','FR',NULL,NULL,NULL,NULL,NULL,NULL),
(177,'M','0000-00-00','FR','64','ORTHEZ','FR','1965-05-27','4 Rue Labourdette',NULL,'64190','SUS',NULL,'06 83 68 08 24',NULL,NULL,NULL,NULL,NULL),
(178,'F','2017-11-20','FR','64','MAULEON','FR','1976-11-04','291 Chemin RECALDE',NULL,'64130','VIODOS - ABENSE DE BAS','FR','06 28 19 67 23','carolegerony@gmail.com',NULL,NULL,NULL,NULL),
(179,'F','2018-11-19','FR','64','OLORON SAINTE MARIE','FR','1966-01-08','16 ALLEE DES FOUGERES',NULL,'64400','AREN','FR','06 81 28 81 81','marie.claire.gesse@orange.fr',NULL,NULL,NULL,NULL),
(180,'M','2010-10-04','FR','64','OLORON SAINTE MARIE','FR','1987-07-16','28 LOTISSEMENT MENDY ALDE',NULL,'64130','MAULEON','FR',NULL,'64.godfrin@gmail.com',NULL,NULL,NULL,NULL),
(181,'M','0000-00-00','PT','99','Portugal','PT','1972-03-25','1 Av. de l\'Hippodrome',NULL,'64130','MAULEON',NULL,'07 84 24 24 81','crismerg@hotmail.com',NULL,NULL,NULL,NULL),
(182,'F','2007-03-05','FR','64','OLORON SAINTE MARIE','FR','1984-11-26',NULL,NULL,'64130','MAULEON','FR','06.86.97.80.72','carogouvert@hotmail.com',NULL,NULL,NULL,NULL),
(183,'F','1982-03-01','FR','64','IDAUX MENDY','FR','1961-05-04','AINHARP',NULL,'64130','AINHARP','FR','06 31 81 23 31',NULL,NULL,NULL,NULL,NULL),
(184,'M','0000-00-00','FR','02','Soissons','FR','2002-01-03','41 Rue des Patriotes',NULL,'02100','SAINT-QUENTIN',NULL,'0768463305','floriancordani@outlook.fr',NULL,NULL,NULL,NULL),
(185,'M','0000-00-00','FR','64','Oloron Sainte Marie','FR','1996-03-05','18 Rue des PyrÃ©nÃ©es',NULL,'64190','SUS',NULL,NULL,'alexandre-heguiabehere@laposte.net',NULL,NULL,NULL,NULL),
(186,'M','2010-09-15','FR','64','OLORON SAINTE MARIE','FR','1984-01-08','4 Bis Route de LAHITAU',NULL,'64390','BARRAUTE-CAMU','FR','06.18.91.79.14','jheugas@gmail.com',NULL,NULL,NULL,NULL),
(187,'F','0000-00-00','FR','64','SAINT-PALAIS','FR','1976-04-24','3 Rue MarÃ©chal Leclerc',NULL,'64130','MAULEON',NULL,'07 67 08 30 66','celine.idiart@orange.fr',NULL,NULL,NULL,NULL),
(188,'M','2020-01-13','FR','64','ORTHEZ','FR','1991-01-02','RESIDENCE O RUE JORGE SEMPRUN',NULL,'64150','MOURENX','FR','0614231519',NULL,NULL,NULL,NULL,NULL),
(189,'M','2017-07-24','FR','64','SAINT PALAIS','FR','1996-07-10','QUARTIER MIZ MAISON OHANTZEA',NULL,'64240','BONLOC','FR','06.20.28.49.50','loic.iturria@gmail.com',NULL,NULL,NULL,NULL),
(190,'M','0000-00-00','FR','64','MaulÃ©on','FR','1979-05-09','4 Rue d\'Iraty',NULL,'64130','MAULEON','FR','06 68 63 04 02','joel.jelassi@gmail.com',NULL,NULL,NULL,NULL),
(191,'M','2002-02-20','FR','64','MAULEON','FR','1961-03-01','LOT TARTACHU',NULL,'64130','GOTEIN LIBA FRANCE','FR','06 43 00 98 52',NULL,NULL,NULL,NULL,NULL),
(192,'M','2007-10-09','FR',NULL,'HAOUCH ARAB','SY','1961-05-25','608 Route de Saint Palais',NULL,'64130','VIODOS ABENSE DE BAS','FR','06.75.99.00.84','vandredy@hotmail.fr',NULL,NULL,NULL,NULL),
(193,'M','2015-08-24','FR','59','TOURCOING','FR','1969-10-01','Chez M. Mme DELNSSE',NULL,'59150','WATTRELOS','FR','06.81.67.81.09','chtiom59@hotmail.fr',NULL,NULL,NULL,NULL),
(194,'F','1991-12-02','FR','64','PAU','FR','1964-02-25',NULL,NULL,'64510','BORDES','FR',NULL,'pascale.lac-peyras@orange.fr',NULL,NULL,NULL,NULL),
(195,'M','2013-01-07','FR','64','SALIES DE BEARN','FR','1969-07-24','16 CITE BERGES',NULL,'64270','CARRESSE','FR','07.87.68.40.84',NULL,NULL,NULL,NULL,NULL),
(196,'M','0000-00-00','FR','64','SAINT-PALAIS','FR','2004-02-03','100 Chemin de Bixta Eder',NULL,'64120','ARBOUET-SUSSAUTE',NULL,'06 40 14 45 22','antlajourande@gmail.com',NULL,NULL,NULL,NULL),
(197,'F','2015-09-01','FR','64','MAULEON','FR','1969-10-10','9 CitÃ© Saint-Jean',NULL,'64130','MAULEON','FR','06.81.34.12.69','larraburu.pascale@neuf.fr',NULL,NULL,NULL,NULL),
(198,'M','2021-08-02','FR','64','Oloron','FR','2002-07-17','Bourg',NULL,'64130','IDAUX MENDY',NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(199,'F','2021-08-16','FR','64','BAYONNE','FR','1981-05-15','1045 Route de Saint Palais',NULL,'64130','VIODOS - ABENSE DE BAS',NULL,NULL,'marielascoumes@gmail.com',NULL,NULL,NULL,NULL),
(200,'M','0000-00-00','FR','64','Saint-Palais','FR','1988-08-20','Lotissement Les Monts',NULL,'64130','LICHOS',NULL,'06 09 96 88 37','laugafrederic64@orange.fr',NULL,NULL,NULL,NULL),
(201,'F','0000-00-00','FR','67','MARSEILLE','FR','1978-05-12',NULL,NULL,'67000','STRASBOURG','FR',NULL,'fabre@internet.fr',NULL,NULL,NULL,NULL),
(202,'M','0000-00-00','FR','89','Auxerre','FR','1990-10-16','1 Chemin de l\'Usine',NULL,'64130','VIODOS ABENSE DE BAS',NULL,'07 88 38 60 37','lepolard.baptiste@gmail.com',NULL,NULL,NULL,NULL),
(203,'NSP','0000-00-00','89','FR','1985-02-26','Auxerre','2001-00-00',NULL,NULL,NULL,NULL,'MAULEON',NULL,NULL,NULL,NULL,NULL,NULL),
(204,'M','1987-11-09','FR','64','SALIES DE BEARN','FR','1962-12-23','ARRAST LARREBIEU',NULL,'64130','ARRAST LARI','FR',NULL,'jeanbaptiste.lordon@sfr.fr',NULL,NULL,NULL,NULL),
(205,'M','0000-00-00','FR','64','OLORON-SAINTE-MARIE','FR','1976-06-01','Route de Hameau',NULL,'64130','ESPES-UNDUREIN',NULL,'06 30 89 38 54',NULL,NULL,NULL,NULL,NULL),
(206,'F','0000-00-00','FR','64','Pau','FR','1974-04-22','12 Quartier CIBI',NULL,'64130','BERROGAIN-LARUNS',NULL,'06 10 71 81 94','morelmarlene@orange.fr',NULL,NULL,NULL,NULL),
(207,'M','0000-00-00','FR','64','SAINT-PALAIS','FR','1996-10-21','300 Route de BOUILLOU',NULL,'64390','ANDREIN',NULL,'06 46 52 69 14','foluquet@gmail.com',NULL,NULL,NULL,NULL),
(208,'M','2019-03-04','FR','64','BAYONNE','FR','1995-07-28',NULL,NULL,'64130','MAULEON','FR','06.15.67.85.97',NULL,NULL,NULL,NULL,NULL),
(209,'M','0000-00-00','FR','64','BAYONNE','FR','1985-04-10','7 Route de Saint-Palais',NULL,'64130','VIODOS ABENSE DE BAS',NULL,'06 85 58 98 56','labrique40@outlook.fr',NULL,NULL,NULL,NULL),
(210,'F','2019-06-04','FR','64','PAU','FR','1995-08-03',NULL,NULL,'64400','GEUS D OLORON','FR','06.49.08.08.42',NULL,NULL,NULL,NULL,NULL),
(211,'M','0000-00-00','FR','47','AGEN','FR','1967-10-27',NULL,NULL,'64130','MAULEON',NULL,'06 17 78 49 75','arbolak@orange.fr',NULL,NULL,NULL,NULL),
(212,'M','1994-10-13','FR','64','NAVARRENX','FR','1961-05-17','2 CHEMIN DU LAVOIR',NULL,'64190','ARAUX','FR','06 33 27 73 12',NULL,NULL,NULL,NULL,NULL),
(213,'M','0000-00-00','FR','28','Chartres','FR','2001-02-04','1 Rue du FORT',NULL,'64130','MAULEON',NULL,'06 28 80 61 02','theomerciris3@gmail.com',NULL,NULL,NULL,NULL),
(214,'M','0000-00-00','FR','64','OLORON-SAINTE-MARIE','FR','2008-10-20','20 Chemin de l\'Osinbidea',NULL,'64470','TARDETS SORHOLUS',NULL,'06 46 87 18 15','bettan.michaut@gmail.com',NULL,NULL,NULL,NULL),
(215,'M','0000-00-00','FR','43','LE PUY EN VELAY','FR','1975-06-11','220 Route de Sauveterre',NULL,'64300','ORTHEZ','FR','06 16 23 82 94','andremoriat@sfr.fr',NULL,NULL,NULL,NULL),
(216,'M','0000-00-00','AR','99','CHACO','AR','2001-02-12','31 Rue des FrÃ¨res Barenne',NULL,'64130','MAULEON',NULL,NULL,NULL,NULL,NULL,NULL,NULL),
(217,'F','2016-11-07','FR','64','SAINT PALAIS','FR','1976-10-13','RD 27 NÂ°1300',NULL,'ANDREIN','64390','FR','06.11.02.61.64','j_moureu@orange.fr',NULL,NULL,NULL,NULL),
(218,'F','0000-00-00','ES','99','VILLAFRANCA','ES','1992-09-30','4 Av. Alsace-Lorraine',NULL,'64130','MAULEON','FR','06 78 61 74 66','vanessamt92@gmail.com',NULL,NULL,NULL,NULL),
(219,'M','0000-00-00','FR','67','STRASBOURG','FR','1958-09-01',NULL,NULL,'67','STRASBOURG','FR',NULL,'jnecod@wanadoo.fr',NULL,NULL,NULL,NULL),
(220,'M','2015-06-01','FR','85','FONTENAY LE COMTE','FR','1981-11-11',NULL,NULL,'64130','CHERAUTE','FR','06.60.38.38.80','alchris@cegetel.net',NULL,NULL,NULL,NULL),
(221,'M','0000-00-00','FR','64','MAULEON','FR','1978-10-24',NULL,NULL,'64130','MENDITTE',NULL,NULL,'damien.pelegrinelli@orange.fr',NULL,NULL,NULL,NULL),
(222,'M','2015-08-10','FR','88','SAINT DIE','FR','1994-02-26',NULL,NULL,'64130','VIODOS - ABENSE DE BAS','FR','06 59 16 65 24','myke-tkt@live.fr',NULL,NULL,NULL,NULL),
(223,'M','0000-00-00','FR','64','Oloron Sainte Marie','FR','1991-01-28','RN 134',NULL,'64870','ESCOUT',NULL,'06 26 49 19 77','sandrine.peyrou@neuf.fr',NULL,NULL,NULL,NULL),
(224,'M','2020-02-10','FR','64','ORTHEZ','FR','1977-01-12','Passage Raymond De Longueil',NULL,'64190','NAVARRENX','FR','06 95 38 36 79','chicopicot@gmail.com',NULL,NULL,NULL,NULL),
(225,'M','2003-11-24','FR','64','SAINT PALAIS','FR','1968-08-07','ITHORROTS OLHAIBY',NULL,'64120','ITHORROTS OLHAIBY','FR',NULL,'andre.pochelu@sfr.fr',NULL,NULL,NULL,NULL),
(226,'M','0000-00-00','FR','64','MAULEON','FR','1973-11-13','Chemin ELISSAGUE',NULL,'64130','CHARRITTE DE BAS',NULL,'06 38 43 81 46','jeanlouispoissonnet@orange.fr',NULL,NULL,NULL,NULL),
(227,'NSP','2000-00-00','FR','Bayonne','1','1997-10-18','1982-00-00','FR',NULL,'SAINT-JEAN-PIED-DE PORT',NULL,NULL,'64008',NULL,NULL,NULL,NULL,NULL),
(228,'M','0000-00-00','CF','99','BANGUI','CF','1986-07-21','48 Rue Mendi Alde',NULL,'64130','MAULEON','FR','06 71 55 07 38','epoutou@yahoo.com',NULL,NULL,NULL,NULL),
(229,'M','2021-01-04','FR','54','Nancy','FR','1997-06-06','17 Rue des MIMOSAS',NULL,'64230','LESCAR','FR','06 88 64 18 68','rabineau.nicolas55@gmail.com',NULL,NULL,NULL,NULL),
(230,'M','0000-00-00','FR','64','OLORON SAINTE MARIE','FR','1982-09-02','7 Chemin du Bois',NULL,'64400','SAINT-GOIN',NULL,'06 76 80 08 63','ludovic.ramonteu@gmail.com',NULL,NULL,NULL,NULL),
(231,'NSP','0000-00-00','33','FR','1996-09-01','BORDEAUX','2001-00-00',NULL,NULL,'FR',NULL,'PAU',NULL,NULL,NULL,NULL,NULL,NULL),
(232,'M','2004-11-01','FR','64','OLORON SAINTE MARTE','FR','1981-10-06','MONTORY',NULL,'64470','MONTORY','FR','06.71.92.43.20','herve.recalt@wanadoo.fr',NULL,NULL,NULL,NULL),
(233,'M','1994-10-26','FR','64','MAULEON','FR','1973-03-18','QUARTIER ARROQUAIN ALTIA',NULL,'64130','GARINDEIN','FR',NULL,'nanirecalt@hotmail.fr',NULL,NULL,NULL,NULL),
(234,'M','2000-02-23','FR','64','MAULEON','FR','1967-10-18','70 BOULEVARD DES PYRENEES',NULL,'64130','MAULEON','FR','06.77.54.43.29','reina.frederic64@gmail.com',NULL,NULL,NULL,NULL),
(235,'M','0000-00-00','FR','64','Saint-Palais','FR','1991-04-04','Appartement 1',NULL,'64130','MAULEON',NULL,'06 31 82 03 80','flairssfmr@hotmail.fr',NULL,NULL,NULL,NULL),
(236,'F','0000-00-00','FR','31','TOULOUSE','FR','1983-04-22','Impasse les Berges du Joos',NULL,'64400','SAINT-GOIN','FR','07 81 08 00 35','isathiery@outlook.fr',NULL,NULL,NULL,NULL),
(237,'M','0000-00-00','FR','67','HAGUENAU','FR','1982-06-12',NULL,NULL,'67','STRASBOURG','FR',NULL,'rocx@expert.fr',NULL,NULL,NULL,NULL),
(238,'F','0000-00-00','FR','67','BESANCON','FR','1988-02-22',NULL,NULL,'67000','STRASBOURG','FR',NULL,'fabre@internet.fr',NULL,NULL,NULL,NULL),
(239,'M','0000-00-00','FR','95','GONESSE','FR','1991-01-15','5 Route de La Plaine',NULL,'64190','ARAUX',NULL,NULL,'tisabelle33@outllok.fr',NULL,NULL,NULL,NULL),
(240,'M','1991-02-23','FR','64','MAULEON','FR','1969-05-09','56 Chemin Aizagerrea',NULL,'64130','CHERAUTE','FR','07.81.34.73.86','jmmaga@hotmail.fr',NULL,NULL,NULL,NULL),
(241,'M','0000-00-00','FR','64','SAINT-PALAIS','FR','1971-05-07','211 Chemin Lajussa',NULL,'64390','BURGARONNE','FR','06 82 09 51 78','frederic.sallette@wanadoo.fr',NULL,NULL,NULL,NULL),
(242,'M','0000-00-00','FR','35','FougÃ¨res','FR','2003-01-01','28 Route de La Plaine',NULL,'64190','PRECHACQ-NAVARRENX',NULL,'06 52 04 23 94','quentin.salmon15@gmail.com',NULL,NULL,NULL,NULL),
(243,'F','2019-11-12','FR','09','FOIX','FR','1995-10-26','Quartier Urcuray',NULL,'64240','HASPARREN','FR','07 87 69 26 37','manonsarda@hotmail.com',NULL,NULL,NULL,NULL),
(244,'F','0000-00-00','FR','67','STRASBOURG','FR','1977-03-08',NULL,NULL,'67200','STRASBOURG','FR','06 13 54 92 31','ssaunier@internet.fr',NULL,NULL,NULL,NULL),
(245,'F','0000-00-00','FR','64','OLORON-SAINTE-MARIE','FR','2004-05-11','7 Chemin de BÃ©rÃ©renx',NULL,'64190','NAVARRENX',NULL,'07 83 08/ 24 18','amaia.sauve@gmail.com',NULL,NULL,NULL,NULL),
(246,'M','2019-08-05','FR','44','NANTES','FR','1991-09-27','RUE LES BERGES DU JOOS',NULL,'64400','SAINT GOIN','FR',NULL,NULL,NULL,NULL,NULL,NULL),
(247,'M','0000-00-00','FR','64','Saint-Palais','FR','1999-09-02','3 Lot. CHOY',NULL,'64270','TROIS-VILLES','FR','06 84 75 75 95','servantmikael340@gmail.com',NULL,NULL,NULL,NULL),
(248,'M','2013-08-19','FR','31','TOULOUSE','FR','1992-08-17',NULL,NULL,'64130','MAULEON','FR','06.52.15.22.38',NULL,NULL,NULL,NULL,NULL),
(249,'F','2012-01-02','FR','31','TOULOUSE','FR','1977-02-23','2 CitÃ© Louis BEGUERIE',NULL,'64130','MAULEON','FR','06.66.93.89.57','verosoub@yahoo.fr',NULL,NULL,NULL,NULL),
(250,'M','2014-01-06','FR','34','LODEVE','FR','1977-10-18','201 ALLEE D HARIA',NULL,'64240','BRISCOUS','FR','06.95.75.19.88','cyrilsublime@yahoo.fr',NULL,NULL,NULL,NULL),
(251,'M','2000-04-03','FR','78','LISLE ADAM','FR','1963-08-15','7 CHEMIN DES FOSSES',NULL,'64270','BELLOCQ','FR',NULL,'rivegauche@sfr.fr',NULL,NULL,NULL,NULL),
(252,'M','0000-00-00','FR','64','Oloron Sainte Marie','FR','1995-10-26','15 Rue du Lavoir',NULL,'64190','RIVEHAUTE',NULL,NULL,'rivehautien@gmail.com',NULL,NULL,NULL,NULL),
(253,'M','0000-00-00','FR','40','DAX','FR','1981-10-24','41 Chemin d\'Etxegoihenea',NULL,'64470','CAMOU-CIHIGUE','FR','06 33 71 82 67','thieryadrien24@gmail.com',NULL,NULL,NULL,NULL),
(254,'M','2017-10-30','FR','64','SAINT PALAIS','FR','1999-03-09','Maison Lascroudzades',NULL,'64270','Labastide Villefranche','FR','06.87.77.51.14',NULL,NULL,NULL,NULL,NULL);
/*!40000 ALTER TABLE `operateur_infos` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `operateurs`
--

DROP TABLE IF EXISTS `operateurs`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!40101 SET character_set_client = utf8mb4 */;
CREATE TABLE `operateurs` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `nom` varchar(255) DEFAULT NULL,
  `prenom` varchar(255) DEFAULT NULL,
  `statut` varchar(255) DEFAULT NULL,
  `matricule` varchar(20) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_matricule` (`matricule`)
) ENGINE=InnoDB AUTO_INCREMENT=370 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `operateurs`
--

LOCK TABLES `operateurs` WRITE;
/*!40000 ALTER TABLE `operateurs` DISABLE KEYS */;
INSERT INTO `operateurs` VALUES
(1,'ACEDO','Sebastien','INACTIF','M000001'),
(2,'AGUERRE','Stéphane','ACTIF','M000002'),
(3,'BAGDASARIANI','Eduardi','ACTIF','M000003'),
(4,'BEHEREGARAY','Jean Michel','INACTIF','M000004'),
(5,'BENGOCHEA','Emmanuel','ACTIF','M000005'),
(6,'BIDONDO','Anthony','ACTIF','M000006'),
(7,'BIDONDO','Michael','ACTIF','M000007'),
(8,'BIDONDO','Pierre','ACTIF','M000008'),
(9,'BRANKAER','Alexandre','ACTIF','M000009'),
(10,'CAMPANE','Jean François','ACTIF','M000010'),
(11,'CARRICABURU','Alain','ACTIF','M000011'),
(12,'CAZENAVE','Jean','ACTIF','M000012'),
(13,'CORDANI','Jean Marie','ACTIF','M000013'),
(14,'CORREIA DOS SANTOS','Jorg','ACTIF','M000014'),
(15,'COSTA','Daniel','ACTIF','M000015'),
(16,'COUCHINAVE','Eric','ACTIF','M000016'),
(17,'COURTIES','Doryan','ACTIF','M000017'),
(18,'DA COSTA','Sergio','ACTIF','M000018'),
(19,'DAVIES','Edouard','INACTIF','M000019'),
(20,'DELGADO','Cedric','ACTIF','M000020'),
(21,'DEVAUX','David','INACTIF','M000021'),
(22,'DOS SANTOS','Charly','ACTIF','M000022'),
(23,'ETCHEVERRY','Frédéric','ACTIF','M000023'),
(24,'FERNANDEZ','Thomas','ACTIF','M000024'),
(25,'GONOT','Damien','ACTIF','M000025'),
(26,'GOUVINHAS','Alexandre','ACTIF','M000026'),
(27,'GUIMON','Alain','ACTIF','M000027'),
(28,'LUQUET','François','ACTIF','M000028'),
(29,'MARCADIEU','Cedric','ACTIF','M000029'),
(30,'MARTA','Frédéric','ACTIF','M000030'),
(31,'MERCIRIS','Theo','INACTIF','M000031'),
(32,'MILAGE','Alban','ACTIF','M000032'),
(33,'MOLUS','Sonia','ACTIF','M000033'),
(34,'MONTOIS','Xabi','ACTIF','M000034'),
(35,'MORIAT','Andre','INACTIF','M000035'),
(36,'MOUSTROUS','Herve','ACTIF','M000036'),
(37,'ORDUNA','Pierre','ACTIF','M000037'),
(38,'OYHENART','Nicolas','ACTIF','M000038'),
(39,'PEREZ','Xavier','ACTIF','M000039'),
(40,'POCHELU','André Maurice','ACTIF','M000040'),
(41,'POISSONNET','Jean Louis','ACTIF','M000041'),
(42,'POUTOU','Eldon Tresor','ACTIF','M000042'),
(43,'RICE','Matthew','ACTIF','M000043'),
(44,'SALLETTE','Frédéric','ACTIF','M000044'),
(45,'SARALEGUI','Eric','ACTIF','M000045'),
(46,'SERVANT','Mikaël','ACTIF','M000046'),
(47,'SICRE','Pierre','ACTIF','M000047'),
(48,'TRADERE','Jonathan','ACTIF','M000048'),
(49,'UNANUA','Dominique','ACTIF','M000049'),
(50,'URRUTIA','Laurent','ACTIF','M000050'),
(51,'VASSEUR','Joffrey','ACTIF','M000051'),
(52,'VERGE','Olivier','ACTIF','M000052'),
(76,'VARIN','Fabien','ACTIF','M000076'),
(99,'ETCHEVERRIA','Joaquim','ACTIF','M000099'),
(100,'LAURENT','Alain','ACTIF','M000100'),
(114,'ACEDO','SÃ©bastien','ACTIF','M000114'),
(115,'ALIADIERE','Pauline','ACTIF','M000115'),
(116,'ALTHABE','MICHEL','ACTIF','M000116'),
(117,'AMAT','ROMAIN','ACTIF','M000117'),
(118,'AREN','Pierre','ACTIF','M000118'),
(119,'ARHANCETEBEHERE','DIDIER','ACTIF','M000119'),
(120,'ARNAL','JEAN MARIE','ACTIF','M000120'),
(121,'ARROUGE','THOMAS','ACTIF','M000121'),
(122,'BAILLY','XAVIER','ACTIF','M000122'),
(123,'BANQUET','Marine','ACTIF','M000123'),
(124,'BARAT','Romain','ACTIF','M000124'),
(125,'BERCAITS','FRANCOIS','ACTIF','M000125'),
(126,'BERGERON','Marie-NoÃ«le','ACTIF','M000126'),
(127,'BERGEZ','FRANCK','ACTIF','M000127'),
(128,'BERHO','INAKI','ACTIF','M000128'),
(129,'BERRETEROT','Julien','ACTIF','M000129'),
(130,'BERROGAIN','JEAN BAPTISTE','ACTIF','M000130'),
(131,'BERTHE','OPHELIE','ACTIF','M000131'),
(132,'BIDONDO','MICKAEL','ACTIF','M000132'),
(133,'BOULDOIRES','MATHIEU','ACTIF','M000133'),
(134,'BRANA','Jean-Paul','ACTIF','M000134'),
(135,'CAMPANE','Jean-FranÃ§ois','ACTIF','M000135'),
(136,'CAMPANE','Lionel','ACTIF','M000136'),
(137,'CAMY','ALAIN','ACTIF','M000137'),
(138,'CAPURET','Anthony','ACTIF','M000138'),
(139,'CASTEX','LAURENT','ACTIF','M000139'),
(140,'CHAMMAM','Marwa','ACTIF','M000140'),
(141,'CHARDIN','KÃ©vin','ACTIF','M000141'),
(142,'CHARMAN','MAXIME','ACTIF','M000142'),
(143,'COLAS','Martin','ACTIF','M000143'),
(144,'CORDANI','JEANMARIE','ACTIF','M000144'),
(145,'CORREIA DOS SANTOS','JORGE','ACTIF','M000145'),
(146,'COUCHINIAV','ERIC','ACTIF','M000146'),
(147,'COUCHINIAV','SONIA','ACTIF','M000147'),
(148,'COURTIES','ClÃ©rik','ACTIF','M000148'),
(149,'COURTIES','Marc','ACTIF','M000149'),
(150,'DA COSTA SILVA','Sonia','ACTIF','M000150'),
(151,'DA COSTA-RAMOS','Sergio','ACTIF','M000151'),
(152,'DAGUERRE','PATRICK','ACTIF','M000152'),
(153,'DAUBAS','GEORGES','ACTIF','M000153'),
(154,'DENECKER','Charlotte','ACTIF','M000154'),
(155,'DENNEMONT','Valentin','ACTIF','M000155'),
(156,'DESLANDES','Laurent','ACTIF','M000156'),
(157,'DEVERITE','Jonathan','ACTIF','M000157'),
(158,'DIPAQUE','BÃ©ti','ACTIF','M000158'),
(159,'DOS SANTOS','Elisa','ACTIF','M000159'),
(160,'DUCHAMP','Lionel','ACTIF','M000160'),
(161,'DUHALDE','PIERRE','ACTIF','M000161'),
(162,'DUMOLLARD','Thierry','ACTIF','M000162'),
(163,'DUMUR-LOURTEAU','Vincent','ACTIF','M000163'),
(164,'DUTTER','Muriel','ACTIF','M000164'),
(165,'EL HAMOUCHI','Mohamed','ACTIF','M000165'),
(166,'EPELVA','FranÃ§ois','ACTIF','M000166'),
(167,'ERBIN','Julien','ACTIF','M000167'),
(168,'ERRECART','SERGE','ACTIF','M000168'),
(169,'ETCHEBERRIBORDE','Julie','ACTIF','M000169'),
(170,'ETCHEVERRY','Adrien','ACTIF','M000170'),
(171,'ETCHEVERRY','Fabien','ACTIF','M000171'),
(172,'FERNANDES','MARIE','ACTIF','M000172'),
(173,'FERNANDEZ','Yohan','ACTIF','M000173'),
(174,'FRETAY','Sabrina','ACTIF','M000174'),
(175,'GAUCHET','STEVE','ACTIF','M000175'),
(176,'GAUDIN','ALEXANDRA','ACTIF','M000176'),
(177,'GELARD','Alain','ACTIF','M000177'),
(178,'GERONY','CAROLE','ACTIF','M000178'),
(179,'GESSE','MARIE CLAIRE','ACTIF','M000179'),
(180,'GODFRIN','DAVID','ACTIF','M000180'),
(181,'GONZALEZ MERG','Paulo Cristiano','ACTIF','M000181'),
(182,'GOUVERT','CAROLINE','ACTIF','M000182'),
(183,'GUIRESSE','BRIGITTE','ACTIF','M000183'),
(184,'HAVY','Floriant','ACTIF','M000184'),
(185,'HEGUIABEHERE','Alexandre','ACTIF','M000185'),
(186,'HEUGAS','JEREMY','ACTIF','M000186'),
(187,'IDIART','CÃ©line','ACTIF','M000187'),
(188,'IGLESIAS','LUDOVIC','ACTIF','M000188'),
(189,'ITURRIA','LOIC','ACTIF','M000189'),
(190,'JELASSI','JoÃ«l-Jean','ACTIF','M000190'),
(191,'JIMENEZ','ANDRE','ACTIF','M000191'),
(192,'JOUMAH','HASSAN','ACTIF','M000192'),
(193,'KERN','BERNARD','ACTIF','M000193'),
(194,'LAC PEYRAS','PASCALE','ACTIF','M000194'),
(195,'LAGOURGUE','DIDIER','ACTIF','M000195'),
(196,'LAJOURNADE','Antoine','ACTIF','M000196'),
(197,'LARRABURU','PASCALE','ACTIF','M000197'),
(198,'LARROQUE','GUILLAUME','ACTIF','M000198'),
(199,'LASCOUMES','MARIE','ACTIF','M000199'),
(200,'LAUGA','FrÃ©dÃ©ric','ACTIF','M000200'),
(201,'LEGRAND','Juliette','ACTIF','M000201'),
(202,'LEPOLARD','Baptiste','ACTIF','M000202'),
(203,'LEPOLARD','Michel','ACTIF','M000203'),
(204,'LORDON','JEANBAPTISTE','ACTIF','M000204'),
(205,'LOUREIRO','Michel','ACTIF','M000205'),
(206,'LOUSTALOT','MarlÃ¨ne','ACTIF','M000206'),
(207,'LUQUET','FranÃ§ois','ACTIF','M000207'),
(208,'MAFFRAND','ALEXIS','ACTIF','M000208'),
(209,'MARCADIEU','CÃ©dric','ACTIF','M000209'),
(210,'MARQUES','PAULINE','ACTIF','M000210'),
(211,'MARTA','FrÃ©dÃ©ric','ACTIF','M000211'),
(212,'MENDRIBIL','ALAIN','ACTIF','M000212'),
(213,'MERCIRIS','ThÃ©o','ACTIF','M000213'),
(214,'MICHAUT','Bettan','ACTIF','M000214'),
(215,'MORIAT','AndrÃ©','ACTIF','M000215'),
(216,'MOSQUEDA','Martin','ACTIF','M000216'),
(217,'MOUREU','MARIE LAURE','ACTIF','M000217'),
(218,'MUNOZ TERES','Vanessa','ACTIF','M000218'),
(219,'NECOUD','Jules','ACTIF','M000219'),
(220,'OLIVIER','ALBAN','ACTIF','M000220'),
(221,'PELEGRINELLI','Damien','ACTIF','M000221'),
(222,'PERARO','MICKAEL','ACTIF','M000222'),
(223,'PEYROU','Maxime','ACTIF','M000223'),
(224,'PICOT','FREDERIC','ACTIF','M000224'),
(225,'POCHELU','ANDRE','ACTIF','M000225'),
(226,'POISSONNET','Jean-Louis','ACTIF','M000226'),
(227,'POLI','Saint','ACTIF','M000227'),
(228,'POUTOU','Eldon','ACTIF','M000228'),
(229,'RABINEAU','Nicolas','ACTIF','M000229'),
(230,'RAMONTEU-CHIROS','Ludovic','ACTIF','M000230'),
(231,'REBIERE','Romain','ACTIF','M000231'),
(232,'RECALT','HERVE','ACTIF','M000232'),
(233,'RECALT','JEAN PAUL','ACTIF','M000233'),
(234,'REINA','FREDERIC','ACTIF','M000234'),
(235,'REMON','Florian','ACTIF','M000235'),
(236,'REVIDIEGO','Isabelle','ACTIF','M000236'),
(237,'ROC','Xavier','ACTIF','M000237'),
(238,'RODRIGES','Marie','ACTIF','M000238'),
(239,'SAIZ FERNANDEZ','KÃ©vin','ACTIF','M000239'),
(240,'SALLABERRY','JEAN MICHEL','ACTIF','M000240'),
(241,'SALLETTE','FrÃ©dÃ©ric','ACTIF','M000241'),
(242,'SALMON','Quentin','ACTIF','M000242'),
(243,'SARDA','MANON','ACTIF','M000243'),
(244,'SAUNIER','Sylvie','ACTIF','M000244'),
(245,'SAUVE','AmaÃ¯a','ACTIF','M000245'),
(246,'SEBILO','ALLAN','ACTIF','M000246'),
(247,'SERVANT','MikaÃ«l','ACTIF','M000247'),
(248,'SIMON','THOMAS','ACTIF','M000248'),
(249,'SOUBIRAN','VERONIQUE','ACTIF','M000249'),
(250,'SUBLIME','CYRIL','ACTIF','M000250'),
(251,'TARDY','JEAN MARIE','ACTIF','M000251'),
(252,'TARDY','Maxime','ACTIF','M000252'),
(253,'THIERY','Adrien','ACTIF','M000253'),
(254,'VERGE','REMY','ACTIF','M000254'),
(369,'LAHIRIGOYEN','Thomas','INACTIF','M000255');
/*!40000 ALTER TABLE `operateurs` ENABLE KEYS */;
UNLOCK TABLES;
/*!50003 SET @saved_cs_client      = @@character_set_client */ ;
/*!50003 SET @saved_cs_results     = @@character_set_results */ ;
/*!50003 SET @saved_col_connection = @@collation_connection */ ;
/*!50003 SET character_set_client  = utf8mb4 */ ;
/*!50003 SET character_set_results = utf8mb4 */ ;
/*!50003 SET collation_connection  = utf8mb4_general_ci */ ;
/*!50003 SET @saved_sql_mode       = @@sql_mode */ ;
/*!50003 SET sql_mode              = 'STRICT_TRANS_TABLES,ERROR_FOR_DIVISION_BY_ZERO,NO_AUTO_CREATE_USER,NO_ENGINE_SUBSTITUTION' */ ;
DELIMITER ;;
/*!50003 CREATE*/ /*!50017 DEFINER=`root`@`localhost`*/ /*!50003 TRIGGER tr_operateurs_matricule
BEFORE INSERT ON operateurs
FOR EACH ROW
BEGIN
  DECLARE next_id INT;
  SELECT IFNULL(MAX(id), 0) + 1 INTO next_id FROM operateurs;
  SET NEW.matricule = CONCAT('M', LPAD(next_id, 6, '0'));
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
  CONSTRAINT `polyvalence_ibfk_1` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE,
  CONSTRAINT `polyvalence_ibfk_2` FOREIGN KEY (`poste_id`) REFERENCES `postes` (`id`) ON DELETE CASCADE,
  CONSTRAINT `polyvalence_chk_1` CHECK (`niveau` between 1 and 4)
) ENGINE=InnoDB AUTO_INCREMENT=18315 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `polyvalence`
--

LOCK TABLES `polyvalence` WRITE;
/*!40000 ALTER TABLE `polyvalence` DISABLE KEYS */;
INSERT INTO `polyvalence` VALUES
(17439,1,5,3,'2024-06-17','2034-06-15'),
(17440,1,31,3,'2023-09-29','2033-09-26'),
(17441,2,5,3,'2022-10-18','2032-10-15'),
(17442,2,8,3,'2020-11-02','2030-10-31'),
(17443,2,11,3,'2021-09-29','2031-09-29'),
(17444,2,13,3,'2021-09-29','2031-09-29'),
(17445,2,19,3,'2020-11-02','2030-10-31'),
(17446,2,20,3,'2021-09-29','2031-09-29'),
(17447,2,21,3,'2021-09-29','2031-09-29'),
(17448,2,32,3,'2020-11-02','2030-10-31'),
(17449,3,2,3,'2024-09-27','2034-09-25'),
(17450,3,5,3,'2024-09-27','2034-09-25'),
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
(17468,7,2,4,'2020-11-02','2030-10-31'),
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
(17502,8,30,4,'2019-10-15','2025-11-28'),
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
(17951,49,28,3,'2025-10-15','2025-11-14'),
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
(18271,76,31,2,'2025-09-16','2025-10-16'),
(18284,12,77,4,'2025-04-07','2035-04-09'),
(18289,99,5,3,'2025-10-15','2025-11-14'),
(18290,99,32,3,'2025-10-15','2025-11-14'),
(18291,100,32,1,'2025-10-15','2025-11-14'),
(18293,2,28,3,NULL,'2025-11-19'),
(18299,15,77,4,NULL,'2025-11-27'),
(18300,16,77,3,NULL,'2025-11-27'),
(18301,20,77,3,NULL,'2025-11-27'),
(18302,28,77,4,NULL,'2025-11-27'),
(18303,28,7,4,NULL,'2025-11-27'),
(18304,34,7,3,NULL,'2025-11-27'),
(18305,34,77,3,NULL,'2025-11-27'),
(18306,44,77,3,NULL,'2025-11-27'),
(18307,47,77,4,NULL,'2025-11-27'),
(18308,16,7,3,NULL,'2025-11-27'),
(18309,20,7,3,NULL,'2025-11-27'),
(18310,32,25,3,NULL,'2025-11-27'),
(18311,44,7,3,NULL,'2025-11-27'),
(18312,51,3,4,NULL,'2025-11-27'),
(18313,8,30,3,NULL,'2025-11-28'),
(18314,8,30,4,NULL,'2025-11-28');
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
  CONSTRAINT `fk_atelier` FOREIGN KEY (`atelier_id`) REFERENCES `atelier` (`id`) ON DELETE SET NULL
) ENGINE=InnoDB AUTO_INCREMENT=82 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;
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
(24,'1026',1,1,10),
(25,'1100',1,1,11),
(26,'1101',1,1,11),
(27,'1103',1,1,11),
(28,'1121',2,1,11),
(29,'1401',3,1,14),
(30,'1402',3,1,14),
(31,'1404',3,1,14),
(32,'1406',3,1,NULL),
(33,'1412',3,1,14),
(77,'0561',2,1,NULL);
/*!40000 ALTER TABLE `postes` ENABLE KEYS */;
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
-- Temporary table structure for view `v_operateurs_complet`
--

DROP TABLE IF EXISTS `v_operateurs_complet`;
/*!50001 DROP VIEW IF EXISTS `v_operateurs_complet`*/;
SET @saved_cs_client     = @@character_set_client;
SET character_set_client = utf8mb4;
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
  1 AS `etp` */;
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
  CONSTRAINT `fk_validite_operateur` FOREIGN KEY (`operateur_id`) REFERENCES `operateurs` (`id`) ON DELETE CASCADE
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
/*!50001 VIEW `v_operateurs_complet` AS select `o`.`id` AS `id`,`o`.`matricule` AS `matricule`,`o`.`nom` AS `nom`,`o`.`prenom` AS `prenom`,`o`.`statut` AS `statut`,`oi`.`sexe` AS `sexe`,`oi`.`date_naissance` AS `date_naissance`,timestampdiff(YEAR,`oi`.`date_naissance`,curdate()) AS `age`,case when timestampdiff(YEAR,`oi`.`date_naissance`,curdate()) <= 25 then '0-25 ans' when timestampdiff(YEAR,`oi`.`date_naissance`,curdate()) <= 45 then '26-45 ans' when timestampdiff(YEAR,`oi`.`date_naissance`,curdate()) <= 54 then '46-54 ans' else '55 ans et +' end AS `tranche_age`,`oi`.`date_entree` AS `date_entree`,`oi`.`email` AS `email`,`oi`.`telephone` AS `telephone`,`c`.`type_contrat` AS `contrat_actuel`,`c`.`categorie` AS `categorie`,`c`.`etp` AS `etp` from ((`operateurs` `o` left join `operateur_infos` `oi` on(`o`.`id` = `oi`.`operateur_id`)) left join `contrat` `c` on(`o`.`id` = `c`.`operateur_id` and `c`.`actif` = 1)) */;
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

-- Dump completed on 2025-11-12  8:45:35
