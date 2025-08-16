const express = require('express');
const fs = require('fs');
const xml2js = require('xml2js');
const Database = require('better-sqlite3');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = 8080;

// 데이터베이스 초기화
const db = new Database(':memory:');

// 미들웨어 설정
app.use(cors());
app.use(express.json());
app.use(express.static('public'));

// 데이터베이스 테이블 생성
db.exec(`
    CREATE TABLE IF NOT EXISTS corporations (
        corp_code TEXT PRIMARY KEY,
        corp_name TEXT NOT NULL,
        corp_eng_name TEXT,
        stock_code TEXT,
        modify_date TEXT
    )
`);

// corp.xml 파일을 읽어서 데이터베이스에 저장하는 함수
async function loadCorporationData() {
    try {
        console.log('corp.xml 파일을 읽어서 데이터베이스에 로드 중...');
        
        const xmlData = fs.readFileSync('corp.xml', 'utf8');
        const parser = new xml2js.Parser();
        const result = await parser.parseStringPromise(xmlData);
        
        const corporations = result.result.list;
        
        const insertStmt = db.prepare(`
            INSERT OR REPLACE INTO corporations 
            (corp_code, corp_name, corp_eng_name, stock_code, modify_date) 
            VALUES (?, ?, ?, ?, ?)
        `);
        
        const insertMany = db.transaction((corps) => {
            for (const corp of corps) {
                const corpCode = corp.corp_code ? corp.corp_code[0] : null;
                const corpName = corp.corp_name ? corp.corp_name[0] : null;
                const corpEngName = corp.corp_eng_name ? corp.corp_eng_name[0] : null;
                const stockCode = corp.stock_code ? corp.stock_code[0] : null;
                const modifyDate = corp.modify_date ? corp.modify_date[0] : null;
                
                // 빈 문자열을 null로 처리
                const cleanEngName = corpEngName && corpEngName.trim() ? corpEngName.trim() : null;
                const cleanStockCode = stockCode && stockCode.trim() ? stockCode.trim() : null;
                
                if (corpCode && corpName) {
                    insertStmt.run(corpCode, corpName, cleanEngName, cleanStockCode, modifyDate);
                }
            }
        });
        
        insertMany(corporations);
        
        const count = db.prepare('SELECT COUNT(*) as count FROM corporations').get();
        console.log(`데이터 로드 완료! 총 ${count.count}개 기업`);
        
    } catch (error) {
        console.error('XML 파일 처리 중 오류 발생:', error.message);
    }
}

// API 라우트들

// 회사명으로 검색
app.get('/api/corporations/search', (req, res) => {
    const query = req.query.q;
    
    if (!query || query.trim() === '') {
        return res.json([]);
    }
    
    const searchTerm = `%${query.trim()}%`;
    const stmt = db.prepare(`
        SELECT * FROM corporations 
        WHERE corp_name LIKE ? OR corp_eng_name LIKE ? 
        ORDER BY corp_name 
        LIMIT 100
    `);
    
    const results = stmt.all(searchTerm, searchTerm);
    res.json(results);
});

// 기업 코드로 상세 조회
app.get('/api/corporations/:corpCode', (req, res) => {
    const corpCode = req.params.corpCode;
    const stmt = db.prepare('SELECT * FROM corporations WHERE corp_code = ?');
    const result = stmt.get(corpCode);
    
    if (result) {
        res.json(result);
    } else {
        res.status(404).json({ error: '기업을 찾을 수 없습니다.' });
    }
});

// 주식 코드로 검색
app.get('/api/corporations/stock/:stockCode', (req, res) => {
    const stockCode = req.params.stockCode;
    const stmt = db.prepare('SELECT * FROM corporations WHERE stock_code = ?');
    const results = stmt.all(stockCode);
    res.json(results);
});

// 전체 기업 수 조회
app.get('/api/corporations/count', (req, res) => {
    const stmt = db.prepare('SELECT COUNT(*) as count FROM corporations');
    const result = stmt.get();
    res.json(result.count);
});

// 상태 확인용 엔드포인트
app.get('/api/corporations/health', (req, res) => {
    res.json({ status: 'API 서버가 정상적으로 동작 중입니다.' });
});

// 웹 페이지 라우트들
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.get('/search', (req, res) => {
    res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

// 서버 시작
async function startServer() {
    // corp.xml 파일이 존재하는지 확인
    if (fs.existsSync('corp.xml')) {
        await loadCorporationData();
    } else {
        console.warn('corp.xml 파일을 찾을 수 없습니다. 프로젝트 루트에 corp.xml 파일을 배치해주세요.');
    }
    
    app.listen(PORT, () => {
        console.log(`🚀 오픈다트 재무 데이터 분석 서비스가 http://localhost:${PORT} 에서 실행 중입니다.`);
        console.log(`📊 메인 페이지: http://localhost:${PORT}`);
        console.log(`🔍 API 상태: http://localhost:${PORT}/api/corporations/health`);
    });
}

startServer();
