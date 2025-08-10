# TASK-103: アセット管理システム - 要件定義

## 概要
PiCalendarアプリケーションで使用するフォント、画像、スプライトなどのアセットを効率的に管理するシステムを実装する。
キャッシュ機能により高速アクセスを実現し、動的リロードによる開発効率の向上を図る。

## 機能要件

### 1. フォント管理
- TrueType/OpenTypeフォントの読み込み
- 複数サイズの管理
- 日本語フォント対応（Noto Sans CJK等）
- システムフォントへのフォールバック
- フォントメトリクスの取得

### 2. 画像管理
- 静止画の読み込み（PNG, JPG, BMP）
- 透過画像のサポート
- サイズ変換とスケーリング
- 回転・反転処理
- カラーキー設定

### 3. スプライトシート管理
- スプライトシートの分割
- アニメーションフレーム管理
- フレームインデックス計算
- メタデータサポート（JSON）
- 自動トリミング

### 4. キャッシュ管理
- メモリキャッシュ
- LRU（Least Recently Used）アルゴリズム
- キャッシュサイズ制限
- 手動パージ機能
- ヒット率統計

### 5. 動的リロード
- ファイル変更監視
- ホットリロード
- 開発モード限定
- 変更通知コールバック
- 自動キャッシュ更新

### 6. パス管理
- 相対パス・絶対パス対応
- ベースディレクトリ設定
- パス正規化
- クロスプラットフォーム対応
- アセットディレクトリ構造

## 技術仕様

### クラス設計

```python
class AssetManager:
    """アセット管理の中央クラス"""
    
    def __init__(self, base_path: str = "assets"):
        """初期化"""
        
    def load_font(self, name: str, size: int) -> pygame.font.Font:
        """フォント読み込み"""
        
    def load_image(self, path: str, alpha: bool = True) -> pygame.Surface:
        """画像読み込み"""
        
    def load_sprite_sheet(self, path: str, frame_size: Tuple[int, int]) -> SpriteSheet:
        """スプライトシート読み込み"""
        
    def preload(self, manifest: Dict[str, Any]) -> None:
        """事前読み込み"""
        
    def clear_cache(self) -> None:
        """キャッシュクリア"""
        
    def get_stats(self) -> Dict[str, Any]:
        """統計情報取得"""

class FontManager:
    """フォント管理"""
    
    def __init__(self, base_path: str):
        """初期化"""
        
    def load(self, font_path: str, size: int) -> pygame.font.Font:
        """フォント読み込み"""
        
    def get_system_font(self, name: str, size: int) -> pygame.font.Font:
        """システムフォント取得"""
        
    def render_text(self, font: pygame.font.Font, text: str, 
                    color: Tuple[int, int, int], antialias: bool = True) -> pygame.Surface:
        """テキストレンダリング"""

class ImageLoader:
    """画像読み込み"""
    
    def __init__(self, base_path: str):
        """初期化"""
        
    def load(self, path: str, alpha: bool = True) -> pygame.Surface:
        """画像読み込み"""
        
    def scale(self, surface: pygame.Surface, size: Tuple[int, int]) -> pygame.Surface:
        """スケーリング"""
        
    def rotate(self, surface: pygame.Surface, angle: float) -> pygame.Surface:
        """回転"""
        
    def flip(self, surface: pygame.Surface, x: bool, y: bool) -> pygame.Surface:
        """反転"""

class SpriteSheet:
    """スプライトシート"""
    
    def __init__(self, surface: pygame.Surface, frame_size: Tuple[int, int]):
        """初期化"""
        
    def get_frame(self, index: int) -> pygame.Surface:
        """フレーム取得"""
        
    def get_frames(self, indices: List[int]) -> List[pygame.Surface]:
        """複数フレーム取得"""
        
    def get_animation(self, start: int, end: int) -> List[pygame.Surface]:
        """アニメーション取得"""
        
    @property
    def frame_count(self) -> int:
        """総フレーム数"""

class AssetCache:
    """キャッシュ管理"""
    
    def __init__(self, max_size: int = 100):
        """初期化"""
        
    def get(self, key: str) -> Optional[Any]:
        """キャッシュ取得"""
        
    def put(self, key: str, value: Any) -> None:
        """キャッシュ追加"""
        
    def remove(self, key: str) -> None:
        """キャッシュ削除"""
        
    def clear(self) -> None:
        """全クリア"""
        
    def get_stats(self) -> Dict[str, Any]:
        """統計情報"""

class FileWatcher:
    """ファイル監視"""
    
    def __init__(self, paths: List[str]):
        """初期化"""
        
    def start(self) -> None:
        """監視開始"""
        
    def stop(self) -> None:
        """監視停止"""
        
    def add_callback(self, callback: Callable) -> None:
        """コールバック登録"""
        
    def check_changes(self) -> List[str]:
        """変更チェック"""
```

