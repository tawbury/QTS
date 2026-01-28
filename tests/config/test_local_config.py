#!/usr/bin/env python3
"""
Local Config 테스트
"""

import pytest
import json
import tempfile
from pathlib import Path

from runtime.config.local_config import load_local_config, validate_local_config_entries
from runtime.config.config_models import ConfigScope, ConfigEntry


class TestLocalConfig:
    """LocalConfig 테스트 클래스"""
    
    def test_load_local_config_success(self):
        """Local Config 로드 성공 테스트"""
        # 임시 디렉토리와 파일 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_dir = project_root / "config" / "local"
            config_dir.mkdir(parents=True)
            
            # 테스트용 config 파일 생성
            config_data = [
                {
                    "category": "SYSTEM",
                    "subcategory": "BROKER",
                    "key": "API_ENDPOINT",
                    "value": "https://api.koreainvestment.com",
                    "description": "KIS API 기본 엔드포인트",
                    "tag": "broker"
                },
                {
                    "category": "SYSTEM",
                    "subcategory": "RISK",
                    "key": "MAX_POSITION_SIZE",
                    "value": "10000000",
                    "description": "최대 포지션 크기 (원)",
                    "tag": "risk"
                }
            ]
            
            config_file = config_dir / "config_local.json"
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            # 로드 테스트
            result = load_local_config(project_root)
            
            assert result.ok is True
            assert result.scope == ConfigScope.LOCAL
            assert len(result.entries) == 2
            assert result.error is None
            assert result.source_path == str(config_file)
            
            # 첫 번째 엔트리 확인
            entry1 = result.entries[0]
            assert entry1.category == "SYSTEM"
            assert entry1.subcategory == "BROKER"
            assert entry1.key == "API_ENDPOINT"
            assert entry1.value == "https://api.koreainvestment.com"
    
    def test_load_local_config_file_not_found(self):
        """파일 없을 때 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            
            result = load_local_config(project_root)
            
            assert result.ok is False
            assert result.scope == ConfigScope.LOCAL
            assert len(result.entries) == 0
            assert "file not found" in result.error.lower()
    
    def test_load_local_config_empty_file(self):
        """빈 파일 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_dir = project_root / "config" / "local"
            config_dir.mkdir(parents=True)
            
            config_file = config_dir / "config_local.json"
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump([], f)
            
            result = load_local_config(project_root)
            
            assert result.ok is True
            assert result.scope == ConfigScope.LOCAL
            assert len(result.entries) == 0
            assert result.error is None
    
    def test_load_local_config_invalid_json(self):
        """잘못된 JSON 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_dir = project_root / "config" / "local"
            config_dir.mkdir(parents=True)
            
            config_file = config_dir / "config_local.json"
            with open(config_file, "w", encoding="utf-8") as f:
                f.write("{ invalid json")
            
            result = load_local_config(project_root)
            
            assert result.ok is False
            assert result.scope == ConfigScope.LOCAL
            assert len(result.entries) == 0
            assert "invalid json" in result.error.lower()
    
    def test_load_local_config_not_array(self):
        """JSON이 배열이 아닐 때 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_dir = project_root / "config" / "local"
            config_dir.mkdir(parents=True)
            
            config_file = config_dir / "config_local.json"
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump({"key": "value"}, f)
            
            result = load_local_config(project_root)
            
            assert result.ok is False
            assert result.scope == ConfigScope.LOCAL
            assert len(result.entries) == 0
            assert "must be a json array" in result.error.lower()
    
    def test_load_local_config_invalid_entry(self):
        """잘못된 엔트리 테스트"""
        with tempfile.TemporaryDirectory() as temp_dir:
            project_root = Path(temp_dir)
            config_dir = project_root / "config" / "local"
            config_dir.mkdir(parents=True)
            
            config_data = [
                {
                    "category": "SYSTEM",
                    "subcategory": "BROKER",
                    "key": "API_ENDPOINT",
                    "value": "https://api.koreainvestment.com",
                    "description": "KIS API 기본 엔드포인트",
                    "tag": "broker"
                },
                "invalid_entry"  # 문자열이 아닌 엔트리
            ]
            
            config_file = config_dir / "config_local.json"
            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config_data, f, ensure_ascii=False, indent=2)
            
            result = load_local_config(project_root)
            
            assert result.ok is False
            assert result.scope == ConfigScope.LOCAL
            assert len(result.entries) == 0
            assert "not a dict" in result.error.lower()
    
    def test_validate_local_config_entries_success(self):
        """Config 엔트리 검증 성공 테스트"""
        entries = [
            ConfigEntry(
                category="SYSTEM",
                subcategory="BROKER",
                key="API_ENDPOINT",
                value="https://api.koreainvestment.com",
                description="KIS API 기본 엔드포인트",
                tag="broker"
            ),
            ConfigEntry(
                category="RISK",
                subcategory="LIMITS",
                key="MAX_POSITION_SIZE",
                value="10000000",
                description="최대 포지션 크기",
                tag="risk"
            )
        ]
        
        is_valid, error = validate_local_config_entries(entries)
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_local_config_entries_empty_category(self):
        """빈 카테고리 테스트"""
        entries = [
            ConfigEntry(
                category="",
                subcategory="BROKER",
                key="API_ENDPOINT",
                value="https://api.koreainvestment.com",
                description="KIS API 기본 엔드포인트",
                tag="broker"
            )
        ]
        
        is_valid, error = validate_local_config_entries(entries)
        
        assert is_valid is False
        assert "category is empty" in error.lower()
    
    def test_validate_local_config_entries_empty_subcategory(self):
        """빈 서브카테고리 테스트"""
        entries = [
            ConfigEntry(
                category="SYSTEM",
                subcategory="",
                key="API_ENDPOINT",
                value="https://api.koreainvestment.com",
                description="KIS API 기본 엔드포인트",
                tag="broker"
            )
        ]
        
        is_valid, error = validate_local_config_entries(entries)
        
        assert is_valid is False
        assert "subcategory is empty" in error.lower()
    
    def test_validate_local_config_entries_empty_key(self):
        """빈 키 테스트"""
        entries = [
            ConfigEntry(
                category="SYSTEM",
                subcategory="BROKER",
                key="",
                value="https://api.koreainvestment.com",
                description="KIS API 기본 엔드포인트",
                tag="broker"
            )
        ]
        
        is_valid, error = validate_local_config_entries(entries)
        
        assert is_valid is False
        assert "key is empty" in error.lower()
    
    def test_load_actual_project_config(self):
        """실제 프로젝트 config 로드 테스트"""
        # 실제 프로젝트 경로에서 테스트
        project_root = Path("d:/development/QTS")
        
        result = load_local_config(project_root)
        
        if result.ok:
            assert len(result.entries) > 0
            assert result.scope == ConfigScope.LOCAL
            
            # 필수 카테고리 확인
            categories = {entry.category for entry in result.entries}
            assert "SYSTEM" in categories
            
            # 필수 서브카테고리 확인
            subcategories = {entry.subcategory for entry in result.entries}
            assert any(sub in subcategories for sub in ["BROKER", "RISK", "SAFETY"])
            
            # 검증
            is_valid, error = validate_local_config_entries(result.entries)
            assert is_valid, f"Validation failed: {error}"
        else:
            # 파일이 없는 경우도 테스트
            assert "file not found" in result.error.lower()


if __name__ == "__main__":
    pytest.main([__file__])
