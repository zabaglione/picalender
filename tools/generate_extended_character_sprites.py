#!/usr/bin/env python3
"""
拡張キャラクタースプライトシート生成ツール

TASK-402 Step 2/6: 15種類のアニメーション状態用スプライト生成
"""

import os
import sys
import pygame
import json
import math
from typing import List, Tuple, Dict

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))


class ExtendedCharacterSpriteGenerator:
    """拡張キャラクタースプライト生成器"""
    
    def __init__(self):
        """初期化"""
        pygame.init()
        
        # スプライト設定
        self.frame_width = 128
        self.frame_height = 128
        self.frames_per_animation = 8
        self.animations_count = 15
        
        # 色設定
        self.base_color = (100, 150, 200)  # ベースカラー（青系）
        self.accent_color = (255, 200, 100)  # アクセントカラー（オレンジ系）
        self.dark_color = (50, 75, 100)    # 暗いカラー
        self.light_color = (150, 200, 255) # 明るいカラー
        
        # 全体のスプライトシートサイズ
        self.sheet_width = self.frame_width * self.frames_per_animation
        self.sheet_height = self.frame_height * self.animations_count
        
        print(f"Extended sprite sheet: {self.sheet_width}x{self.sheet_height}")
    
    def create_extended_sprite_sheet(self) -> Tuple[pygame.Surface, Dict]:
        """拡張スプライトシートを作成"""
        # 大きなサーフェスを作成
        sprite_sheet = pygame.Surface((self.sheet_width, self.sheet_height), pygame.SRCALPHA)
        sprite_sheet.fill((0, 0, 0, 0))  # 透明に初期化
        
        # アニメーション定義
        animations = {
            # 既存アニメーション
            "idle": {"row": 0, "description": "待機", "mood": "neutral"},
            "walk": {"row": 1, "description": "歩行", "mood": "active"},
            "wave": {"row": 2, "description": "手振り", "mood": "friendly"},
            
            # 天気対応アニメーション
            "umbrella": {"row": 3, "description": "雨傘", "mood": "protected"},
            "shivering": {"row": 4, "description": "寒がり", "mood": "cold"},
            "sunbathing": {"row": 5, "description": "日光浴", "mood": "relaxed"},
            "hiding": {"row": 6, "description": "隠れる", "mood": "scared"},
            
            # 時間対応アニメーション
            "stretching": {"row": 7, "description": "ストレッチ", "mood": "energetic"},
            "yawning": {"row": 8, "description": "あくび", "mood": "sleepy"},
            "reading": {"row": 9, "description": "読書", "mood": "focused"},
            
            # 感情アニメーション
            "celebrating": {"row": 10, "description": "祝福", "mood": "joyful"},
            "pondering": {"row": 11, "description": "考え中", "mood": "thoughtful"},
            
            # 特殊アニメーション
            "dancing": {"row": 12, "description": "踊り", "mood": "ecstatic"},
            "eating": {"row": 13, "description": "食事", "mood": "satisfied"},
            "sleeping": {"row": 14, "description": "睡眠", "mood": "peaceful"}
        }
        
        # 各アニメーションを描画
        for anim_name, anim_data in animations.items():
            row = anim_data["row"]
            mood = anim_data["mood"]
            
            for frame in range(self.frames_per_animation):
                x = frame * self.frame_width
                y = row * self.frame_height
                
                frame_surface = self.create_animation_frame(anim_name, frame, mood)
                sprite_sheet.blit(frame_surface, (x, y))
        
        # メタデータを作成
        metadata = {
            "frame_size": [self.frame_width, self.frame_height],
            "frames_per_row": self.frames_per_animation,
            "total_animations": self.animations_count,
            "version": "2.0",
            "created_by": "TASK-402 Extended Character System",
            "animations": {}
        }
        
        # アニメーションメタデータを追加
        for anim_name, anim_data in animations.items():
            metadata["animations"][anim_name] = {
                "row": anim_data["row"],
                "frames": self.frames_per_animation,
                "fps": self.get_animation_fps(anim_name),
                "loop": self.get_animation_loop(anim_name),
                "description": anim_data["description"],
                "mood": anim_data["mood"],
                "triggers": self.get_animation_triggers(anim_name)
            }
        
        return sprite_sheet, metadata
    
    def create_animation_frame(self, animation: str, frame_index: int, mood: str) -> pygame.Surface:
        """特定のアニメーションフレームを作成"""
        surface = pygame.Surface((self.frame_width, self.frame_height), pygame.SRCALPHA)
        surface.fill((0, 0, 0, 0))
        
        # フレーム進行度 (0.0 - 1.0)
        progress = frame_index / self.frames_per_animation
        
        # 気分に応じた基本色を取得
        base_color = self.get_mood_color(mood)
        
        if animation == "idle":
            self.draw_idle_frame(surface, progress, base_color)
        elif animation == "walk":
            self.draw_walk_frame(surface, progress, base_color)
        elif animation == "wave":
            self.draw_wave_frame(surface, progress, base_color)
        elif animation == "umbrella":
            self.draw_umbrella_frame(surface, progress, base_color)
        elif animation == "shivering":
            self.draw_shivering_frame(surface, progress, base_color)
        elif animation == "sunbathing":
            self.draw_sunbathing_frame(surface, progress, base_color)
        elif animation == "hiding":
            self.draw_hiding_frame(surface, progress, base_color)
        elif animation == "stretching":
            self.draw_stretching_frame(surface, progress, base_color)
        elif animation == "yawning":
            self.draw_yawning_frame(surface, progress, base_color)
        elif animation == "reading":
            self.draw_reading_frame(surface, progress, base_color)
        elif animation == "celebrating":
            self.draw_celebrating_frame(surface, progress, base_color)
        elif animation == "pondering":
            self.draw_pondering_frame(surface, progress, base_color)
        elif animation == "dancing":
            self.draw_dancing_frame(surface, progress, base_color)
        elif animation == "eating":
            self.draw_eating_frame(surface, progress, base_color)
        elif animation == "sleeping":
            self.draw_sleeping_frame(surface, progress, base_color)
        else:
            # デフォルト（idle）
            self.draw_idle_frame(surface, progress, base_color)
        
        return surface
    
    def get_mood_color(self, mood: str) -> Tuple[int, int, int]:
        """気分に応じた色を取得"""
        mood_colors = {
            "neutral": (100, 150, 200),     # 青
            "active": (120, 180, 100),      # 緑
            "friendly": (200, 150, 100),    # オレンジ
            "protected": (100, 100, 180),   # 紫
            "cold": (150, 200, 255),        # 水色
            "relaxed": (255, 200, 150),     # 暖色
            "scared": (80, 80, 120),        # 暗い青
            "energetic": (255, 180, 100),   # 明るいオレンジ
            "sleepy": (120, 120, 150),      # グレー青
            "focused": (100, 120, 100),     # 深緑
            "joyful": (255, 200, 200),      # ピンク
            "thoughtful": (150, 100, 150),  # 紫
            "ecstatic": (255, 150, 255),    # マゼンタ
            "satisfied": (200, 180, 100),   # 金色
            "peaceful": (150, 150, 200)     # 薄紫
        }
        return mood_colors.get(mood, self.base_color)
    
    def draw_base_character(self, surface: pygame.Surface, x: int, y: int, 
                           color: Tuple[int, int, int], size_multiplier: float = 1.0):
        """基本キャラクター形状を描画"""
        # ベースサイズ調整
        base_size = int(30 * size_multiplier)
        head_size = int(20 * size_multiplier)
        
        # 体（楕円）
        body_rect = pygame.Rect(x - base_size//2, y - base_size//2, base_size, base_size * 1.2)
        pygame.draw.ellipse(surface, color, body_rect)
        
        # 頭（円）
        head_center = (x, y - int(base_size * 0.7))
        pygame.draw.circle(surface, color, head_center, head_size)
        
        # 目
        eye_color = (50, 50, 50)
        eye_size = max(2, int(3 * size_multiplier))
        left_eye = (x - int(8 * size_multiplier), y - int(base_size * 0.7))
        right_eye = (x + int(8 * size_multiplier), y - int(base_size * 0.7))
        pygame.draw.circle(surface, eye_color, left_eye, eye_size)
        pygame.draw.circle(surface, eye_color, right_eye, eye_size)
        
        return head_center, body_rect.center
    
    def draw_idle_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """待機アニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 微妙な上下動
        offset = int(math.sin(progress * math.pi * 2) * 2)
        self.draw_base_character(surface, x, y + offset, color)
    
    def draw_walk_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """歩行アニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 歩行の上下動
        offset = int(abs(math.sin(progress * math.pi * 4)) * 3)
        
        # 軽い傾き
        tilt = math.sin(progress * math.pi * 4) * 0.1
        
        self.draw_base_character(surface, x, y - offset, color, 1.0 + tilt * 0.1)
    
    def draw_wave_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """手振りアニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 基本キャラクター
        head_pos, body_pos = self.draw_base_character(surface, x, y, color)
        
        # 手（腕）の描画
        arm_angle = math.sin(progress * math.pi * 4) * 0.5 + 1.0
        arm_length = 15
        arm_x = x + int(math.cos(arm_angle) * arm_length)
        arm_y = y - int(math.sin(arm_angle) * arm_length)
        
        pygame.draw.line(surface, self.dark_color, body_pos, (arm_x, arm_y), 3)
        pygame.draw.circle(surface, color, (arm_x, arm_y), 5)
    
    def draw_umbrella_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """傘アニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 基本キャラクター
        head_pos, body_pos = self.draw_base_character(surface, x, y, color)
        
        # 傘の描画
        umbrella_x = x - 5
        umbrella_y = y - 50
        
        # 傘の棒
        pygame.draw.line(surface, self.dark_color, (umbrella_x, umbrella_y + 30), (umbrella_x, y), 2)
        
        # 傘の布部分（半円）
        umbrella_rect = pygame.Rect(umbrella_x - 25, umbrella_y, 50, 30)
        pygame.draw.arc(surface, (200, 50, 50), umbrella_rect, 0, math.pi, 3)
        
        # 雨滴効果
        for i in range(3):
            drop_x = x + (i - 1) * 30 + int(math.sin(progress * math.pi * 2) * 5)
            drop_y = umbrella_y - 10 - i * 5
            pygame.draw.circle(surface, (100, 150, 255), (drop_x, drop_y), 2)
    
    def draw_shivering_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """震えアニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 震えエフェクト
        shake_x = int(math.sin(progress * math.pi * 8) * 2)
        shake_y = int(math.cos(progress * math.pi * 6) * 1)
        
        self.draw_base_character(surface, x + shake_x, y + shake_y, color, 0.95)
        
        # 寒さエフェクト（小さな雪の結晶）
        for i in range(2):
            flake_x = x + (i - 0.5) * 40 + int(math.sin(progress * math.pi * 2 + i) * 3)
            flake_y = y - 30 - i * 10
            pygame.draw.circle(surface, (255, 255, 255), (flake_x, flake_y), 1)
    
    def draw_sunbathing_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """日光浴アニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 15
        
        # リラックスした姿勢（少し横になった感じ）
        self.draw_base_character(surface, x, y, color, 1.1)
        
        # 太陽光エフェクト
        sun_rays = 6
        for i in range(sun_rays):
            angle = (i / sun_rays) * math.pi * 2 + progress * math.pi
            ray_length = 20 + math.sin(progress * math.pi * 2) * 5
            ray_x = x + int(math.cos(angle) * ray_length)
            ray_y = y - 40 + int(math.sin(angle) * ray_length)
            pygame.draw.line(surface, (255, 255, 150), (x, y - 40), (ray_x, ray_y), 1)
    
    def draw_hiding_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """隠れるアニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 20
        
        # 縮んだ姿勢
        crouch_factor = 0.7 + math.sin(progress * math.pi * 4) * 0.1
        self.draw_base_character(surface, x, y, color, crouch_factor)
        
        # 雷エフェクト
        if progress > 0.7:
            lightning_points = [(x - 20, 10), (x - 15, 30), (x - 10, 20), (x - 5, 40)]
            if len(lightning_points) > 1:
                pygame.draw.lines(surface, (255, 255, 100), False, lightning_points, 2)
    
    def draw_stretching_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """ストレッチアニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 伸びる動作
        stretch = math.sin(progress * math.pi) * 0.2
        self.draw_base_character(surface, x, y - int(stretch * 10), color, 1.0 + stretch)
        
        # 腕を上に伸ばす
        if progress > 0.3:
            arm_y = y - 30 - int(stretch * 15)
            pygame.draw.line(surface, self.dark_color, (x, y - 10), (x - 10, arm_y), 3)
            pygame.draw.line(surface, self.dark_color, (x, y - 10), (x + 10, arm_y), 3)
    
    def draw_yawning_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """あくびアニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 基本キャラクター
        head_pos, body_pos = self.draw_base_character(surface, x, y, color)
        
        # 口を開ける動作
        if 0.3 < progress < 0.7:
            mouth_size = int(math.sin((progress - 0.3) / 0.4 * math.pi) * 5)
            mouth_pos = (x, y - 15)
            pygame.draw.ellipse(surface, (50, 50, 50), 
                              (mouth_pos[0] - mouth_size//2, mouth_pos[1] - mouth_size//2, 
                               mouth_size, mouth_size))
    
    def draw_reading_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """読書アニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 基本キャラクター
        head_pos, body_pos = self.draw_base_character(surface, x, y, color)
        
        # 本の描画
        book_x = x + 5
        book_y = y + 5
        book_rect = pygame.Rect(book_x - 8, book_y - 6, 16, 12)
        pygame.draw.rect(surface, (150, 100, 50), book_rect)
        pygame.draw.line(surface, (100, 70, 30), (book_x, book_y - 6), (book_x, book_y + 6), 1)
        
        # ページめくり効果
        if int(progress * 4) % 2 == 1:
            pygame.draw.line(surface, (200, 200, 200), 
                           (book_x - 8, book_y - 6), (book_x + 8, book_y - 6), 1)
    
    def draw_celebrating_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """祝福アニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 跳ねる動作
        bounce = abs(math.sin(progress * math.pi * 2)) * 10
        self.draw_base_character(surface, x, y - bounce, color)
        
        # 紙吹雪エフェクト
        for i in range(4):
            confetti_x = x + (i - 2) * 15 + int(math.sin(progress * math.pi * 2 + i) * 10)
            confetti_y = y - 40 - int(progress * 20) % 60
            confetti_colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255), (255, 255, 100)]
            pygame.draw.circle(surface, confetti_colors[i], (confetti_x, confetti_y), 2)
    
    def draw_pondering_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """考え中アニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 基本キャラクター
        head_pos, body_pos = self.draw_base_character(surface, x, y, color)
        
        # 手を顎に当てる
        hand_x = x + 8
        hand_y = y - 20
        pygame.draw.circle(surface, color, (hand_x, hand_y), 4)
        
        # 思考バブル
        if progress > 0.5:
            bubble_x = x - 20
            bubble_y = y - 45
            bubble_sizes = [3, 5, 8]
            for i, size in enumerate(bubble_sizes):
                bubble_pos = (bubble_x - i * 8, bubble_y - i * 5)
                pygame.draw.circle(surface, (255, 255, 255), bubble_pos, size)
                pygame.draw.circle(surface, (100, 100, 100), bubble_pos, size, 1)
    
    def draw_dancing_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """踊りアニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # ダンスポーズ
        dance_offset_x = int(math.sin(progress * math.pi * 4) * 8)
        dance_offset_y = int(abs(math.cos(progress * math.pi * 4)) * 5)
        
        self.draw_base_character(surface, x + dance_offset_x, y - dance_offset_y, color)
        
        # 音楽ノート
        for i in range(2):
            note_x = x + (i - 0.5) * 30 + int(math.sin(progress * math.pi * 2 + i * 2) * 5)
            note_y = y - 35 - i * 8
            pygame.draw.circle(surface, (200, 150, 255), (note_x, note_y), 3)
            pygame.draw.line(surface, (200, 150, 255), (note_x + 3, note_y), (note_x + 3, note_y - 8), 2)
    
    def draw_eating_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """食事アニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 10
        
        # 基本キャラクター
        head_pos, body_pos = self.draw_base_character(surface, x, y, color)
        
        # 食べ物（りんご）
        if progress < 0.8:
            apple_x = x + 10
            apple_y = y - 5
            pygame.draw.circle(surface, (255, 100, 100), (apple_x, apple_y), 6)
            pygame.draw.arc(surface, (100, 200, 100), 
                          (apple_x - 2, apple_y - 8, 4, 6), 0, math.pi, 2)
        
        # 咀嚼動作
        if int(progress * 8) % 2 == 1:
            # 口が動く
            pygame.draw.circle(surface, (100, 50, 50), (x - 2, y - 18), 2)
    
    def draw_sleeping_frame(self, surface: pygame.Surface, progress: float, color: Tuple[int, int, int]):
        """睡眠アニメーション"""
        x, y = self.frame_width // 2, self.frame_height // 2 + 20
        
        # 横になった姿勢
        self.draw_base_character(surface, x, y, color, 0.8)
        
        # 睡眠エフェクト（Z文字）
        z_chars = ['z', 'Z', 'z']
        for i, char in enumerate(z_chars):
            z_x = x - 15 + i * 8 + int(math.sin(progress * math.pi * 2 + i) * 3)
            z_y = y - 30 - i * 8 - int(progress * 10) % 20
            # 簡易的なZ表現（線で描画）
            if char == 'z':
                size = 4
            else:
                size = 6
            
            # Z字を線で描画
            z_points = [
                (z_x - size//2, z_y - size//2),
                (z_x + size//2, z_y - size//2),
                (z_x - size//2, z_y + size//2),
                (z_x + size//2, z_y + size//2)
            ]
            if len(z_points) >= 4:
                pygame.draw.lines(surface, (150, 150, 200), False, z_points[:3], 2)
    
    def get_animation_fps(self, animation: str) -> int:
        """アニメーションのFPSを取得"""
        fps_map = {
            "idle": 6,
            "walk": 12,
            "wave": 10,
            "umbrella": 8,
            "shivering": 15,
            "sunbathing": 4,
            "hiding": 12,
            "stretching": 6,
            "yawning": 5,
            "reading": 3,
            "celebrating": 15,
            "pondering": 4,
            "dancing": 20,
            "eating": 8,
            "sleeping": 2
        }
        return fps_map.get(animation, 8)
    
    def get_animation_loop(self, animation: str) -> bool:
        """アニメーションがループするかどうか"""
        non_loop = ["stretching", "yawning"]
        return animation not in non_loop
    
    def get_animation_triggers(self, animation: str) -> List[str]:
        """アニメーションのトリガー条件"""
        trigger_map = {
            "idle": ["default", "calm"],
            "walk": ["active", "exploring"],
            "wave": ["greeting", "friendly"],
            "umbrella": ["rain", "drizzle"],
            "shivering": ["cold", "snow", "freezing"],
            "sunbathing": ["sunny", "hot", "relaxing"],
            "hiding": ["thunderstorm", "lightning", "scared"],
            "stretching": ["morning", "wake_up"],
            "yawning": ["tired", "sleepy", "late_night"],
            "reading": ["evening", "quiet", "rainy"],
            "celebrating": ["special_event", "happy", "achievement"],
            "pondering": ["thinking", "confused", "decision"],
            "dancing": ["music", "very_happy", "party"],
            "eating": ["meal_time", "hungry"],
            "sleeping": ["night", "very_tired", "bedtime"]
        }
        return trigger_map.get(animation, [])
    
    def save_sprite_sheet(self, sprite_sheet: pygame.Surface, metadata: Dict, 
                         sprite_path: str, metadata_path: str):
        """スプライトシートとメタデータを保存"""
        # スプライトシート保存
        pygame.image.save(sprite_sheet, sprite_path)
        print(f"✅ Extended sprite sheet saved: {sprite_path}")
        
        # メタデータ保存
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        print(f"✅ Metadata saved: {metadata_path}")


def main():
    """メイン関数"""
    print("=== Extended Character Sprite Generator ===")
    print("TASK-402 Step 2/6: Generating extended animation sprites")
    
    # 出力パス設定
    sprite_path = "assets/sprites/character_sheet_extended.png"
    metadata_path = "assets/sprites/character_sheet_extended.json"
    
    # ディレクトリ作成
    os.makedirs(os.path.dirname(sprite_path), exist_ok=True)
    
    try:
        # ジェネレーター作成
        generator = ExtendedCharacterSpriteGenerator()
        
        # スプライトシート生成
        print("Generating extended sprite sheet...")
        sprite_sheet, metadata = generator.create_extended_sprite_sheet()
        
        # 保存
        generator.save_sprite_sheet(sprite_sheet, metadata, sprite_path, metadata_path)
        
        # 統計情報表示
        print(f"\n=== Generation Summary ===")
        print(f"Total animations: {len(metadata['animations'])}")
        print(f"Total frames: {len(metadata['animations']) * generator.frames_per_animation}")
        print(f"Sheet dimensions: {generator.sheet_width}x{generator.sheet_height}")
        print(f"Frame size: {generator.frame_width}x{generator.frame_height}")
        
        # アニメーションリスト表示
        print(f"\n=== Animation List ===")
        for anim_name, anim_data in metadata['animations'].items():
            triggers = ", ".join(anim_data['triggers'][:3])  # 最初の3つのトリガーを表示
            print(f"{anim_name:12} | {anim_data['mood']:10} | {triggers}")
        
        print(f"\n✅ Extended character sprite system ready!")
        return True
        
    except Exception as e:
        print(f"❌ Generation failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        pygame.quit()


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)