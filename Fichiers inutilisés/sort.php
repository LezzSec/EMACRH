<?php
// Configuration de la base de données
$host = 'localhost';
$dbname = 'emac_db';
$username = 'root';
$password = '';

try {
    $pdo = new PDO("mysql:host=$host;dbname=$dbname;charset=utf8mb4", $username, $password);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
} catch(PDOException $e) {
    die("Erreur de connexion : " . $e->getMessage());
}

// Traitement de la suppression
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['delete_id'])) {
    $delete_id = (int)$_POST['delete_id'];
    
    try {
        $pdo->beginTransaction();
        
        // Supprimer l'enregistrement (les polyvalences seront supprimées automatiquement grâce à ON DELETE CASCADE)
        $stmt = $pdo->prepare("DELETE FROM personnel WHERE id = ?");
        $stmt->execute([$delete_id]);
        
        $pdo->commit();
        $message = "Personnel ID $delete_id supprimé avec succès !";
        $message_type = "success";
    } catch(PDOException $e) {
        $pdo->rollBack();
        $message = "Erreur lors de la suppression : " . $e->getMessage();
        $message_type = "error";
    }
}

// Rechercher les doublons (même nom ET même prénom)
$query = "
    SELECT 
        p.id,
        p.nom,
        p.prenom,
        p.statut,
        p.matricule,
        p.numposte,
        s.nom_service,
        COUNT(poly.id) as nb_polyvalences,
        GROUP_CONCAT(
            CONCAT(pos.poste_code, ' (Niveau ', poly.niveau, ')')
            ORDER BY pos.poste_code
            SEPARATOR ', '
        ) as liste_polyvalences
    FROM personnel p
    LEFT JOIN services s ON p.service_id = s.id
    LEFT JOIN polyvalence poly ON p.id = poly.operateur_id
    LEFT JOIN postes pos ON poly.poste_id = pos.id
    WHERE EXISTS (
        SELECT 1 
        FROM personnel p2 
        WHERE p2.nom = p.nom 
        AND p2.prenom = p.prenom 
        AND p2.id != p.id
    )
    GROUP BY p.id, p.nom, p.prenom, p.statut, p.matricule, p.numposte, s.nom_service
    ORDER BY p.nom, p.prenom, p.id
";

$doublons = $pdo->query($query)->fetchAll(PDO::FETCH_ASSOC);

// Grouper les doublons par nom/prénom
$groupes_doublons = [];
foreach ($doublons as $doublon) {
    $key = strtoupper(trim($doublon['nom'])) . '|' . strtoupper(trim($doublon['prenom']));
    $groupes_doublons[$key][] = $doublon;
}
?>

