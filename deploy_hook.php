<?php
$secret = 'shopbusk_deploy_secret_2026';
$token = $_GET['secret'] ?? $_SERVER['HTTP_X_DEPLOY_SECRET'] ?? '';

if (empty($token) || !hash_equals($secret, (string)$token)) {
    http_response_code(403);
    header('Content-Type: application/json');
    echo json_encode(['success' => false, 'message' => 'Forbidden']);
    exit;
}

// 1. Touch restart.txt for instant Passenger reload
$restartDir = __DIR__ . '/tmp';
if (!is_dir($restartDir)) {
    @mkdir($restartDir, 0755, true);
}
@touch($restartDir . '/restart.txt');

// Ensure media directories exist with valid permissions
$mediaDirs = [
    __DIR__ . '/media',
    __DIR__ . '/media/products',
    __DIR__ . '/media/products/gallery',
    __DIR__ . '/media/categories',
    __DIR__ . '/media/brands',
    __DIR__ . '/media/branding',
];
foreach ($mediaDirs as $md) {
    if (!is_dir($md)) {
        @mkdir($md, 0755, true);
    }
}

// 2. Parse .env for database credentials
$env = [];
$envFile = __DIR__ . '/.env';
if (file_exists($envFile)) {
    $lines = file($envFile, FILE_IGNORE_NEW_LINES | FILE_SKIP_EMPTY_LINES);
    foreach ($lines as $line) {
        $line = trim($line);
        if ($line === '' || str_starts_with($line, '#')) continue;
        if (str_contains($line, '=')) {
            [$k, $v] = explode('=', $line, 2);
            $env[trim($k)] = trim($v, " \t\n\r\0\x0B'\"");
        }
    }
}

$dbStatus = [];
if (!empty($env['DB_NAME']) && !empty($env['DB_USER'])) {
    try {
        $dsn = sprintf('mysql:host=%s;port=%s;dbname=%s;charset=utf8mb4',
            $env['DB_HOST'] ?? 'localhost',
            $env['DB_PORT'] ?? '3306',
            $env['DB_NAME']
        );
        $pdo = new PDO($dsn, $env['DB_USER'], $env['DB_PASSWORD'] ?? '', [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        ]);

        // Check active_theme column on core_sitesetting
        $stmt = $pdo->prepare("
            SELECT COUNT(*) AS cnt 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = :schema 
              AND TABLE_NAME = 'core_sitesetting' 
              AND COLUMN_NAME = 'active_theme'
        ");
        $stmt->execute(['schema' => $env['DB_NAME']]);
        $hasActiveTheme = (int)($stmt->fetch()['cnt'] ?? 0) > 0;

        if (!$hasActiveTheme) {
            $pdo->exec("ALTER TABLE core_sitesetting ADD COLUMN active_theme varchar(50) NOT NULL DEFAULT 'mega_market'");
            $dbStatus['active_theme_added'] = true;
        } else {
            $dbStatus['active_theme_already_exists'] = true;
        }

        // Ensure migration records exist in django_migrations
        $pdo->exec("
            INSERT IGNORE INTO django_migrations (app, name, applied) 
            VALUES 
                ('core', '0005_sitesetting_active_theme_and_more', NOW()),
                ('core', '0006_alter_sitesetting_active_theme', NOW())
        ");
        $dbStatus['migrations_synced'] = true;

        // Check if product gallery images exist
        $stmtImg = $pdo->query("SELECT COUNT(*) AS img_count FROM product_productimage");
        $dbStatus['product_images_count'] = (int)($stmtImg->fetch()['img_count'] ?? 0);

        // Check if categories exist
        $stmtCat = $pdo->query("SELECT COUNT(*) AS cat_count FROM product_category");
        $dbStatus['categories_count'] = (int)($stmtCat->fetch()['cat_count'] ?? 0);

        // Check active theme in DB
        $stmtSet = $pdo->query("SELECT active_theme FROM core_sitesetting LIMIT 1");
        $dbStatus['current_active_theme'] = $stmtSet->fetch()['active_theme'] ?? null;

    } catch (Throwable $e) {
        $dbStatus['error'] = $e->getMessage();
    }
}

// 3. Clear opcache if enabled
if (function_exists('opcache_reset')) {
    @opcache_reset();
}
clearstatcache(true);

header('Content-Type: application/json');
echo json_encode([
    'success' => true,
    'message' => 'Passenger application reloaded successfully!',
    'db' => $dbStatus,
    'timestamp' => date('Y-m-d H:i:s')
], JSON_PRETTY_PRINT);