### ディレクトリ構造

```
assets/
  ├── fonts/
  │   ├── NotoSansCJK-Regular.otf
  │   ├── NotoSansCJK-Bold.otf
  │   └── default.ttf
  ├── images/
  │   ├── backgrounds/
  │   │   ├── day.png
  │   │   └── night.png
  │   ├── icons/
  │   │   ├── weather/
  │   │   └── ui/
  │   └── misc/
  ├── sprites/
  │   ├── character.png
  │   ├── character.json
  │   └── effects.png
  └── manifest.json
```

### マニフェストファイル形式

```json
{
  "fonts": {
    "main": {
      "path": "fonts/NotoSansCJK-Regular.otf",
      "sizes": [16, 24, 36, 48, 72, 130]
    },
    "bold": {
      "path": "fonts/NotoSansCJK-Bold.otf",
      "sizes": [24, 36]
    }
  },
  "images": {
    "backgrounds": [
      "images/backgrounds/day.png",
      "images/backgrounds/night.png"
    ],
    "icons": {
      "weather": "images/icons/weather/*.png",
      "ui": "images/icons/ui/*.png"
    }
  },
  "sprites": {
    "character": {
      "sheet": "sprites/character.png",
      "frame_size": [128, 128],
      "animations": {
        "idle": [0, 3],
        "walk": [4, 11]
      }
    }
  }
}
```

## パフォーマンス要件

- フォント読み込み: 100ms以内
- 画像読み込み: 50ms以内（1024×600）
- キャッシュヒット率: 80%以上
- メモリ使用量: 100MB以内
- ホットリロード反応時間: 500ms以内

## 受け入れ基準

1. ✅ フォントが正しく読み込まれる
2. ✅ 日本語テキストが表示できる
3. ✅ 画像が正しく読み込まれる
4. ✅ 透過画像が正しく処理される
5. ✅ スプライトシートが分割される
6. ✅ キャッシュが機能する
7. ✅ ファイル不在時にエラーハンドリングされる
8. ✅ フォールバックフォントが使用される
9. ✅ 動的リロードが機能する（開発モード）
10. ✅ メモリ使用量が制限内に収まる

## 非機能要件

- スレッドセーフな実装
- 遅延読み込みのサポート
- プログレッシブ読み込み
- エラーログの適切な出力
- 単体テストカバレッジ: 80%以上

## 依存関係

- pygame >= 2.5.0（画像・フォント処理）
- Pillow >= 10.0.0（高度な画像処理、オプション）
- watchdog >= 3.0.0（ファイル監視、オプション）
- ConfigManager（設定読み込み）
- LogManager（ログ出力）

## 制約事項

- サポート画像形式: PNG, JPG, BMP
- サポートフォント形式: TTF, OTF
- 最大画像サイズ: 4096×4096
- 最大キャッシュサイズ: 100MB
- 最大同時読み込み数: 10

## エラーハンドリング

### ファイル不在
- デフォルトアセットを使用
- 警告ログ出力
- アプリケーション継続

### メモリ不足
- キャッシュの自動パージ
- 低品質モードへの切り替え
- エラーログ出力

### 破損ファイル
- スキップして次のアセット処理
- エラーログ出力
- 代替アセットの使用