<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Gestionnaire de Doublons - Personnel</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            padding: 30px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 2em;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 1.1em;
        }
        
        .message {
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            font-weight: 500;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        
        .stats {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            display: flex;
            gap: 30px;
            flex-wrap: wrap;
        }
        
        .stat-item {
            flex: 1;
            min-width: 200px;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        
        .doublon-group {
            background: #fff;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            margin-bottom: 25px;
            overflow: hidden;
        }
        
        .group-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            font-weight: 600;
            font-size: 1.2em;
        }
        
        .person-card {
            padding: 20px;
            border-bottom: 1px solid #e0e0e0;
            transition: background 0.3s;
        }
        
        .person-card:last-child {
            border-bottom: none;
        }
        
        .person-card:hover {
            background: #f8f9fa;
        }
        
        .person-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .person-info {
            flex: 1;
        }
        
        .person-id {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }
        
        .person-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 15px;
        }
        
        .detail-item {
            display: flex;
            flex-direction: column;
        }
        
        .detail-label {
            font-size: 0.85em;
            color: #666;
            margin-bottom: 3px;
        }
        
        .detail-value {
            font-weight: 500;
            color: #333;
        }
        
        .badge {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .badge.actif {
            background: #d4edda;
            color: #155724;
        }
        
        .badge.inactif {
            background: #f8d7da;
            color: #721c24;
        }
        
        .badge.count {
            background: #667eea;
            color: white;
        }
        
        .polyvalences {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            margin-top: 10px;
        }
        
        .polyvalences-title {
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .polyvalences-list {
            color: #555;
            line-height: 1.6;
            font-size: 0.95em;
        }
        
        .no-data {
            color: #999;
            font-style: italic;
        }
        
        .btn {
            padding: 10px 20px;
            border: none;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 1em;
        }
        
        .btn-delete {
            background: #dc3545;
            color: white;
        }
        
        .btn-delete:hover {
            background: #c82333;
            transform: translateY(-2px);
            box-shadow: 0 5px 15px rgba(220, 53, 69, 0.3);
        }
        
        .btn-delete:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .delete-form {
            display: inline;
        }
        
        .warning-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            color: #856404;
        }
        
        .warning-box strong {
            display: block;
            margin-bottom: 5px;
        }
        
        .no-doublons {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        
        .no-doublons-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            .person-details {
                grid-template-columns: 1fr;
            }
            
            .stats {
                flex-direction: column;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🔍 Gestionnaire de Doublons</h1>
        <p class="subtitle">Identifiez et gérez les entrées en double dans le personnel</p>
        
        <?php if (isset($message)): ?>
            <div class="message <?php echo $message_type; ?>">
                <?php echo htmlspecialchars($message); ?>
            </div>
        <?php endif; ?>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-label">Groupes de doublons</div>
                <div class="stat-value"><?php echo count($groupes_doublons); ?></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">Entrées en double</div>
                <div class="stat-value"><?php echo count($doublons); ?></div>
            </div>
            <div class="stat-item">
                <div class="stat-label">À nettoyer</div>
                <div class="stat-value"><?php echo count($doublons) - count($groupes_doublons); ?></div>
            </div>
        </div>
        
        <?php if (empty($groupes_doublons)): ?>
            <div class="no-doublons">
                <div class="no-doublons-icon">✅</div>
                <h2>Aucun doublon détecté</h2>
                <p>Votre base de données est propre !</p>
            </div>
        <?php else: ?>
            <div class="warning-box">
                <strong>⚠️ Attention</strong>
                La suppression d'un personnel supprimera automatiquement toutes ses polyvalences associées (CASCADE).
            </div>
            
            <?php foreach ($groupes_doublons as $key => $groupe): ?>
                <?php list($nom, $prenom) = explode('|', $key); ?>
                <div class="doublon-group">
                    <div class="group-header">
                        👤 <?php echo htmlspecialchars($nom . ' ' . $prenom); ?>
                        <span class="badge count"><?php echo count($groupe); ?> entrées</span>
                    </div>
                    
                    <?php foreach ($groupe as $person): ?>
                        <div class="person-card">
                            <div class="person-header">
                                <div class="person-info">
                                    <div class="person-id">
                                        ID: <?php echo $person['id']; ?>
                                        <span class="badge <?php echo strtolower($person['statut']); ?>">
                                            <?php echo htmlspecialchars($person['statut']); ?>
                                        </span>
                                    </div>
                                </div>
                                <form method="POST" class="delete-form" onsubmit="return confirm('Êtes-vous sûr de vouloir supprimer ce personnel (ID: <?php echo $person['id']; ?>) et toutes ses polyvalences ?');">
                                    <input type="hidden" name="delete_id" value="<?php echo $person['id']; ?>">
                                    <button type="submit" class="btn btn-delete">
                                        🗑️ Supprimer
                                    </button>
                                </form>
                            </div>
                            
                            <div class="person-details">
                                <div class="detail-item">
                                    <span class="detail-label">Matricule</span>
                                    <span class="detail-value">
                                        <?php echo $person['matricule'] ? htmlspecialchars($person['matricule']) : '<span class="no-data">Non défini</span>'; ?>
                                    </span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Numéro de poste</span>
                                    <span class="detail-value">
                                        <?php echo $person['numposte'] ? htmlspecialchars($person['numposte']) : '<span class="no-data">Non défini</span>'; ?>
                                    </span>
                                </div>
                                <div class="detail-item">
                                    <span class="detail-label">Service</span>
                                    <span class="detail-value">
                                        <?php echo $person['nom_service'] ? htmlspecialchars($person['nom_service']) : '<span class="no-data">Non défini</span>'; ?>
                                    </span>
                                </div>
                            </div>
                            
                            <?php if ($person['nb_polyvalences'] > 0): ?>
                                <div class="polyvalences">
                                    <div class="polyvalences-title">
                                        📊 Polyvalences
                                        <span class="badge count"><?php echo $person['nb_polyvalences']; ?></span>
                                    </div>
                                    <div class="polyvalences-list">
                                        <?php echo htmlspecialchars($person['liste_polyvalences']); ?>
                                    </div>
                                </div>
                            <?php else: ?>
                                <div class="polyvalences">
                                    <div class="polyvalences-title">📊 Polyvalences</div>
                                    <div class="no-data">Aucune polyvalence enregistrée</div>
                                </div>
                            <?php endif; ?>
                        </div>
                    <?php endforeach; ?>
                </div>
            <?php endforeach; ?>
        <?php endif; ?>
    </div>
</body>
</html>