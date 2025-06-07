# Docker 설정 테스트 가이드

## 🧪 **환경변수 및 볼륨 매핑 테스트**

### 1️⃣ **환경변수 확인**

```bash
# .env 파일 내용 확인
cat .env | grep DOCS_BASE_DIR

# 실제 디렉토리 존재 확인
ls -la /Volumes/Library/Archive  # 또는 .env의 DOCS_BASE_DIR 경로
```

### 2️⃣ **Docker Compose 변수 치환 테스트**

```bash
# docker-compose.yml에서 환경변수가 제대로 치환되는지 확인
docker-compose config

# 출력에서 volumes 섹션 확인:
# volumes:
#   - /Volumes/Library/Archive:/app/docs  # 실제 경로로 치환됨
```

### 3️⃣ **볼륨 마운트 테스트**

```bash
# 컨테이너 실행 후 볼륨 마운트 확인
docker-compose up -d

# 백엔드 컨테이너 내부에서 확인
docker exec -it betarxiv-backend ls -la /app/docs

# 파일 개수 비교
echo "로컬 파일 개수:"
find ${DOCS_BASE_DIR} -name "*.pdf" | wc -l

echo "Docker 내부 파일 개수:"
docker exec -it betarxiv-backend find /app/docs -name "*.pdf" | wc -l
```

### 4️⃣ **환경변수 전달 테스트**

```bash
# 백엔드 컨테이너 내부에서 환경변수 확인
docker exec -it betarxiv-backend env | grep DOCS_BASE_DIR

# 예상 출력: DOCS_BASE_DIR=/app/docs
```

### 5️⃣ **API 엔드포인트 테스트**

```bash
# 백엔드 API가 문서 디렉토리에 접근할 수 있는지 테스트
curl http://localhost:8001/documents

# 썸네일 생성 테스트 (문서가 있는 경우)
curl http://localhost:8001/documents/{document_id}/thumbnail
```

## 🔧 **문제 해결**

### 볼륨이 빈 경우
```bash
# 1. .env 파일 확인
cat .env | grep DOCS_BASE_DIR

# 2. 경로 존재 여부 확인
ls -la /your/actual/path

# 3. Docker Desktop File Sharing 설정 확인
# Docker Desktop > Settings > Resources > File Sharing
```

### 환경변수 치환 실패
```bash
# docker-compose config로 실제 치환된 값 확인
docker-compose config | grep -A 5 volumes

# .env 파일이 올바른 위치에 있는지 확인
ls -la .env
```

### 권한 문제
```bash
# 디렉토리 권한 확인
ls -la ${DOCS_BASE_DIR}

# Docker가 읽을 수 있는지 확인
docker run --rm -v ${DOCS_BASE_DIR}:/test alpine ls -la /test
``` 