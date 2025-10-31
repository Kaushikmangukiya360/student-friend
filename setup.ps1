# Quick Setup Script for StudyFriend Backend

Write-Host "🚀 Setting up StudyFriend Backend..." -ForegroundColor Cyan

# Check Python installation
Write-Host "`n📌 Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "✅ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Python not found. Please install Python 3.9+" -ForegroundColor Red
    exit 1
}

# Check MongoDB
Write-Host "`n📌 Checking MongoDB..." -ForegroundColor Yellow
$mongoRunning = Get-Process mongod -ErrorAction SilentlyContinue
if ($mongoRunning) {
    Write-Host "✅ MongoDB is running" -ForegroundColor Green
} else {
    Write-Host "⚠️  MongoDB not detected. Please ensure MongoDB is running." -ForegroundColor Yellow
}

# Create virtual environment
Write-Host "`n📌 Creating virtual environment..." -ForegroundColor Yellow
if (Test-Path "venv") {
    Write-Host "✅ Virtual environment already exists" -ForegroundColor Green
} else {
    python -m venv venv
    Write-Host "✅ Virtual environment created" -ForegroundColor Green
}

# Activate virtual environment
Write-Host "`n📌 Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1
Write-Host "✅ Virtual environment activated" -ForegroundColor Green

# Install dependencies
Write-Host "`n📌 Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt
Write-Host "✅ Dependencies installed" -ForegroundColor Green

# Create uploads directory
Write-Host "`n📌 Creating uploads directory..." -ForegroundColor Yellow
if (!(Test-Path "uploads")) {
    New-Item -ItemType Directory -Path "uploads" | Out-Null
    Write-Host "✅ Uploads directory created" -ForegroundColor Green
} else {
    Write-Host "✅ Uploads directory already exists" -ForegroundColor Green
}

# Check .env file
Write-Host "`n📌 Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "✅ .env file exists" -ForegroundColor Green
    Write-Host "⚠️  Please ensure you've added your GROQ_API_KEY to .env" -ForegroundColor Yellow
} else {
    Write-Host "❌ .env file not found" -ForegroundColor Red
    Write-Host "Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
    Write-Host "✅ .env file created. Please update it with your credentials." -ForegroundColor Green
}

Write-Host "`n✨ Setup complete!" -ForegroundColor Green
Write-Host "`n📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Update .env file with your GROQ_API_KEY" -ForegroundColor White
Write-Host "2. Ensure MongoDB is running" -ForegroundColor White
Write-Host "3. Run: cd app" -ForegroundColor White
Write-Host "4. Run: python main.py" -ForegroundColor White
Write-Host "5. Visit: http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
