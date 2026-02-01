#!/usr/bin/env python3
"""
Enhanced Repository 기능 검증 스크립트 (수정 버전)
"""

import sys
sys.path.append('src')

import pytest

from runtime.data.repositories.enhanced_portfolio_repository import EnhancedPortfolioRepository
from runtime.data.repositories.enhanced_performance_repository import EnhancedPerformanceRepository
from runtime.data.repositories.schema_based_repository import SchemaBasedRepository
import gspread
import os
from dotenv import load_dotenv
from pathlib import Path

@pytest.mark.live_sheets
def test_schema_loader():
    """Schema Loader 테스트"""
    print('🔧 Schema Loader 테스트:')
    print('=' * 40)
    
    try:
        # 환경 변수 로드
        load_dotenv()
        
        # Schema Loader 초기화
        from runtime.config.schema_loader import get_schema_loader
        
        project_root = Path('.')
        schema_loader = get_schema_loader(project_root)
        
        # 스키마 로드
        schema = schema_loader.load_schema()
        print(f'✅ 스키마 로드 성공')
        print(f'   버전: {schema.get("schema_version", "N/A")}')
        
        # 시트 설정 조회
        sheet_configs = schema_loader.get_all_sheet_configs()
        print(f'   시트 수: {len(sheet_configs)}')
        
        for sheet_key, config in sheet_configs.items():
            print(f'   - {sheet_key}: {config.sheet_name} ({config.sheet_type})')
        
        # 필드 매핑 테스트
        portfolio_mapping = schema_loader.get_field_mapping('Portfolio')
        print(f'   Portfolio 필드 매핑: {len(portfolio_mapping)}개')
        
        performance_mapping = schema_loader.get_field_mapping('Performance')
        print(f'   Performance 필드 매핑: {len(performance_mapping)}개')
        
        assert len(portfolio_mapping) > 0
        assert len(performance_mapping) > 0
        
    except Exception as e:
        pytest.fail(f"Schema Loader 테스트 실패: {e}")

@pytest.mark.live_sheets
def test_enhanced_portfolio_repository():
    """Enhanced Portfolio Repository 테스트"""
    print('\n🎯 Enhanced Portfolio Repository 테스트:')
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
        gs_client.gspread_client = gc
        
        # Enhanced Portfolio Repository 초기화
        project_root = Path('.')
        portfolio_repo = EnhancedPortfolioRepository(gs_client, os.getenv('GOOGLE_SHEET_KEY'), project_root)
        
        # 스키마 기반 테스트
        print('📋 스키마 정보:')
        print(f'   시트명: {portfolio_repo.sheet_config.sheet_name}')
        print(f'   시트 타입: {portfolio_repo.sheet_config.sheet_type}')
        print(f'   필드 매핑 수: {len(portfolio_repo.get_field_mapping())}')
        
        # 구조 검증
        validation_result = portfolio_repo.validate_portfolio_structure()
        validation_success = validation_result.get('valid', False)
        print(f'   구조 검증: {"성공" if validation_success else "실패"}')
        
        # KPI 데이터 조회 (스키마 기반)
        current_kpi = portfolio_repo.get_kpi_overview()
        print(f'   KPI 필드 수: {len(current_kpi)}')
        
        # KPI 업데이트 테스트
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
        
        assert portfolio_repo.sheet_config.sheet_name
        assert len(portfolio_repo.get_field_mapping()) > 0
        
    except Exception as e:
        pytest.fail(f"Enhanced Portfolio Repository 테스트 실패: {e}")

@pytest.mark.live_sheets
def test_enhanced_performance_repository():
    """Enhanced Performance Repository 테스트"""
    print('\n🎯 Enhanced Performance Repository 테스트:')
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
        gs_client.gspread_client = gc
        
        # Enhanced Performance Repository 초기화
        project_root = Path('.')
        performance_repo = EnhancedPerformanceRepository(gs_client, os.getenv('GOOGLE_SHEET_KEY'), project_root)
        
        # 스키마 기반 테스트
        print('📋 스키마 정보:')
        print(f'   시트명: {performance_repo.sheet_config.sheet_name}')
        print(f'   시트 타입: {performance_repo.sheet_config.sheet_type}')
        print(f'   필드 매핑 수: {len(performance_repo.get_field_mapping())}')
        
        # 구조 검증
        validation_result = performance_repo.validate_performance_structure()
        validation_success = validation_result.get('valid', False)
        print(f'   구조 검증: {"성공" if validation_success else "실패"}')
        
        # KPI 데이터 조회 (스키마 기반)
        current_kpi = performance_repo.get_kpi_summary()
        print(f'   KPI 필드 수: {len(current_kpi)}')
        
        # KPI 업데이트 테스트
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
        
        assert performance_repo.sheet_config.sheet_name
        assert isinstance(performance_repo.get_kpi_summary(), dict)
        
    except Exception as e:
        pytest.fail(f"Enhanced Performance Repository 테스트 실패: {e}")

def main():
    """메인 테스트 함수"""
    print('🧪 Enhanced Repository 기능 검증 시작')
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
        
        # Schema Loader 테스트
        schema_success = test_schema_loader()
        
        # Enhanced Portfolio Repository 테스트
        portfolio_success = test_enhanced_portfolio_repository()
        
        # Enhanced Performance Repository 테스트
        performance_success = test_enhanced_performance_repository()
        
        # 최종 결과
        print('\n' + '=' * 50)
        print('🎉 테스트 결과:')
        print(f'Schema Loader: {"✅ 성공" if schema_success else "❌ 실패"}')
        print(f'Enhanced Portfolio Repository: {"✅ 성공" if portfolio_success else "❌ 실패"}')
        print(f'Enhanced Performance Repository: {"✅ 성공" if performance_success else "❌ 실패"}')
        
        if schema_success and portfolio_success and performance_success:
            print('\n🎯 모든 Enhanced Repository 기능이 정상적으로 동작합니다!')
        else:
            print('\n⚠️ 일부 기능에 문제가 있습니다. 로그를 확인하세요.')
        
    except Exception as e:
        print(f'❌ 전체 테스트 실패: {e}')

if __name__ == "__main__":
    main()
