#!/usr/bin/env python3
"""
오픈다트 재무 데이터 시각화 분석 서비스
Flask 기반 웹 애플리케이션
"""

from flask import Flask, render_template, jsonify, request, send_from_directory
import xml.etree.ElementTree as ET
import sqlite3
import os
import threading
import json
import requests
from datetime import datetime
import google.generativeai as genai
import requests

# 환경 변수 설정
OPEN_DART_API_KEY = os.environ.get('OPEN_DART_API_KEY', '3f53feeb48fbdfcba84eecd12d12a106d691d2a3')
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY', 'AIzaSyAoqUUnhpGA9DQ4UsAgGay3X-inzths4KQ')

# Gemini AI 설정
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

app = Flask(__name__, static_folder='static', template_folder='templates')

# 전역 변수
db_loaded = False
db_lock = threading.Lock()

# 오픈다트 API 설정
OPENDART_API_KEY = OPEN_DART_API_KEY
OPENDART_BASE_URL = "https://opendart.fss.or.kr/api"

def init_database():
    """데이터베이스 초기화"""
    conn = sqlite3.connect(':memory:', check_same_thread=False)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS corporations (
            corp_code TEXT PRIMARY KEY,
            corp_name TEXT NOT NULL,
            corp_eng_name TEXT,
            stock_code TEXT,
            modify_date TEXT
        )
    ''')
    
    conn.commit()
    return conn

def load_corp_data(conn):
    """corp.xml 파일을 읽어서 데이터베이스에 로드"""
    global db_loaded
    
    if db_loaded:
        return
    
    try:
        print("corp.xml 파일을 읽어서 데이터베이스에 로드 중...")
        
        if not os.path.exists('corp.xml'):
            print("⚠️  corp.xml 파일을 찾을 수 없습니다.")
            return
        
        # XML 파싱
        tree = ET.parse('corp.xml')
        root = tree.getroot()
        
        cursor = conn.cursor()
        
        count = 0
        for corp_list in root.findall('list'):
            corp_code = corp_list.find('corp_code')
            corp_name = corp_list.find('corp_name')
            corp_eng_name = corp_list.find('corp_eng_name')
            stock_code = corp_list.find('stock_code')
            modify_date = corp_list.find('modify_date')
            
            # 텍스트 추출
            corp_code_text = corp_code.text if corp_code is not None else None
            corp_name_text = corp_name.text if corp_name is not None else None
            corp_eng_name_text = corp_eng_name.text if corp_eng_name is not None else None
            stock_code_text = stock_code.text if stock_code is not None else None
            modify_date_text = modify_date.text if modify_date is not None else None
            
            # 빈 문자열을 None으로 처리
            if corp_eng_name_text and corp_eng_name_text.strip() == '':
                corp_eng_name_text = None
            if stock_code_text and stock_code_text.strip() == '':
                stock_code_text = None
            
            if corp_code_text and corp_name_text:
                cursor.execute(
                    'INSERT OR REPLACE INTO corporations (corp_code, corp_name, corp_eng_name, stock_code, modify_date) VALUES (?, ?, ?, ?, ?)',
                    (corp_code_text, corp_name_text, corp_eng_name_text, stock_code_text, modify_date_text)
                )
                count += 1
                
                # 진행 상황 출력 (1000개마다)
                if count % 1000 == 0:
                    print(f"처리된 기업 수: {count}")
        
        conn.commit()
        db_loaded = True
        print(f"데이터 로드 완료! 총 {count}개 기업")
        
    except Exception as e:
        print(f"XML 파일 처리 중 오류 발생: {e}")

# 데이터베이스 연결 생성
db_conn = init_database()

@app.route('/')
def index():
    """메인 페이지"""
    return send_from_directory('static', 'index.html')

@app.route('/search')
def search_page():
    """검색 페이지 (메인과 동일)"""
    return send_from_directory('static', 'index.html')

@app.route('/api/corporations/search')
def search_corporations():
    """회사명으로 검색"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify([])
    
    # 디버깅을 위한 로그
    print(f"Search query received: '{query}' (length: {len(query)})")
    
    with db_lock:
        cursor = db_conn.cursor()
        search_term = f'%{query}%'
        
        cursor.execute('''
            SELECT corp_code, corp_name, corp_eng_name, stock_code, modify_date 
            FROM corporations 
            WHERE corp_name LIKE ? OR corp_eng_name LIKE ? 
            ORDER BY corp_name 
            LIMIT 100
        ''', (search_term, search_term))
        
        results = cursor.fetchall()
        
        # 결과를 딕셔너리 리스트로 변환
        corporations = []
        for row in results:
            corporations.append({
                'corp_code': row[0],
                'corp_name': row[1],
                'corp_eng_name': row[2],
                'stock_code': row[3],
                'modify_date': row[4]
            })
        
        return jsonify(corporations)

@app.route('/api/corporations/<corp_code>')
def get_corporation(corp_code):
    """기업 코드로 상세 조회"""
    with db_lock:
        cursor = db_conn.cursor()
        cursor.execute(
            'SELECT corp_code, corp_name, corp_eng_name, stock_code, modify_date FROM corporations WHERE corp_code = ?',
            (corp_code,)
        )
        
        result = cursor.fetchone()
        
        if result:
            corporation = {
                'corp_code': result[0],
                'corp_name': result[1],
                'corp_eng_name': result[2],
                'stock_code': result[3],
                'modify_date': result[4]
            }
            return jsonify(corporation)
        else:
            return jsonify({'error': '기업을 찾을 수 없습니다.'}), 404

@app.route('/api/corporations/stock/<stock_code>')
def get_corporation_by_stock(stock_code):
    """주식 코드로 검색"""
    with db_lock:
        cursor = db_conn.cursor()
        cursor.execute(
            'SELECT corp_code, corp_name, corp_eng_name, stock_code, modify_date FROM corporations WHERE stock_code = ?',
            (stock_code,)
        )
        
        results = cursor.fetchall()
        
        corporations = []
        for row in results:
            corporations.append({
                'corp_code': row[0],
                'corp_name': row[1],
                'corp_eng_name': row[2],
                'stock_code': row[3],
                'modify_date': row[4]
            })
        
        return jsonify(corporations)

@app.route('/api/corporations/count')
def get_total_count():
    """전체 기업 수 조회"""
    with db_lock:
        cursor = db_conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM corporations')
        count = cursor.fetchone()[0]
        return jsonify(count)

@app.route('/api/corporations/health')
def health_check():
    """상태 확인용 엔드포인트"""
    return jsonify({'status': 'API 서버가 정상적으로 동작 중입니다.'})

# 오픈다트 API 관련 함수들
def call_opendart_api(endpoint, params):
    """오픈다트 API 호출 공통 함수"""
    try:
        params['crtfc_key'] = OPENDART_API_KEY
        url = f"{OPENDART_BASE_URL}/{endpoint}"
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        data = response.json()
        
        # API 에러 체크
        if data.get('status') != '000':
            error_messages = {
                '010': '등록되지 않은 키입니다.',
                '011': '사용할 수 없는 키입니다.',
                '012': '접근할 수 없는 IP입니다.',
                '013': '조회된 데이터가 없습니다.',
                '020': '요청 제한을 초과하였습니다.',
                '100': '필드의 부적절한 값입니다.',
                '800': '시스템 점검 중입니다.',
                '900': '정의되지 않은 오류가 발생하였습니다.'
            }
            error_msg = error_messages.get(data.get('status'), data.get('message', '알 수 없는 오류'))
            return {'error': error_msg, 'status': data.get('status')}
        
        return data
        
    except requests.exceptions.RequestException as e:
        return {'error': f'API 호출 오류: {str(e)}'}
    except json.JSONDecodeError as e:
        return {'error': f'JSON 파싱 오류: {str(e)}'}
    except Exception as e:
        return {'error': f'예상치 못한 오류: {str(e)}'}

def get_financial_statements(corp_code, bsns_year, reprt_code):
    """단일회사 주요계정 조회"""
    params = {
        'corp_code': corp_code,
        'bsns_year': bsns_year,
        'reprt_code': reprt_code
    }
    
    return call_opendart_api('fnlttSinglAcnt.json', params)

def format_financial_data(financial_data):
    """재무 데이터 포맷팅"""
    if 'error' in financial_data:
        return financial_data
    
    # 데이터가 없는 경우
    if not financial_data.get('list'):
        return {'error': '조회된 재무 데이터가 없습니다.'}
    
    # 재무제표별로 데이터 분류
    formatted_data = {
        'company_info': {},
        'balance_sheet': [],  # 재무상태표
        'income_statement': [],  # 손익계산서
        'metadata': {}
    }
    
    for item in financial_data['list']:
        # 회사 기본 정보
        if not formatted_data['company_info']:
            formatted_data['company_info'] = {
                'bsns_year': item.get('bsns_year'),
                'stock_code': item.get('stock_code'),
                'reprt_code': item.get('reprt_code'),
                'rcept_no': item.get('rcept_no')
            }
        
        # 재무제표 구분
        if item.get('sj_div') == 'BS':  # 재무상태표
            formatted_data['balance_sheet'].append(item)
        elif item.get('sj_div') == 'IS':  # 손익계산서
            formatted_data['income_statement'].append(item)
    
    return formatted_data

# 재무 데이터 API 엔드포인트들
@app.route('/api/financial/<corp_code>')
def get_financial_data(corp_code):
    """재무 데이터 조회"""
    bsns_year = request.args.get('year', str(datetime.now().year - 1))  # 기본값: 작년
    reprt_code = request.args.get('report', '11011')  # 기본값: 사업보고서
    
    # 재무 데이터 조회
    financial_data = get_financial_statements(corp_code, bsns_year, reprt_code)
    
    if 'error' in financial_data:
        return jsonify(financial_data), 400
    
    # 데이터 포맷팅
    formatted_data = format_financial_data(financial_data)
    
    return jsonify(formatted_data)

@app.route('/api/financial/<corp_code>/summary')
def get_financial_summary(corp_code):
    """재무 데이터 요약 정보"""
    bsns_year = request.args.get('year', str(datetime.now().year - 1))
    reprt_code = request.args.get('report', '11011')
    
    # 재무 데이터 조회
    financial_data = get_financial_statements(corp_code, bsns_year, reprt_code)
    
    if 'error' in financial_data:
        return jsonify(financial_data), 400
    
    if not financial_data.get('list'):
        return jsonify({'error': '조회된 재무 데이터가 없습니다.'}), 400
    
    # 주요 계정 추출
    summary = {
        'company_info': {
            'bsns_year': financial_data['list'][0].get('bsns_year'),
            'stock_code': financial_data['list'][0].get('stock_code'),
            'reprt_code': financial_data['list'][0].get('reprt_code')
        },
        'key_accounts': {
            'assets': None,  # 자산총계
            'liabilities': None,  # 부채총계
            'equity': None,  # 자본총계
            'revenue': None,  # 매출액
            'operating_profit': None,  # 영업이익
            'net_income': None  # 당기순이익
        }
    }
    
    # 주요 계정 값 추출
    for item in financial_data['list']:
        account_name = item.get('account_nm', '').strip()
        current_amount = item.get('thstrm_amount')
        
        if current_amount and current_amount.replace(',', '').replace('-', '').isdigit():
            amount = int(current_amount.replace(',', ''))
            
            if '자산총계' in account_name:
                summary['key_accounts']['assets'] = amount
            elif '부채총계' in account_name:
                summary['key_accounts']['liabilities'] = amount
            elif '자본총계' in account_name:
                summary['key_accounts']['equity'] = amount
            elif '매출액' in account_name and item.get('sj_div') == 'IS':
                summary['key_accounts']['revenue'] = amount
            elif '영업이익' in account_name and '영업이익(손실)' not in account_name:
                summary['key_accounts']['operating_profit'] = amount
            elif '영업이익(손실)' in account_name:
                summary['key_accounts']['operating_profit'] = amount
            elif '당기순이익' in account_name and '당기순이익(손실)' not in account_name:
                summary['key_accounts']['net_income'] = amount
            elif '당기순이익(손실)' in account_name:
                summary['key_accounts']['net_income'] = amount
    
    return jsonify(summary)

@app.route('/api/financial/<corp_code>/analysis')
def get_financial_analysis(corp_code):
    """재무 분석 - 매출액, 수익성, 재무비율 분석"""
    bsns_year = request.args.get('year', str(datetime.now().year - 1))
    reprt_code = request.args.get('report', '11011')
    
    # 재무 데이터 조회
    financial_data = get_financial_statements(corp_code, bsns_year, reprt_code)
    
    if 'error' in financial_data:
        return jsonify(financial_data), 400
    
    if not financial_data.get('list'):
        return jsonify({'error': '조회된 재무 데이터가 없습니다.'}), 400
    
    # 분석 결과 초기화
    analysis = {
        'company_info': {
            'bsns_year': financial_data['list'][0].get('bsns_year'),
            'stock_code': financial_data['list'][0].get('stock_code'),
            'reprt_code': financial_data['list'][0].get('reprt_code')
        },
        'revenue_analysis': {},
        'profitability_analysis': {},
        'financial_ratios': {},
        'performance_indicators': {}
    }
    
    # 재무 데이터 추출
    accounts = {}
    for item in financial_data['list']:
        account_name = item.get('account_nm', '').strip()
        current_amount = item.get('thstrm_amount')
        previous_amount = item.get('frmtrm_amount')
        
        if current_amount and current_amount.replace(',', '').replace('-', '').isdigit():
            current_value = int(current_amount.replace(',', ''))
            previous_value = None
            
            if previous_amount and previous_amount.replace(',', '').replace('-', '').isdigit():
                previous_value = int(previous_amount.replace(',', ''))
            
            # 주요 계정별 분류
            if '자산총계' in account_name:
                accounts['total_assets'] = {'current': current_value, 'previous': previous_value}
            elif '부채총계' in account_name:
                accounts['total_liabilities'] = {'current': current_value, 'previous': previous_value}
            elif '자본총계' in account_name:
                accounts['total_equity'] = {'current': current_value, 'previous': previous_value}
            elif '매출액' in account_name and item.get('sj_div') == 'IS':
                accounts['revenue'] = {'current': current_value, 'previous': previous_value}
            elif '매출총이익' in account_name:
                accounts['gross_profit'] = {'current': current_value, 'previous': previous_value}
            elif '영업이익' in account_name and '영업이익(손실)' not in account_name:
                accounts['operating_profit'] = {'current': current_value, 'previous': previous_value}
            elif '영업이익(손실)' in account_name:
                accounts['operating_profit'] = {'current': current_value, 'previous': previous_value}
            elif '당기순이익' in account_name and '당기순이익(손실)' not in account_name:
                accounts['net_income'] = {'current': current_value, 'previous': previous_value}
            elif '당기순이익(손실)' in account_name:
                accounts['net_income'] = {'current': current_value, 'previous': previous_value}
            elif '영업활동으로인한현금흐름' in account_name.replace(' ', ''):
                accounts['operating_cash_flow'] = {'current': current_value, 'previous': previous_value}
    
    # 1. 매출액 및 수익성 분석
    if 'revenue' in accounts:
        revenue_data = accounts['revenue']
        analysis['revenue_analysis'] = {
            'current_revenue': revenue_data['current'],
            'previous_revenue': revenue_data['previous'],
            'revenue_growth_rate': None,
            'revenue_trend': '정보없음'
        }
        
        if revenue_data['previous'] and revenue_data['previous'] != 0:
            growth_rate = ((revenue_data['current'] - revenue_data['previous']) / revenue_data['previous']) * 100
            analysis['revenue_analysis']['revenue_growth_rate'] = round(growth_rate, 2)
            
            if growth_rate > 5:
                analysis['revenue_analysis']['revenue_trend'] = '매출 증가'
            elif growth_rate < -5:
                analysis['revenue_analysis']['revenue_trend'] = '매출 감소'
            else:
                analysis['revenue_analysis']['revenue_trend'] = '매출 안정'
    
    # 2. 수익성 지표 분석
    profitability = analysis['profitability_analysis']
    
    # 매출총이익률
    if 'gross_profit' in accounts and 'revenue' in accounts:
        if accounts['revenue']['current'] != 0:
            gross_margin = (accounts['gross_profit']['current'] / accounts['revenue']['current']) * 100
            profitability['gross_profit_margin'] = round(gross_margin, 2)
    
    # 영업이익률
    if 'operating_profit' in accounts and 'revenue' in accounts:
        if accounts['revenue']['current'] != 0:
            operating_margin = (accounts['operating_profit']['current'] / accounts['revenue']['current']) * 100
            profitability['operating_profit_margin'] = round(operating_margin, 2)
    
    # 순이익률
    if 'net_income' in accounts and 'revenue' in accounts:
        if accounts['revenue']['current'] != 0:
            net_margin = (accounts['net_income']['current'] / accounts['revenue']['current']) * 100
            profitability['net_profit_margin'] = round(net_margin, 2)
    
    # ROA (총자산수익률)
    if 'net_income' in accounts and 'total_assets' in accounts:
        if accounts['total_assets']['current'] != 0:
            roa = (accounts['net_income']['current'] / accounts['total_assets']['current']) * 100
            profitability['roa'] = round(roa, 2)
    
    # ROE (자기자본수익률)
    if 'net_income' in accounts and 'total_equity' in accounts:
        if accounts['total_equity']['current'] != 0:
            roe = (accounts['net_income']['current'] / accounts['total_equity']['current']) * 100
            profitability['roe'] = round(roe, 2)
    
    # 3. 재무 비율 분석
    ratios = analysis['financial_ratios']
    
    # 부채비율
    if 'total_liabilities' in accounts and 'total_equity' in accounts:
        if accounts['total_equity']['current'] != 0:
            debt_ratio = (accounts['total_liabilities']['current'] / accounts['total_equity']['current']) * 100
            ratios['debt_to_equity_ratio'] = round(debt_ratio, 2)
    
    # 자기자본비율
    if 'total_equity' in accounts and 'total_assets' in accounts:
        if accounts['total_assets']['current'] != 0:
            equity_ratio = (accounts['total_equity']['current'] / accounts['total_assets']['current']) * 100
            ratios['equity_ratio'] = round(equity_ratio, 2)
    
    # 부채비율 (부채/자산)
    if 'total_liabilities' in accounts and 'total_assets' in accounts:
        if accounts['total_assets']['current'] != 0:
            debt_to_assets = (accounts['total_liabilities']['current'] / accounts['total_assets']['current']) * 100
            ratios['debt_to_assets_ratio'] = round(debt_to_assets, 2)
    
    # 4. 성과 지표
    performance = analysis['performance_indicators']
    
    # 총자산 증가율
    if 'total_assets' in accounts and accounts['total_assets']['previous']:
        if accounts['total_assets']['previous'] != 0:
            asset_growth = ((accounts['total_assets']['current'] - accounts['total_assets']['previous']) / accounts['total_assets']['previous']) * 100
            performance['total_assets_growth'] = round(asset_growth, 2)
    
    # 자기자본 증가율
    if 'total_equity' in accounts and accounts['total_equity']['previous']:
        if accounts['total_equity']['previous'] != 0:
            equity_growth = ((accounts['total_equity']['current'] - accounts['total_equity']['previous']) / accounts['total_equity']['previous']) * 100
            performance['equity_growth'] = round(equity_growth, 2)
    
    # 순이익 증가율
    if 'net_income' in accounts and accounts['net_income']['previous']:
        if accounts['net_income']['previous'] != 0:
            income_growth = ((accounts['net_income']['current'] - accounts['net_income']['previous']) / accounts['net_income']['previous']) * 100
            performance['net_income_growth'] = round(income_growth, 2)
    
    return jsonify(analysis)

@app.route('/api/financial/<corp_code>/balance-structure')
def get_balance_structure(corp_code):
    """재무구조 분석 - 자산=부채+자본 등식 시각화"""
    bsns_year = request.args.get('year', str(datetime.now().year - 1))
    reprt_code = request.args.get('report', '11011')
    
    # 재무 데이터 조회
    financial_data = get_financial_statements(corp_code, bsns_year, reprt_code)
    
    if 'error' in financial_data:
        return jsonify(financial_data), 400
    
    if not financial_data.get('list'):
        return jsonify({'error': '조회된 재무 데이터가 없습니다.'}), 400
    
    # 재무구조 분석 결과 초기화
    balance_structure = {
        'company_info': {
            'bsns_year': financial_data['list'][0].get('bsns_year'),
            'stock_code': financial_data['list'][0].get('stock_code'),
            'reprt_code': financial_data['list'][0].get('reprt_code')
        },
        'balance_equation': {
            'total_assets': None,
            'total_liabilities': None,
            'total_equity': None,
            'equation_balance': False
        },
        'asset_composition': {},
        'liability_composition': {},
        'equity_composition': {}
    }
    
    # 재무제표 데이터에서 주요 항목 추출
    assets_items = {}
    liabilities_items = {}
    equity_items = {}
    
    for item in financial_data['list']:
        if item.get('sj_div') != 'BS':  # 재무상태표가 아닌 경우 건너뛰기
            continue
            
        account_name = item.get('account_nm', '').strip()
        current_amount = item.get('thstrm_amount')
        
        if not current_amount or not current_amount.replace(',', '').replace('-', '').isdigit():
            continue
            
        amount = int(current_amount.replace(',', ''))
        
        # 자산 항목들
        if '자산총계' in account_name:
            balance_structure['balance_equation']['total_assets'] = amount
        elif any(keyword in account_name for keyword in ['유동자산', '당좌자산', '현금및현금성자산', '단기금융상품']):
            assets_items['current_assets'] = assets_items.get('current_assets', 0) + amount
        elif any(keyword in account_name for keyword in ['비유동자산', '유형자산', '무형자산', '투자자산']):
            assets_items['non_current_assets'] = assets_items.get('non_current_assets', 0) + amount
        elif '재고자산' in account_name:
            assets_items['inventory'] = amount
        elif '매출채권' in account_name or '수취채권' in account_name:
            assets_items['receivables'] = amount
            
        # 부채 항목들
        elif '부채총계' in account_name:
            balance_structure['balance_equation']['total_liabilities'] = amount
        elif any(keyword in account_name for keyword in ['유동부채', '단기부채']):
            liabilities_items['current_liabilities'] = liabilities_items.get('current_liabilities', 0) + amount
        elif any(keyword in account_name for keyword in ['비유동부채', '장기부채']):
            liabilities_items['non_current_liabilities'] = liabilities_items.get('non_current_liabilities', 0) + amount
        elif '매입채무' in account_name:
            liabilities_items['payables'] = amount
        elif '차입금' in account_name or '대출' in account_name:
            liabilities_items['borrowings'] = liabilities_items.get('borrowings', 0) + amount
            
        # 자본 항목들
        elif '자본총계' in account_name:
            balance_structure['balance_equation']['total_equity'] = amount
        elif '자본금' in account_name:
            equity_items['capital_stock'] = amount
        elif '이익잉여금' in account_name:
            equity_items['retained_earnings'] = amount
        elif '기타포괄손익누계액' in account_name:
            equity_items['other_comprehensive_income'] = amount
    
    # 등식 균형 확인
    total_assets = balance_structure['balance_equation']['total_assets']
    total_liabilities = balance_structure['balance_equation']['total_liabilities']
    total_equity = balance_structure['balance_equation']['total_equity']
    
    if total_assets and total_liabilities and total_equity:
        # 오차 범위 1% 이내로 균형 확인
        calculated_total = total_liabilities + total_equity
        balance_error = abs(total_assets - calculated_total) / total_assets
        balance_structure['balance_equation']['equation_balance'] = balance_error < 0.01
        balance_structure['balance_equation']['balance_error_rate'] = round(balance_error * 100, 4)
    
    # 구성 요소 정리
    balance_structure['asset_composition'] = assets_items
    balance_structure['liability_composition'] = liabilities_items
    balance_structure['equity_composition'] = equity_items
    
    return jsonify(balance_structure)

def generate_ai_analysis(company_name, financial_data, analysis_data, balance_data):
    """Gemini AI를 사용하여 재무 분석 설명 생성"""
    try:
        # Gemini 모델 초기화
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # 수치를 읽기 쉽게 포맷팅하는 함수
        def format_amount(amount):
            if amount is None or amount == 'N/A' or amount == 0:
                return '정보 없음'
            try:
                if abs(amount) >= 1000000000000:  # 1조 이상
                    return f"{amount/1000000000000:.1f}조"
                elif abs(amount) >= 100000000:  # 1억 이상
                    return f"{amount/100000000:.0f}억"
                else:
                    return f"{amount:,}"
            except:
                return '정보 없음'
        
        # 재무 데이터 추출
        key_accounts = financial_data.get('key_accounts', {})
        profitability = analysis_data.get('profitability_analysis', {})
        ratios = analysis_data.get('financial_ratios', {})
        
        # 회사 유형 판단 (금융회사 여부)
        revenue = key_accounts.get('revenue')
        is_financial_company = revenue is None or revenue == 0
        
        # 디버깅: key_accounts 내용 확인
        print(f"key_accounts contents: {key_accounts}")
        
        # 실제 수치 확인 및 명시적 데이터 전달  
        assets = key_accounts.get('assets', 0) if key_accounts else 0
        liabilities = key_accounts.get('liabilities', 0) if key_accounts else 0
        equity = key_accounts.get('equity', 0) if key_accounts else 0
        operating_profit = key_accounts.get('operating_profit', 0) if key_accounts else 0
        net_income = key_accounts.get('net_income', 0) if key_accounts else 0
        
        # 디버깅: AI에게 전달되는 수치 확인
        print(f"AI Prompt values - assets: {assets}, liabilities: {liabilities}, equity: {equity}")
        print(f"AI Prompt values - operating_profit: {operating_profit}, net_income: {net_income}")
        
        # key_accounts가 비어있는 경우 오류 메시지
        if not key_accounts:
            print("WARNING: key_accounts is empty!")
        
        # 안전한 조원 변환 함수
        def safe_to_trillion(amount):
            if amount and amount > 0:
                return f"{amount/1000000000000:.1f}조"
            return "정보없음"
        
        # 재무 데이터를 텍스트로 정리
        if is_financial_company:
            prompt = f"""
다음은 {company_name}의 실제 재무 데이터입니다. 모든 수치는 실제 오픈다트 API에서 조회된 정확한 데이터입니다.

**실제 재무 정보:**
- 자산총계: {assets:,}원 (약 {safe_to_trillion(assets)})
- 부채총계: {liabilities:,}원 (약 {safe_to_trillion(liabilities)})
- 자본총계: {equity:,}원 (약 {safe_to_trillion(equity)})
- 영업수익: {operating_profit:,}원 (약 {safe_to_trillion(operating_profit)})
- 당기순이익: {net_income:,}원 (약 {safe_to_trillion(net_income)})

**중요**: 위의 모든 수치는 실제 데이터이며, 0원이 아닙니다. 
금융업 특성상 매출액 대신 영업수익을 중심으로 분석해주세요."""
        else:
            revenue = key_accounts.get('revenue', 0)
            prompt = f"""
다음은 {company_name}의 실제 재무 데이터입니다. 모든 수치는 실제 오픈다트 API에서 조회된 정확한 데이터입니다.

**실제 재무 정보:**
- 자산총계: {assets:,}원 (약 {safe_to_trillion(assets)})
- 부채총계: {liabilities:,}원 (약 {safe_to_trillion(liabilities)})
- 자본총계: {equity:,}원 (약 {safe_to_trillion(equity)})
- 매출액: {revenue:,}원 (약 {safe_to_trillion(revenue)})
- 영업이익: {operating_profit:,}원 (약 {safe_to_trillion(operating_profit)})
- 당기순이익: {net_income:,}원 (약 {safe_to_trillion(net_income)})

**중요**: 위의 모든 수치는 실제 데이터이며, 0원이 아닙니다."""

        
        # 공통 프롬프트 부분
        prompt += f"""

**계산된 수익성 지표:**
- ROE (자기자본수익률): {profitability.get('roe', 'N/A')}%
- ROA (총자산수익률): {profitability.get('roa', 'N/A')}%

**재무 안정성:**
- 부채비율: {ratios.get('debt_to_equity_ratio', 'N/A')}%
- 자기자본비율: {ratios.get('equity_ratio', 'N/A')}%

다음 관점에서 위에 제공된 실제 재무 데이터를 바탕으로 구체적으로 분석해주시기 바랍니다:
1. 회사 개요: 제공된 실제 재무 데이터를 바탕으로 이 회사의 재무 상태를 종합적으로 평가해주세요.
2. 수익성: 실제 ROE/ROA 수치를 고려하여 수익성을 평가해주세요. {'(금융업 특성 고려)' if is_financial_company else ''}
3. 안정성: 실제 부채비율과 자기자본비율을 바탕으로 재무 안정성을 평가해주세요.
4. 성장성: 현재 실제 재무 수치로 보이는 성장 잠재력을 평가해주세요.
5. 투자 관점: 일반 투자자가 이 실제 수치들을 어떻게 해석해야 하는지 조언해주세요.
6. 주의사항: 실제 재무 수치를 바탕으로 투자 시 주의해야 할 리스크 요인을 분석해주세요.

**중요한 지침**: 
- 위에 제공된 모든 재무 데이터는 실제 수치입니다. 
- "누락된 정보" 또는 "정보 부족"이라는 표현은 사용하지 마세요.
- 제공된 실제 수치를 바탕으로 분석해주세요.
정중하고 전문적인 어조로 작성하되, 일반인도 이해하기 쉽게 설명해주세요. 
각 섹션은 2-3문장으로 간결하게 작성해주세요.
{'금융업의 특성을 고려하여 분석해주세요.' if is_financial_company else ''}
"""

        # AI 분석 생성
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"AI 분석 생성 중 오류가 발생했습니다: {str(e)}"

@app.route('/api/financial/<corp_code>/ai-analysis')
def get_ai_analysis(corp_code):
    """AI 기반 재무 분석 설명"""
    bsns_year = request.args.get('year', str(datetime.now().year - 1))
    reprt_code = request.args.get('report', '11011')
    
    # 회사 정보 조회
    with db_lock:
        cursor = db_conn.cursor()
        cursor.execute('SELECT corp_name FROM corporations WHERE corp_code = ?', (corp_code,))
        corp_result = cursor.fetchone()
        
        if not corp_result:
            return jsonify({'error': '회사 정보를 찾을 수 없습니다.'}), 404
        
        company_name = corp_result[0]
    
    try:
        # 기존 재무 데이터들을 병렬로 조회
        summary_data = get_financial_statements(corp_code, bsns_year, reprt_code)
        if 'error' in summary_data:
            return jsonify({'error': '재무 데이터를 조회할 수 없습니다.'}), 400
        
        # 요약 데이터 생성
        financial_summary = format_financial_data(summary_data)
        if 'error' in financial_summary:
            return jsonify({'error': '재무 데이터 처리에 실패했습니다.'}), 400
        
        # 실제 분석 데이터 생성 (기존 분석 함수 활용)
        analysis_result = {}
        balance_result = {}
        
        # summary 로직을 직접 복사해서 정확한 key_accounts 생성
        key_accounts = {}
        
        # 주요 계정 추출 (summary 엔드포인트와 동일한 로직)
        for item in summary_data.get('list', []):
            account_name = item.get('account_nm', '').strip()
            current_amount = item.get('thstrm_amount')
            
            # 금액 검증 및 변환
            if not current_amount:
                continue
                
            # 음수나 특수문자 처리
            amount_str = str(current_amount).replace(',', '').replace(' ', '')
            if not amount_str.replace('-', '').isdigit():
                continue
                
            try:
                amount = int(amount_str)
            except ValueError:
                continue
            
            # 개별회사 재무제표 (OFS) 우선 처리
            if item.get('fs_div') == 'OFS':
                if '자산총계' in account_name:
                    key_accounts['assets'] = amount
                elif '부채총계' in account_name:
                    key_accounts['liabilities'] = amount
                elif '자본총계' in account_name:
                    key_accounts['equity'] = amount
                elif '매출액' in account_name and '매출원가' not in account_name:
                    key_accounts['revenue'] = amount
                elif '영업이익' in account_name and '영업이익(손실)' not in account_name:
                    key_accounts['operating_profit'] = amount
                elif '영업이익(손실)' in account_name:
                    key_accounts['operating_profit'] = amount
                elif '당기순이익' in account_name and '당기순이익(손실)' not in account_name and '손실' not in account_name:
                    key_accounts['net_income'] = amount
                elif '당기순이익(손실)' in account_name:
                    key_accounts['net_income'] = amount
        
        # 연결재무제표로 보완 (필요한 데이터가 없는 경우)
        for item in summary_data.get('list', []):
            account_name = item.get('account_nm', '').strip()
            current_amount = item.get('thstrm_amount')
            
            if not current_amount:
                continue
                
            amount_str = str(current_amount).replace(',', '').replace(' ', '')
            if not amount_str.replace('-', '').isdigit():
                continue
                
            try:
                amount = int(amount_str)
            except ValueError:
                continue
            
            # 연결재무제표 (CFS) 처리 - 누락된 항목만
            if item.get('fs_div') == 'CFS':
                if '자산총계' in account_name and 'assets' not in key_accounts:
                    key_accounts['assets'] = amount
                elif '부채총계' in account_name and 'liabilities' not in key_accounts:
                    key_accounts['liabilities'] = amount
                elif '자본총계' in account_name and 'equity' not in key_accounts:
                    key_accounts['equity'] = amount
                elif '매출액' in account_name and '매출원가' not in account_name and 'revenue' not in key_accounts:
                    key_accounts['revenue'] = amount
                elif '영업이익' in account_name and '영업이익(손실)' not in account_name and 'operating_profit' not in key_accounts:
                    key_accounts['operating_profit'] = amount
                elif '영업이익(손실)' in account_name and 'operating_profit' not in key_accounts:
                    key_accounts['operating_profit'] = amount
                elif '당기순이익' in account_name and '당기순이익(손실)' not in account_name and '손실' not in account_name and 'net_income' not in key_accounts:
                    key_accounts['net_income'] = amount
                elif '당기순이익(손실)' in account_name and 'net_income' not in key_accounts:
                    key_accounts['net_income'] = amount
        
        # 디버깅용 로그
        print(f"AI Analysis - Extracted key_accounts for {corp_code}: {key_accounts}")
        
        if key_accounts:
            revenue = key_accounts.get('revenue', 0)
            operating_profit = key_accounts.get('operating_profit', 0)
            net_income = key_accounts.get('net_income', 0)
            assets = key_accounts.get('assets', 0)
            equity = key_accounts.get('equity', 0)
            
            # 수익성 지표 계산
            profitability_analysis = {}
            if revenue and revenue != 0:
                profitability_analysis['operating_profit_margin'] = round((operating_profit / revenue) * 100, 2) if operating_profit else 0
                profitability_analysis['net_profit_margin'] = round((net_income / revenue) * 100, 2) if net_income else 0
            
            if assets and assets != 0:
                profitability_analysis['roa'] = round((net_income / assets) * 100, 2) if net_income else 0
                
            if equity and equity != 0:
                profitability_analysis['roe'] = round((net_income / equity) * 100, 2) if net_income else 0
            
            # 재무 비율 계산
            financial_ratios = {}
            if equity and equity != 0:
                debt = key_accounts.get('liabilities', 0)
                financial_ratios['debt_to_equity_ratio'] = round((debt / equity) * 100, 2) if debt else 0
                financial_ratios['equity_ratio'] = round((equity / assets) * 100, 2) if assets else 0
            
            analysis_result = {
                'profitability_analysis': profitability_analysis,
                'financial_ratios': financial_ratios,
                'revenue_analysis': {
                    'current_revenue': revenue,
                    'revenue_growth_rate': 0  # 전년 대비 데이터가 없어서 0으로 설정
                }
            }
        
        # AI 분석 생성 (계산된 분석 데이터 포함)
        ai_analysis = generate_ai_analysis(
            company_name, 
            {'key_accounts': key_accounts},  # key_accounts를 직접 전달
            analysis_result, 
            balance_result
        )
        
        return jsonify({
            'company_name': company_name,
            'analysis_year': bsns_year,
            'report_type': reprt_code,
            'ai_analysis': ai_analysis,
            'financial_data': financial_summary,  # 디버깅용 데이터 추가
            'analysis_data': analysis_result,  # 계산된 분석 데이터 추가
            'generated_at': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': f'AI 분석 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@app.route('/api/financial/<corp_code>/ai-summary')
def get_ai_summary(corp_code):
    """AI 기반 간단한 재무 요약"""
    bsns_year = request.args.get('year', str(datetime.now().year - 1))
    reprt_code = request.args.get('report', '11011')
    
    # 회사 정보 조회
    with db_lock:
        cursor = db_conn.cursor()
        cursor.execute('SELECT corp_name FROM corporations WHERE corp_code = ?', (corp_code,))
        corp_result = cursor.fetchone()
        
        if not corp_result:
            return jsonify({'error': '회사 정보를 찾을 수 없습니다.'}), 404
        
        company_name = corp_result[0]
    
    try:
        # 기본 재무 데이터 조회
        summary_data = get_financial_statements(corp_code, bsns_year, reprt_code)
        if 'error' in summary_data:
            return jsonify({'error': '재무 데이터를 조회할 수 없습니다.'}), 400
        
        financial_summary = format_financial_data(summary_data)
        if 'error' in financial_summary:
            return jsonify({'error': '재무 데이터 처리에 실패했습니다.'}), 400
        
        # 간단한 AI 요약 생성
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # summary 로직과 동일하게 key_accounts 추출
        key_accounts = {}
        
        # 주요 계정 추출
        for item in summary_data.get('list', []):
            account_name = item.get('account_nm', '').strip()
            current_amount = item.get('thstrm_amount')
            
            if not current_amount or not current_amount.replace(',', '').replace('-', '').isdigit():
                continue
                
            amount = int(current_amount.replace(',', ''))
            
            # 개별회사 재무제표 (OFS) 우선
            if item.get('fs_div') == 'OFS':
                if '자산총계' in account_name:
                    key_accounts['assets'] = amount
                elif '부채총계' in account_name:
                    key_accounts['liabilities'] = amount
                elif '자본총계' in account_name:
                    key_accounts['equity'] = amount
                elif '매출액' in account_name and '매출원가' not in account_name:
                    key_accounts['revenue'] = amount
                elif '영업이익' in account_name and '영업이익(손실)' not in account_name:
                    key_accounts['operating_profit'] = amount
                elif '영업이익(손실)' in account_name:
                    key_accounts['operating_profit'] = amount
                elif '당기순이익' in account_name and '당기순이익(손실)' not in account_name and '손실' not in account_name:
                    key_accounts['net_income'] = amount
                elif '당기순이익(손실)' in account_name:
                    key_accounts['net_income'] = amount
        
        # 연결재무제표로 보완 (OFS 데이터가 없는 경우)
        if not key_accounts:
            for item in summary_data.get('list', []):
                account_name = item.get('account_nm', '').strip()
                current_amount = item.get('thstrm_amount')
                
                if not current_amount or not current_amount.replace(',', '').replace('-', '').isdigit():
                    continue
                    
                amount = int(current_amount.replace(',', ''))
                
                if item.get('fs_div') == 'CFS':
                    if '자산총계' in account_name and 'assets' not in key_accounts:
                        key_accounts['assets'] = amount
                    elif '부채총계' in account_name and 'liabilities' not in key_accounts:
                        key_accounts['liabilities'] = amount
                    elif '자본총계' in account_name and 'equity' not in key_accounts:
                        key_accounts['equity'] = amount
                    elif '매출액' in account_name and '매출원가' not in account_name and 'revenue' not in key_accounts:
                        key_accounts['revenue'] = amount
                    elif '영업이익' in account_name and '영업이익(손실)' not in account_name and 'operating_profit' not in key_accounts:
                        key_accounts['operating_profit'] = amount
                    elif '영업이익(손실)' in account_name and 'operating_profit' not in key_accounts:
                        key_accounts['operating_profit'] = amount
                    elif '당기순이익' in account_name and '당기순이익(손실)' not in account_name and '손실' not in account_name and 'net_income' not in key_accounts:
                        key_accounts['net_income'] = amount
                    elif '당기순이익(손실)' in account_name and 'net_income' not in key_accounts:
                        key_accounts['net_income'] = amount
        
        # 수치를 읽기 쉽게 포맷팅
        def format_for_ai(amount):
            if amount is None or amount == 'N/A':
                return 'N/A'
            try:
                if abs(amount) >= 1000000000000:  # 1조 이상
                    return f"{amount/1000000000000:.1f}조"
                elif abs(amount) >= 100000000:  # 1억 이상
                    return f"{amount/100000000:.0f}억"
                else:
                    return f"{amount:,}"
            except:
                return str(amount)
        
        revenue_str = format_for_ai(key_accounts.get('revenue'))
        net_income_str = format_for_ai(key_accounts.get('net_income'))
        assets_str = format_for_ai(key_accounts.get('assets'))
        operating_profit_str = format_for_ai(key_accounts.get('operating_profit'))
        
        prompt = f"""
{company_name}의 {bsns_year}년 재무 상태를 3-4문장으로 정중하게 요약해주시기 바랍니다.

주요 수치:
- 매출액: {revenue_str}원
- 영업이익: {operating_profit_str}원
- 순이익: {net_income_str}원  
- 총자산: {assets_str}원

일반인이 이해하기 쉽게, 전문적이면서도 정중한 어조로 작성해주세요.
수치의 의미와 회사의 재무 건전성에 대해 존댓말로 간단히 설명해주시기 바랍니다.
"""
        
        response = model.generate_content(prompt)
        
        return jsonify({
            'company_name': company_name,
            'summary': response.text,
            'key_metrics': key_accounts,
            'financial_data': financial_summary  # 디버깅을 위해 전체 데이터도 포함
        })
        
    except Exception as e:
        return jsonify({'error': f'AI 요약 생성 중 오류가 발생했습니다: {str(e)}'}), 500

if __name__ == '__main__':
    # 데이터 로드를 별도 스레드에서 실행
    load_thread = threading.Thread(target=load_corp_data, args=(db_conn,))
    load_thread.start()
    
    print("🚀 오픈다트 재무 데이터 분석 서비스가 http://localhost:8080 에서 실행 중입니다.")
    print("📊 메인 페이지: http://localhost:8080")
    print("🔍 API 상태: http://localhost:8080/api/corporations/health")
    
    # 배포 환경에서는 포트를 환경 변수에서 가져옴
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
