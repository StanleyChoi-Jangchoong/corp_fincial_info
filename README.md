# 🏢 오픈다트 재무 데이터 분석 서비스 (v2.1)

한국 기업의 재무 데이터를 시각화하고 AI 분석을 제공하는 웹 서비스입니다.

## ✨ 주요 기능

- 🔍 **실시간 기업 검색**: 3,800+ 기업 데이터베이스
- 📊 **재무 데이터 시각화**: Chart.js 기반 인터랙티브 차트
- 🤖 **AI 재무 분석**: Google Gemini AI 기반 분석 리포트
- 📈 **다양한 분석 탭**: 
  - 개요 (주요 재무지표)
  - AI분석 (AI 요약 및 상세 분석)
  - 재무구조 (자산=부채+자본 시각화)
  - 매출분석 (매출 추이 및 성장률)
  - 수익성 (ROE, ROA, 이익률)
  - 재무비율 (부채비율, 유동비율 등)
  - 성과지표 (성장률 분석)

## 🚀 배포 가이드

### 1. Heroku 배포 (추천)

#### 사전 준비
1. [Heroku 계정 생성](https://signup.heroku.com/)
2. [Heroku CLI 설치](https://devcenter.heroku.com/articles/heroku-cli)

#### 배포 단계
```bash
# 1. Heroku 로그인
heroku login

# 2. Git 저장소 초기화 (아직 안 했다면)
git init
git add .
git commit -m "Initial commit"

# 3. Heroku 앱 생성
heroku create your-app-name

# 4. 환경 변수 설정
heroku config:set OPEN_DART_API_KEY="your_open_dart_api_key"
heroku config:set GEMINI_API_KEY="your_gemini_api_key"

# 5. 배포
git push heroku main

# 6. 앱 실행
heroku open
```

### 2. Railway 배포

#### 사전 준비
1. [Railway 계정 생성](https://railway.app/)
2. GitHub 저장소 연결

#### 배포 단계
1. Railway 대시보드에서 "New Project" 클릭
2. "Deploy from GitHub repo" 선택
3. GitHub 저장소 연결
4. 환경 변수 설정:
   - `OPEN_DART_API_KEY`: 오픈다트 API 키
   - `GEMINI_API_KEY`: Gemini API 키
5. 자동 배포 완료

### 3. Render 배포

#### 사전 준비
1. [Render 계정 생성](https://render.com/)
2. GitHub 저장소 준비

#### 배포 단계
1. Render 대시보드에서 "New Web Service" 클릭
2. GitHub 저장소 연결
3. 설정:
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
4. 환경 변수 설정
5. 배포 완료

## 🔧 로컬 개발 환경

### 필수 요구사항
- Python 3.11+
- 오픈다트 API 키
- Google Gemini API 키

### 설치 및 실행
```bash
# 1. 저장소 클론
git clone <repository-url>
cd 05_vibe_fs5

# 2. 가상환경 생성 및 활성화
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 의존성 설치
pip install -r requirements.txt

# 4. 환경 변수 설정 (선택사항)
export OPEN_DART_API_KEY="your_api_key"
export GEMINI_API_KEY="your_gemini_key"

# 5. 서버 실행
python app.py
```

### 데이터베이스 설정
- `corp.xml` 파일이 프로젝트 루트에 있어야 합니다
- 서버 시작 시 자동으로 메모리 데이터베이스에 로드됩니다

## 📊 API 엔드포인트

### 기업 검색
- `GET /api/corporations/search?q={검색어}`: 기업 검색
- `GET /api/corporations/count`: 전체 기업 수 조회
- `GET /api/corporations/health`: API 상태 확인

### 재무 데이터
- `GET /api/financial/{corp_code}/summary?year={년도}&report={보고서}`: 재무 요약
- `GET /api/financial/{corp_code}/analysis?year={년도}&report={보고서}`: 재무 분석
- `GET /api/financial/{corp_code}/balance-structure?year={년도}&report={보고서}`: 재무구조
- `GET /api/financial/{corp_code}/ai-summary?year={년도}&report={보고서}`: AI 요약
- `GET /api/financial/{corp_code}/ai-analysis?year={년도}&report={보고서}`: AI 상세분석

## 🔑 API 키 설정

### 오픈다트 API
1. [오픈다트](https://opendart.fss.or.kr/) 회원가입
2. API 키 발급
3. 환경 변수 `OPEN_DART_API_KEY`에 설정

### Google Gemini API
1. [Google AI Studio](https://makersuite.google.com/app/apikey) 접속
2. API 키 생성
3. 환경 변수 `GEMINI_API_KEY`에 설정

## 🛠️ 기술 스택

- **Backend**: Python Flask
- **Frontend**: HTML5, CSS3, JavaScript (Vanilla)
- **Database**: SQLite (In-Memory)
- **Charts**: Chart.js
- **AI**: Google Gemini AI
- **API**: OpenDart API
- **Deployment**: Gunicorn

## 📝 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📞 문의

프로젝트에 대한 문의사항이 있으시면 이슈를 생성해주세요.
