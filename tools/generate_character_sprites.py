#!/usr/bin/env python3
"""
キャラクタースプライト生成ツール

シンプルな2Dキャラクターのスプライトシートを生成
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PIL import Image, ImageDraw
import math


def create_character_frame(size: int, frame_index: int, state: str) -> Image.Image:
    """
    キャラクターの1フレームを作成
    
    Args:
        size: フレームサイズ
        frame_index: フレーム番号
        state: 状態（idle, walk, wave）
        
    Returns:
        フレーム画像
    """
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    center_x = size // 2
    center_y = size // 2
    
    # 色設定
    body_color = (100, 150, 200)
    outline_color = (50, 75, 100)
    eye_color = (255, 255, 255)
    pupil_color = (0, 0, 0)
    
    if state == "idle":
        # アイドル状態（呼吸アニメーション）
        breath_offset = math.sin(frame_index * math.pi / 4) * 2
        
        # 体
        body_y = center_y + 10 + breath_offset
        draw.ellipse([center_x - 25, body_y - 20,
                     center_x + 25, body_y + 30],
                    fill=body_color, outline=outline_color, width=2)
        
        # 頭
        head_y = center_y - 15 + breath_offset
        draw.ellipse([center_x - 20, head_y - 20,
                     center_x + 20, head_y + 20],
                    fill=body_color, outline=outline_color, width=2)
        
        # 目（瞬き）
        if frame_index == 7:  # 瞬き
            draw.line([center_x - 10, head_y - 5, center_x - 2, head_y - 5],
                     fill=pupil_color, width=2)
            draw.line([center_x + 2, head_y - 5, center_x + 10, head_y - 5],
                     fill=pupil_color, width=2)
        else:
            # 左目
            draw.ellipse([center_x - 10, head_y - 8,
                         center_x - 2, head_y],
                        fill=eye_color)
            draw.ellipse([center_x - 8, head_y - 6,
                         center_x - 4, head_y - 2],
                        fill=pupil_color)
            
            # 右目
            draw.ellipse([center_x + 2, head_y - 8,
                         center_x + 10, head_y],
                        fill=eye_color)
            draw.ellipse([center_x + 4, head_y - 6,
                         center_x + 8, head_y - 2],
                        fill=pupil_color)
        
        # 口
        draw.arc([center_x - 5, head_y + 2,
                 center_x + 5, head_y + 8],
                start=0, end=180, fill=outline_color, width=2)
        
    elif state == "walk":
        # 歩行状態
        walk_offset = math.sin(frame_index * math.pi / 2) * 3
        bounce = abs(math.sin(frame_index * math.pi / 2)) * 2
        
        # 体
        body_y = center_y + 10 - bounce
        draw.ellipse([center_x - 25, body_y - 20,
                     center_x + 25, body_y + 30],
                    fill=body_color, outline=outline_color, width=2)
        
        # 頭
        head_y = center_y - 15 - bounce
        draw.ellipse([center_x - 20, head_y - 20,
                     center_x + 20, head_y + 20],
                    fill=body_color, outline=outline_color, width=2)
        
        # 足（アニメーション）
        left_foot_x = center_x - 10 + walk_offset
        right_foot_x = center_x + 10 - walk_offset
        foot_y = body_y + 25
        
        draw.ellipse([left_foot_x - 5, foot_y - 3,
                     left_foot_x + 5, foot_y + 3],
                    fill=body_color, outline=outline_color)
        draw.ellipse([right_foot_x - 5, foot_y - 3,
                     right_foot_x + 5, foot_y + 3],
                    fill=body_color, outline=outline_color)
        
        # 目
        draw.ellipse([center_x - 10, head_y - 8,
                     center_x - 2, head_y],
                    fill=eye_color)
        draw.ellipse([center_x - 7, head_y - 6,
                     center_x - 3, head_y - 2],
                    fill=pupil_color)
        
        draw.ellipse([center_x + 2, head_y - 8,
                     center_x + 10, head_y],
                    fill=eye_color)
        draw.ellipse([center_x + 5, head_y - 6,
                     center_x + 9, head_y - 2],
                    fill=pupil_color)
        
    elif state == "wave":
        # 手を振る状態
        wave_angle = math.sin(frame_index * math.pi / 2) * 30
        
        # 体
        body_y = center_y + 10
        draw.ellipse([center_x - 25, body_y - 20,
                     center_x + 25, body_y + 30],
                    fill=body_color, outline=outline_color, width=2)
        
        # 頭
        head_y = center_y - 15
        draw.ellipse([center_x - 20, head_y - 20,
                     center_x + 20, head_y + 20],
                    fill=body_color, outline=outline_color, width=2)
        
        # 腕（手を振る）
        arm_end_x = center_x + 30 + wave_angle / 3
        arm_end_y = head_y - 10 + abs(wave_angle) / 5
        
        # 腕の線
        draw.line([center_x + 20, body_y - 10,
                  arm_end_x, arm_end_y],
                 fill=outline_color, width=4)
        
        # 手
        draw.ellipse([arm_end_x - 6, arm_end_y - 6,
                     arm_end_x + 6, arm_end_y + 6],
                    fill=body_color, outline=outline_color)
        
        # もう一方の腕
        draw.line([center_x - 20, body_y - 10,
                  center_x - 25, body_y + 5],
                 fill=outline_color, width=4)
        
        # 笑顔の目
        draw.arc([center_x - 10, head_y - 10,
                 center_x - 2, head_y - 2],
                start=180, end=0, fill=pupil_color, width=2)
        draw.arc([center_x + 2, head_y - 10,
                 center_x + 10, head_y - 2],
                start=180, end=0, fill=pupil_color, width=2)
        
        # 大きな笑顔
        draw.arc([center_x - 8, head_y,
                 center_x + 8, head_y + 10],
                start=0, end=180, fill=outline_color, width=3)
    
    return img


def create_sprite_sheet(frame_size: int = 128, frames_per_state: int = 8):
    """
    スプライトシートを作成
    
    Args:
        frame_size: 1フレームのサイズ
        frames_per_state: 各状態のフレーム数
        
    Returns:
        スプライトシート画像
    """
    states = ["idle", "walk", "wave"]
    
    # スプライトシートのサイズ
    sheet_width = frame_size * frames_per_state
    sheet_height = frame_size * len(states)
    
    sprite_sheet = Image.new('RGBA', (sheet_width, sheet_height), (0, 0, 0, 0))
    
    for state_index, state in enumerate(states):
        for frame_index in range(frames_per_state):
            # フレームを生成
            frame = create_character_frame(frame_size, frame_index, state)
            
            # スプライトシートに配置
            x = frame_index * frame_size
            y = state_index * frame_size
            sprite_sheet.paste(frame, (x, y))
    
    return sprite_sheet


def main():
    """メイン処理"""
    # 出力ディレクトリ
    output_dir = "assets/sprites"
    os.makedirs(output_dir, exist_ok=True)
    
    print("Generating character sprite sheet...")
    
    # スプライトシート生成
    sprite_sheet = create_sprite_sheet(128, 8)
    
    # 保存
    output_path = os.path.join(output_dir, "character_sheet.png")
    sprite_sheet.save(output_path)
    print(f"  Saved: {output_path}")
    print(f"  Size: {sprite_sheet.size}")
    print(f"  Format: 3 states × 8 frames = 24 total frames")
    
    # メタデータ生成
    metadata = {
        "frame_size": [128, 128],
        "frames_per_row": 8,
        "animations": {
            "idle": {
                "row": 0,
                "frames": 8,
                "fps": 8,
                "loop": True
            },
            "walk": {
                "row": 1,
                "frames": 8,
                "fps": 12,
                "loop": True
            },
            "wave": {
                "row": 2,
                "frames": 8,
                "fps": 10,
                "loop": True
            }
        }
    }
    
    import json
    metadata_path = os.path.join(output_dir, "character_sheet.json")
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    print(f"  Metadata saved: {metadata_path}")
    
    print("\n✓ Character sprite sheet generated successfully!")


if __name__ == "__main__":
    main()