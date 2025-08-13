#!/usr/bin/env python3
"""
PiCalendar テーマ管理システム
"""

import os
import sys
import yaml
from pathlib import Path
import shutil
from typing import Dict, List, Optional

class ThemeManager:
    """テーマ管理クラス"""
    
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.themes_dir = self.base_dir / "themes"
        self.settings_file = self.base_dir / "settings.yaml"
        self.settings_backup = self.base_dir / "settings.yaml.backup"
        
    def list_themes(self) -> List[Dict]:
        """利用可能なテーマ一覧を取得"""
        themes = []
        if not self.themes_dir.exists():
            return themes
            
        for theme_file in self.themes_dir.glob("*.yaml"):
            try:
                with open(theme_file, 'r', encoding='utf-8') as f:
                    theme_data = yaml.safe_load(f)
                    themes.append({
                        'file': theme_file.stem,
                        'name': theme_data.get('name', theme_file.stem),
                        'description': theme_data.get('description', ''),
                        'path': theme_file
                    })
            except Exception as e:
                print(f"Error loading theme {theme_file}: {e}")
                
        return sorted(themes, key=lambda x: x['name'])
    
    def load_theme(self, theme_name: str) -> Optional[Dict]:
        """テーマを読み込み"""
        theme_file = self.themes_dir / f"{theme_name}.yaml"
        if not theme_file.exists():
            print(f"Theme not found: {theme_name}")
            return None
            
        try:
            with open(theme_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading theme: {e}")
            return None
    
    def apply_theme(self, theme_name: str, keep_location: bool = True) -> bool:
        """テーマを適用"""
        theme_data = self.load_theme(theme_name)
        if not theme_data:
            return False
            
        # 現在の設定をバックアップ
        if self.settings_file.exists():
            shutil.copy2(self.settings_file, self.settings_backup)
            print(f"Backed up current settings to {self.settings_backup}")
            
            # 場所の設定を保持する場合
            if keep_location:
                try:
                    with open(self.settings_file, 'r', encoding='utf-8') as f:
                        current_settings = yaml.safe_load(f) or {}
                    
                    # 天気の場所設定を保持
                    if 'weather' in current_settings and 'location' in current_settings['weather']:
                        if 'weather' not in theme_data:
                            theme_data['weather'] = {}
                        theme_data['weather']['location'] = current_settings['weather']['location']
                except:
                    pass
        
        # テーマ情報を追加
        theme_data['theme'] = {
            'name': theme_name,
            'applied_from': theme_data.get('name', theme_name)
        }
        
        # 設定を保存
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                yaml.dump(theme_data, f, default_flow_style=False, allow_unicode=True)
            print(f"Applied theme: {theme_data.get('name', theme_name)}")
            return True
        except Exception as e:
            print(f"Error applying theme: {e}")
            return False
    
    def create_theme_from_current(self, name: str, description: str = "") -> bool:
        """現在の設定からテーマを作成"""
        if not self.settings_file.exists():
            print("No current settings found")
            return False
            
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                current_settings = yaml.safe_load(f) or {}
            
            # テーマメタデータを追加
            current_settings['name'] = name
            current_settings['description'] = description
            
            # テーマファイルとして保存
            theme_file = self.themes_dir / f"{name.lower().replace(' ', '_')}.yaml"
            with open(theme_file, 'w', encoding='utf-8') as f:
                yaml.dump(current_settings, f, default_flow_style=False, allow_unicode=True)
            
            print(f"Created theme: {theme_file}")
            return True
        except Exception as e:
            print(f"Error creating theme: {e}")
            return False
    
    def get_current_theme(self) -> Optional[str]:
        """現在適用されているテーマを取得"""
        if not self.settings_file.exists():
            return None
            
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = yaml.safe_load(f) or {}
            return settings.get('theme', {}).get('name')
        except:
            return None


def main():
    """CLI インターフェース"""
    import argparse
    
    parser = argparse.ArgumentParser(description='PiCalendar Theme Manager')
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # list コマンド
    subparsers.add_parser('list', help='List available themes')
    
    # apply コマンド
    apply_parser = subparsers.add_parser('apply', help='Apply a theme')
    apply_parser.add_argument('theme', help='Theme name to apply')
    apply_parser.add_argument('--no-keep-location', action='store_true', 
                            help='Do not keep current location settings')
    
    # current コマンド
    subparsers.add_parser('current', help='Show current theme')
    
    # create コマンド
    create_parser = subparsers.add_parser('create', help='Create theme from current settings')
    create_parser.add_argument('name', help='Name for the new theme')
    create_parser.add_argument('-d', '--description', default='', help='Theme description')
    
    args = parser.parse_args()
    
    manager = ThemeManager()
    
    if args.command == 'list':
        themes = manager.list_themes()
        if not themes:
            print("No themes found")
        else:
            print("\n利用可能なテーマ:")
            print("-" * 60)
            for theme in themes:
                print(f"  {theme['file']:15} - {theme['name']}")
                if theme['description']:
                    print(f"  {'':15}   {theme['description']}")
            print()
            
    elif args.command == 'apply':
        success = manager.apply_theme(args.theme, not args.no_keep_location)
        if success:
            print("\n✅ テーマを適用しました")
            print("   再起動して反映してください: ./quick_restart.sh")
        else:
            print("\n❌ テーマの適用に失敗しました")
            sys.exit(1)
            
    elif args.command == 'current':
        current = manager.get_current_theme()
        if current:
            print(f"現在のテーマ: {current}")
        else:
            print("テーマが設定されていません（デフォルト設定を使用中）")
            
    elif args.command == 'create':
        success = manager.create_theme_from_current(args.name, args.description)
        if success:
            print("\n✅ テーマを作成しました")
        else:
            print("\n❌ テーマの作成に失敗しました")
            sys.exit(1)
            
    else:
        parser.print_help()


if __name__ == "__main__":
    main()