# パフォーマンス最適化ガイド

## 概要

PiCalendarは、Raspberry Pi Zero 2 W（RAM 512MB、4コアCPU）での動作を想定して最適化されています。
このドキュメントでは、パフォーマンス最適化の仕組みと設定方法について説明します。

## 目標値

Raspberry Pi Zero 2 Wでの目標パフォーマンス：

- **CPU使用率**: 平均30%以下
- **メモリ使用量**: 180MB以下
- **フレームレート**: 15-30 FPS（品質レベルに応じて）

## 品質レベル

### 4つの品質レベル

アプリケーションは4つの品質レベルを提供し、自動または手動で切り替えることができます：

| レベル | FPS | CPU目安 | メモリ目安 | 用途 |
|--------|-----|---------|------------|------|
| ultra_low | 10 | 10-15% | 100MB | 最小リソース、省電力重視 |
| low | 15 | 15-20% | 120MB | 低スペック環境、バッテリー駆動 |
| medium | 20 | 20-30% | 150MB | バランス重視（推奨） |
| high | 30 | 30-40% | 180MB | 高品質表示 |

### 各レベルの更新間隔

| コンポーネント | ultra_low | low | medium | high |
|---------------|-----------|-----|--------|------|
| 時計 | 1秒 | 1秒 | 1秒 | 1秒 |
| 日付 | 60秒 | 30秒 | 10秒 | 1秒 |
| カレンダー | 5分 | 2分 | 1分 | 1分 |
| 天気 | 30分 | 15分 | 10分 | 5分 |
| 背景 | 60分 | 30分 | 10分 | 5分 |
| キャラクター | 5fps | 8fps | 10fps | 16fps |

## 設定方法

### settings.yamlでの設定

```yaml
performance:
  # 自動品質調整を有効化
  auto_adjust: true
  
  # デフォルトの品質レベル
  default_quality: medium  # ultra_low, low, medium, high
  
  # パフォーマンス監視間隔（秒）
  monitor_interval: 5.0
  
  # 手動で品質を固定する場合
  # auto_adjust: false
  # default_quality: low
```

### 環境変数での設定

```bash
# 品質レベルを環境変数で指定
export PICALENDAR_QUALITY=low

# 自動調整を無効化
export PICALENDAR_AUTO_ADJUST=false
```

## 最適化テクニック

### 1. Dirty Rectangle最適化

変更があった領域のみを再描画することで、描画処理を高速化：

```python
# PerformanceOptimizerを使用
optimizer = get_performance_optimizer(settings)

# 変更領域を記録
optimizer.add_dirty_rect(pygame.Rect(100, 100, 200, 200))

# 更新が必要な領域を取得
dirty_rects = optimizer.get_dirty_rects()
pygame.display.update(dirty_rects)
```

### 2. サーフェスキャッシュ

頻繁に使用するサーフェスをキャッシュ：

```python
# RenderOptimizerを使用
render_opt = get_render_optimizer()

# テキストレンダリングの最適化
text_surface = render_opt.optimize_text_rendering(font, "Hello", (255, 255, 255))

# スケールされたサーフェスのキャッシュ
scaled = render_opt.get_scaled_surface(original_surface, 0.75)
```

### 3. 更新間隔の最適化

各コンポーネントの更新頻度を制御：

```python
# コンポーネントの更新判定
if optimizer.should_update_component('clock', last_clock_update):
    # 時計を更新
    update_clock()
    last_clock_update = time.time()
```

### 4. メモリ管理

自動メモリ解放機能：

```python
# メモリ使用量が閾値を超えた場合、自動的に解放
optimizer.free_memory()

# キャッシュのクリア
render_opt.clear_cache()
```

## パフォーマンス監視

### ベンチマークスクリプトの実行

```bash
# フルベンチマーク
python scripts/benchmark.py

# クイックテスト（5秒間の測定）
python scripts/benchmark.py --quick

# カスタム設定でテスト
python scripts/benchmark.py --config custom_settings.yaml
```

### 実行時の監視

アプリケーション実行中のパフォーマンス監視：

```python
# パフォーマンス統計の取得
stats = optimizer.get_performance_stats()
print(f"CPU平均: {stats['avg_cpu']:.1f}%")
print(f"メモリ平均: {stats['avg_memory']:.1f}MB")
print(f"FPS平均: {stats['avg_fps']:.1f}")
print(f"品質レベル: {stats['current_quality']}")
```

### systemdでの監視

```bash
# リソース使用状況を確認
systemctl status picalender

# 詳細なリソース情報
systemd-cgtop -p /system.slice/picalender.service
```

## トラブルシューティング

### CPU使用率が高い場合

1. 品質レベルを下げる：
   ```yaml
   performance:
     default_quality: low
   ```

2. FPSを制限する：
   ```yaml
   screen:
     fps: 15
   ```

3. キャラクターアニメーションを無効化：
   ```yaml
   character:
     enabled: false
   ```

### メモリ使用量が多い場合

1. キャッシュサイズを削減：
   ```yaml
   performance:
     cache_size: 20
   ```

2. 背景画像の解像度を下げる
3. フォントサイズを最適化

### 描画がカクつく場合

1. Dirty Rectangle最適化を有効化
2. ハードウェアアクセラレーションの設定を確認：
   ```bash
   export SDL_VIDEODRIVER=kmsdrm
   export SDL_RENDER_DRIVER=software  # または opengles2
   ```

## Raspberry Pi固有の最適化

### GPU メモリ分割

`/boot/config.txt`で GPU メモリを調整：

```ini
# 128MBをGPUに割り当て（推奨）
gpu_mem=128
```

### オーバークロック（オプション）

安定性を重視する場合は推奨しませんが、必要に応じて：

```ini
# /boot/config.txt
arm_freq=1200
over_voltage=4
```

### 冷却

継続的な運用では、ヒートシンクの装着を推奨します。

## ベンチマーク結果例

Raspberry Pi Zero 2 Wでの実測値：

```json
{
  "quality_level": "medium",
  "memory_usage": {
    "min_mb": 145.2,
    "max_mb": 168.4,
    "avg_mb": 156.8
  },
  "cpu_usage": {
    "min_percent": 18.5,
    "max_percent": 35.2,
    "avg_percent": 26.4
  },
  "fps": {
    "target": 20,
    "actual_avg": 19.2
  }
}
```

## まとめ

PiCalendarのパフォーマンス最適化は、以下の3つの柱で構成されています：

1. **動的品質調整**: リソース使用状況に応じた自動調整
2. **効率的な描画**: Dirty Rectangle、キャッシュ、更新間隔の最適化
3. **メモリ管理**: 自動解放とキャッシュ制御

これらの機能により、Raspberry Pi Zero 2 Wのような限られたリソースでも、
安定して美しい表示を実現できます。