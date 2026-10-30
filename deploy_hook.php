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

// 2. Clear opcache if enabled
if (function_exists('opcache_reset')) {
    @opcache_reset();
}
clearstatcache(true);

header('Content-Type: application/json');
echo json_encode([
    'success' => true,
    'message' => 'Passenger application reloaded successfully!',
    'timestamp' => date('Y-m-d H:i:s')
]);
