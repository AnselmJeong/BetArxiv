# BetArxiv 배포 단계별 가이드

## 🚀 **Step-by-Step 배포 과정**

### 1️⃣ **환경변수 설정**

```bash
# 1. 템플릿 복사
cp env.template .env

# 2. .env 파일 편집 (실제 값으로 변경)
nano .env  # 또는 원하는 에디터 사용
```

**편집해야 할 값들:**
```bash
# Google AI API Key (필수!)
GOOGLE_API_KEY=your_actual_google_api_key_here

# Document Storage (실제 경로로 변경)
DOCS_BASE_DIR=/Volumes/Library/Archive

# 나머지는 기본값 사용 가능
DATABASE_URL=postgresql://betarxiv:betarxiv_password@localhost:5433/betarxiv
ARXIV_API_URL=http://export.arxiv.org/api/query
BACKEND_URL=http://backend:8000
NODE_ENV=development
```

### 2️⃣ **디렉토리 준비**

```bash
# 문서 디렉토리 확인
ls -la /Volumes/Library/Archive

# 임시 documents 디렉토리 생성 (없으면)
mkdir -p documents
```

### 3️⃣ **Docker 빌드 및 실행**

```bash
# 전체 시스템 빌드 및 실행
docker-compose up --build

# 백그라운드에서 실행하려면
docker-compose up -d --build
```

### 4️⃣ **접속 확인**

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **Database**: localhost:5433

### 5️⃣ **로그 확인**

```bash
# 전체 로그
docker-compose logs

# 특정 서비스 로그
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

## 🔧 **문제 해결**

### 환경변수 누락 오류
```bash
# .env 파일 확인
cat .env

# 누락된 값이 있으면 편집
nano .env
```

### 볼륨 마운트 오류
```bash
# Docker Desktop에서 File Sharing 확인
# DOCS_BASE_DIR 경로가 공유되어 있는지 확인

# .env 파일의 DOCS_BASE_DIR 경로 확인
echo $DOCS_BASE_DIR
ls -la $DOCS_BASE_DIR
```

### 포트 충돌
```bash
# 사용 중인 포트 확인
lsof -i :3001
lsof -i :8001
lsof -i :5433
```

## 📁 **파일 구조 최종 확인**

```
betarxiv/
├── .env                    ← 실제 환경변수 (gitignore)
├── env.template           ← 템플릿
├── docker-compose.yml     ← Docker 설정
├── README.docker.md       ← Docker 가이드
├── backend/
│   ├── Dockerfile        
│   └── app/
└── frontend/
    ├── Dockerfile
    └── src/
``` 