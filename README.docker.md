# BetArxiv Docker 배포 가이드

## 🐳 Docker로 전체 시스템 배포하기

### 📋 사전 준비

1. **Docker 및 Docker Compose 설치**
2. **환경변수 설정**:
   ```bash
   cp env.template .env
   # .env 파일을 편집해서 다음 값들을 설정:
   # - GOOGLE_API_KEY=your_actual_google_api_key_here
   # - DOCS_BASE_DIR=/Volumes/Library/Archive (실제 경로로 변경)
   ```
   
   **⚠️ 중요**: `.env` 파일에는 실제 API 키와 경로를 입력해야 합니다!

3. **포트 충돌 해결**:
   - 기존 로컬 서비스와 충돌 없이 Docker 포트 분리
   ```
   로컬 개발환경        Docker 환경
   Frontend:  3000  →  Frontend:  3001  
   Backend:   8000  →  Backend:   8001
   PostgreSQL: 5432 →  PostgreSQL: 5433
   ```

### 🚀 전체 시스템 실행

```bash
# 모든 서비스 빌드 및 실행
docker-compose up --build

# 백그라운드 실행
docker-compose up -d --build
```

### 📊 서비스 접근

- **Frontend**: http://localhost:3001
- **Backend API**: http://localhost:8001
- **Database**: localhost:5433

### 🛠️ 개별 서비스 관리

#### Backend만 실행
```bash
cd backend
docker build -t betarxiv-backend .
docker run -p 8001:8000 --env-file ../.env betarxiv-backend
```

#### Frontend만 실행
```bash
cd frontend  
docker build -t betarxiv-frontend .
docker run -p 3001:3000 -e BACKEND_URL=http://localhost:8001 betarxiv-frontend
```

### 🗂️ 생성된 Docker 파일들

```
betarxiv/
├── docker-compose.yml          # 전체 시스템 오케스트레이션
├── backend/
│   ├── Dockerfile             # FastAPI 백엔드
│   └── .dockerignore         
├── frontend/
│   ├── Dockerfile             # Next.js 프론트엔드
│   └── .dockerignore
└── env.template               # 환경변수 템플릿
```

### 🔧 주요 기능

1. **Multi-stage 빌드**: 효율적인 이미지 크기
2. **Health checks**: 서비스 상태 모니터링
3. **Non-root 사용자**: 보안 강화
4. **pgvector 지원**: PostgreSQL + 벡터 검색
5. **Auto-restart**: 컨테이너 자동 재시작
6. **Volume 매핑**: 로컬 문서 디렉토리를 Docker 내부로 연결

### 📝 문제 해결

#### 로그 확인
```bash
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db
```

#### 컨테이너 재시작
```bash
docker-compose restart backend
docker-compose restart frontend
```

#### 볼륨 초기화
```bash
docker-compose down -v
docker-compose up --build
```

### 📁 **볼륨 매핑 상세**

```
로컬 시스템 (.env 파일)    →    Docker 컨테이너
${DOCS_BASE_DIR}          →    /app/docs

환경변수:
- 로컬 개발: DOCS_BASE_DIR=/Volumes/Library/Archive (직접 사용)
- Docker:   DOCS_BASE_DIR=/app/docs (컨테이너 내부 매핑된 경로)
```

**주의사항**:
- 로컬 `DOCS_BASE_DIR` 경로가 실제로 존재하는지 확인
- 해당 디렉토리에 대한 읽기 권한 필요
- Docker Desktop에서 해당 경로 공유 허용 필요