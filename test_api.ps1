# Test Script for StudyFriend API

Write-Host "🧪 Testing StudyFriend API..." -ForegroundColor Cyan

$baseUrl = "http://localhost:8000/api/v1"
$headers = @{
    "Content-Type" = "application/json"
}

# Test 1: Health Check
Write-Host "`n📌 Test 1: Health Check" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get
    Write-Host "✅ Health check passed" -ForegroundColor Green
    Write-Host $response | ConvertTo-Json
} catch {
    Write-Host "❌ Health check failed: $_" -ForegroundColor Red
    exit 1
}

# Test 2: Register Student
Write-Host "`n📌 Test 2: Register Student" -ForegroundColor Yellow
$studentData = @{
    name = "Test Student"
    email = "student@test.com"
    password = "password123"
    role = "student"
    institution = "Test University"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/auth/register" -Method Post -Body $studentData -Headers $headers
    $studentToken = $response.data.access_token
    Write-Host "✅ Student registered successfully" -ForegroundColor Green
    Write-Host "Token: $($studentToken.Substring(0, 20))..." -ForegroundColor Gray
} catch {
    Write-Host "⚠️  Registration failed (user may already exist)" -ForegroundColor Yellow
    
    # Try login instead
    Write-Host "`n📌 Attempting login..." -ForegroundColor Yellow
    $loginData = @{
        email = "student@test.com"
        password = "password123"
    } | ConvertTo-Json
    
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/auth/login" -Method Post -Body $loginData -Headers $headers
        $studentToken = $response.data.access_token
        Write-Host "✅ Login successful" -ForegroundColor Green
    } catch {
        Write-Host "❌ Login failed: $_" -ForegroundColor Red
        exit 1
    }
}

# Test 3: Get Profile
Write-Host "`n📌 Test 3: Get Student Profile" -ForegroundColor Yellow
$authHeaders = @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer $studentToken"
}

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/auth/profile" -Method Get -Headers $authHeaders
    Write-Host "✅ Profile retrieved successfully" -ForegroundColor Green
    Write-Host "Name: $($response.data.name)" -ForegroundColor Gray
    Write-Host "Email: $($response.data.email)" -ForegroundColor Gray
    Write-Host "Role: $($response.data.role)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Profile retrieval failed: $_" -ForegroundColor Red
}

# Test 4: Register Faculty
Write-Host "`n📌 Test 4: Register Faculty" -ForegroundColor Yellow
$facultyData = @{
    name = "Test Faculty"
    email = "faculty@test.com"
    password = "password123"
    role = "faculty"
    institution = "Test University"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "$baseUrl/auth/register" -Method Post -Body $facultyData -Headers $headers
    $facultyToken = $response.data.access_token
    Write-Host "✅ Faculty registered successfully" -ForegroundColor Green
} catch {
    Write-Host "⚠️  Faculty registration failed (user may already exist)" -ForegroundColor Yellow
}

# Test 5: Get Materials
Write-Host "`n📌 Test 5: Get Study Materials" -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "$baseUrl/students/materials" -Method Get -Headers $authHeaders
    Write-Host "✅ Materials retrieved successfully" -ForegroundColor Green
    Write-Host "Total materials: $($response.data.Count)" -ForegroundColor Gray
} catch {
    Write-Host "❌ Materials retrieval failed: $_" -ForegroundColor Red
}

Write-Host "`n✨ Basic tests completed!" -ForegroundColor Green
Write-Host "`n📋 API Documentation available at:" -ForegroundColor Cyan
Write-Host "http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
