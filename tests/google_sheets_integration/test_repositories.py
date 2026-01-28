#!/usr/bin/env python3
"""
Portfolio 및 Performance 리포지토리 기능 검증 스크립트
"""

import sys
sys.path.append('src')

from runtime.data.repositories.enhanced_portfolio_repository import EnhancedPortfolioRepository
from runtime.data.repositories.enhanced_performance_repository import EnhancedPerformanceRepository
import gspread
import os
from dotenv import load_dotenv

def test_portfolio_repository():
    """Portfolio 리포지토리 테스트"""
    print('🎯 Portfolio Repository 테스트:')
    print('=' * 40)
    
    try:
        # 환경 변수 로드
        load_dotenv()
        
        # Google Sheets 클라이언트 생성
        gc = gspread.service_account(
            filename=os.getenv('GOOGLE_CREDENTIALS_FILE'),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        spreadsheet = gc.open_by_key(os.getenv('GOOGLE_SHEET_KEY'))
        
        # GoogleSheetsClient 래퍼 생성
        from runtime.data.google_sheets_client import GoogleSheetsClient
        gs_client = GoogleSheetsClient()
        gs_client.gspread_client = gc  # 직접 클라이언트 설정
        
        # Portfolio 리포지토리 초기화
        portfolio_repo = PortfolioRepository(gs_client, os.getenv('GOOGLE_SHEET_KEY'))
        
        # 현재 KPI 데이터 조회
        current_kpi = portfolio_repo.get_kpi_overview()
        print('📊 현재 KPI 데이터:')
        for key, value in current_kpi.items():
            print(f'  {key}: {value}')
        
        # KPI 업데이트 테스트 (샘플 데이터)
        test_kpi_data = {
            'total_equity': 1000000.0,
            'daily_pnl': 5000.0,
            'exposure': 0.75,
            'cash_ratio': 0.25,
            'holdings_count': 15,
            'killswitch_status': 'ACTIVE'
        }
        
        print('\n🔄 KPI 업데이트 테스트...')
        update_result = portfolio_repo.update_kpi_overview(test_kpi_data)
        print(f'업데이트 결과: {"성공" if update_result else "실패"}')
        
        # 업데이트된 데이터 확인
        updated_kpi = portfolio_repo.get_kpi_overview()
        print('\n📊 업데이트된 KPI 데이터:')
        for key, value in updated_kpi.items():
            print(f'  {key}: {value}')
        
        return True
        
    except Exception as e:
        print(f'❌ Portfolio Repository 테스트 실패: {e}')
        return False

def test_performance_repository():
    """Performance 리포지토리 테스트"""
    print('\n🎯 Performance Repository 테스트:')
    print('=' * 40)
    
    try:
        # 환경 변수 로드
        load_dotenv()
        
        # Google Sheets 클라이언트 생성
        gc = gspread.service_account(
            filename=os.getenv('GOOGLE_CREDENTIALS_FILE'),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        spreadsheet = gc.open_by_key(os.getenv('GOOGLE_SHEET_KEY'))
        
        # GoogleSheetsClient 래퍼 생성
        from runtime.data.google_sheets_client import GoogleSheetsClient
        gs_client = GoogleSheetsClient()
        gs_client.gspread_client = gc  # 직접 클라이언트 설정
        
        # Performance 리포지토리 초기화
        performance_repo = PerformanceRepository(gs_client, os.getenv('GOOGLE_SHEET_KEY'))
        
        # 현재 KPI 데이터 조회
        current_performance_kpi = performance_repo.get_kpi_summary()
        print('📊 현재 Performance KPI 데이터:')
        for key, value in current_performance_kpi.items():
            print(f'  {key}: {value}')
        
        # KPI 업데이트 테스트 (샘플 데이터)
        test_performance_kpi = {
            'total_return': 0.15,
            'mdd': -0.08,
            'daily_vol': 0.02,
            'sharpe': 1.25,
            'win_rate': 0.65,
            'avg_win': 1500.0,
            'avg_loss': -800.0
        }
        
        print('\n🔄 Performance KPI 업데이트 테스트...')
        update_result = performance_repo.update_kpi_summary(test_performance_kpi)
        print(f'업데이트 결과: {"성공" if update_result else "실패"}')
        
        # 업데이트된 데이터 확인
        updated_kpi = performance_repo.get_kpi_summary()
        print('\n📊 업데이트된 Performance KPI 데이터:')
        for key, value in updated_kpi.items():
            print(f'  {key}: {value}')
        
        # Summary Table 데이터 조회
        summary_data = performance_repo.get_summary_table()
        print(f'\n📋 Summary Table 데이터: {len(summary_data)}개 레코드')
        if summary_data:
            print('최근 3개 레코드:')
            for i, record in enumerate(summary_data[-3:], 1):
                date_str = record.get('date', 'N/A')
                pnl_val = record.get('daily_pnl', 0)
                print(f'  {i}. {date_str}: PnL={pnl_val}')
        
        # Summary Table 업데이트 테스트 (샘플 데이터)
        test_summary_data = [
            {
                'date': '2025-01-24',
                'daily_pnl': 5000.0,
                'cum_pnl': 150000.0,
                'return_pct': 0.015,
                'mdd': -0.08,
                'exposure': 0.75,
                'drawdown': -0.02,
                'notes': 'Test data'
            }
        ]
        
        print('\n🔄 Summary Table 업데이트 테스트...')
        summary_update_result = performance_repo.update_summary_table(test_summary_data)
        print(f'업데이트 결과: {"성공" if summary_update_result else "실패"}')
        
        return True
        
    except Exception as e:
        print(f'❌ Performance Repository 테스트 실패: {e}')
        return False

def main():
    """메인 테스트 함수"""
    print('🧪 Repository 기능 검증 시작')
    print('=' * 50)
    
    try:
        # Google Sheets 연결 테스트
        load_dotenv()
        gc = gspread.service_account(
            filename=os.getenv('GOOGLE_CREDENTIALS_FILE'),
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        spreadsheet = gc.open_by_key(os.getenv('GOOGLE_SHEET_KEY'))
        
        print('✅ Google Sheets 연결 성공')
        print(f'📋 스프레드시트: {spreadsheet.title}')
        
        # Portfolio 리포지토리 테스트
        portfolio_success = test_portfolio_repository()
        
        # Performance 리포지토리 테스트
        performance_success = test_performance_repository()
        
        # 최종 결과
        print('\n' + '=' * 50)
        print('🎉 테스트 결과:')
        print(f'Portfolio Repository: {"✅ 성공" if portfolio_success else "❌ 실패"}')
        print(f'Performance Repository: {"✅ 성공" if performance_success else "❌ 실패"}')
        
        if portfolio_success and performance_success:
            print('\n🎯 모든 리포지토리 기능이 정상적으로 동작합니다!')
        else:
            print('\n⚠️ 일부 기능에 문제가 있습니다. 로그를 확인하세요.')
        
    except Exception as e:
        print(f'❌ 전체 테스트 실패: {e}')

if __name__ == "__main__":
    main()
