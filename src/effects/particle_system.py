"""
パーティクルシステム

天気エフェクト用の軽量パーティクルシステム
"""

import random
import math
from typing import List, Tuple, Optional, Callable
import pygame


class Particle:
    """個別のパーティクル"""
    
    def __init__(self, x: float, y: float, vx: float = 0, vy: float = 0):
        """
        初期化
        
        Args:
            x: X座標
            y: Y座標
            vx: X方向速度
            vy: Y方向速度
        """
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = 1.0  # 生存時間（0-1）
        self.size = 1.0
        self.color = (255, 255, 255, 255)
        self.active = True
    
    def update(self, dt: float) -> None:
        """
        更新
        
        Args:
            dt: デルタタイム（秒）
        """
        if not self.active:
            return
        
        self.x += self.vx * dt
        self.y += self.vy * dt
    
    def reset(self, x: float, y: float, vx: float = 0, vy: float = 0) -> None:
        """リセット"""
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = 1.0
        self.active = True


class ParticleSystem:
    """パーティクルシステム"""
    
    def __init__(self, max_particles: int = 1000):
        """
        初期化
        
        Args:
            max_particles: 最大パーティクル数
        """
        self.max_particles = max_particles
        self.particles: List[Particle] = []
        self.particle_pool: List[Particle] = []
        
        # オブジェクトプールを事前作成
        for _ in range(max_particles):
            self.particle_pool.append(Particle(0, 0))
            self.particle_pool[-1].active = False
        
        # エミッター設定
        self.emit_rate = 10.0  # 秒あたりの放出数
        self.emit_timer = 0.0
        
        # 物理設定
        self.gravity = (0, 100)  # 重力加速度
        self.wind = (0, 0)  # 風の影響
        self.damping = 0.99  # 減衰率
        
        # 描画設定
        self.blend_mode = pygame.BLEND_ADD
    
    def emit(self, x: float, y: float, 
             vx_range: Tuple[float, float] = (-10, 10),
             vy_range: Tuple[float, float] = (-10, 10)) -> Optional[Particle]:
        """
        パーティクルを放出
        
        Args:
            x: 放出X座標
            y: 放出Y座標
            vx_range: X速度範囲
            vy_range: Y速度範囲
            
        Returns:
            放出されたパーティクル
        """
        # プールから取得
        for particle in self.particle_pool:
            if not particle.active:
                vx = random.uniform(vx_range[0], vx_range[1])
                vy = random.uniform(vy_range[0], vy_range[1])
                particle.reset(x, y, vx, vy)
                self.particles.append(particle)
                return particle
        
        return None
    
    def update(self, dt: float) -> None:
        """
        システム全体を更新
        
        Args:
            dt: デルタタイム（秒）
        """
        # アクティブなパーティクルを更新
        active_particles = []
        for particle in self.particles:
            if particle.active:
                # 物理更新
                particle.vx += self.gravity[0] * dt + self.wind[0] * dt
                particle.vy += self.gravity[1] * dt + self.wind[1] * dt
                
                # 減衰
                particle.vx *= self.damping
                particle.vy *= self.damping
                
                # 位置更新
                particle.update(dt)
                
                # 生存時間更新
                particle.life -= dt * 0.2  # 5秒で消滅
                
                if particle.life > 0:
                    active_particles.append(particle)
                else:
                    particle.active = False
        
        self.particles = active_particles
    
    def render(self, screen: pygame.Surface) -> None:
        """
        パーティクルを描画
        
        Args:
            screen: 描画対象サーフェス
        """
        for particle in self.particles:
            if particle.active and particle.life > 0:
                alpha = int(particle.life * 255)
                color = (*particle.color[:3], alpha)
                
                # シンプルな円で描画
                pygame.draw.circle(screen, color, 
                                 (int(particle.x), int(particle.y)),
                                 int(particle.size))
    
    def clear(self) -> None:
        """全パーティクルをクリア"""
        for particle in self.particles:
            particle.active = False
        self.particles.clear()
    
    def set_gravity(self, x: float, y: float) -> None:
        """重力を設定"""
        self.gravity = (x, y)
    
    def set_wind(self, x: float, y: float) -> None:
        """風を設定"""
        self.wind = (x, y)


class RainParticleSystem(ParticleSystem):
    """雨パーティクルシステム"""
    
    def __init__(self, screen_width: int, screen_height: int, intensity: float = 0.5):
        """
        初期化
        
        Args:
            screen_width: 画面幅
            screen_height: 画面高さ
            intensity: 強度（0-1）
        """
        particle_count = int(200 * intensity)
        super().__init__(particle_count)
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.intensity = intensity
        
        # 雨の設定
        self.set_gravity(0, 800)  # 強い下向き
        self.set_wind(50, 0)  # 少し横風
        
        # 初期パーティクル生成
        for _ in range(particle_count // 2):
            x = random.uniform(0, screen_width)
            y = random.uniform(-100, screen_height)
            particle = self.emit(x, y, (0, 20), (300, 400))
            if particle:
                particle.size = random.uniform(1, 2)
                particle.color = (100, 150, 255, 200)
    
    def update(self, dt: float) -> None:
        """更新"""
        super().update(dt)
        
        # 新しい雨粒を生成
        emit_count = int(self.intensity * 5)
        for _ in range(emit_count):
            if random.random() < 0.3:
                x = random.uniform(-50, self.screen_width + 50)
                y = -10
                particle = self.emit(x, y, (-20, 20), (300, 500))
                if particle:
                    particle.size = random.uniform(1, 3)
                    particle.color = (100, 150, 255, 150)
        
        # 画面外のパーティクルをリサイクル
        for particle in self.particles:
            if particle.active and particle.y > self.screen_height + 10:
                particle.active = False


class SnowParticleSystem(ParticleSystem):
    """雪パーティクルシステム"""
    
    def __init__(self, screen_width: int, screen_height: int, intensity: float = 0.5):
        """
        初期化
        
        Args:
            screen_width: 画面幅
            screen_height: 画面高さ
            intensity: 強度（0-1）
        """
        particle_count = int(150 * intensity)
        super().__init__(particle_count)
        
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.intensity = intensity
        self.time = 0
        
        # 雪の設定
        self.set_gravity(0, 50)  # 弱い下向き
        self.damping = 0.98
        
        # 初期パーティクル生成
        for _ in range(particle_count // 2):
            x = random.uniform(0, screen_width)
            y = random.uniform(-100, screen_height)
            particle = self.emit(x, y, (-10, 10), (20, 60))
            if particle:
                particle.size = random.uniform(2, 5)
                particle.color = (255, 255, 255, 200)
    
    def update(self, dt: float) -> None:
        """更新"""
        self.time += dt
        
        # 風を変化させる（ゆらゆら効果）
        wind_x = math.sin(self.time * 2) * 30
        self.set_wind(wind_x, 0)
        
        super().update(dt)
        
        # 新しい雪を生成
        emit_count = int(self.intensity * 3)
        for _ in range(emit_count):
            if random.random() < 0.2:
                x = random.uniform(-50, self.screen_width + 50)
                y = -10
                particle = self.emit(x, y, (-20, 20), (20, 80))
                if particle:
                    particle.size = random.uniform(2, 6)
                    particle.color = (255, 255, 255, 180)
        
        # 画面外のパーティクルをリサイクル
        for particle in self.particles:
            if particle.active and particle.y > self.screen_height + 10:
                particle.active = False


class FogLayer:
    """霧レイヤー"""
    
    def __init__(self, screen_width: int, screen_height: int, density: float = 0.5):
        """
        初期化
        
        Args:
            screen_width: 画面幅
            screen_height: 画面高さ
            density: 濃度（0-1）
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.density = density
        self.time = 0
        
        # 霧のサーフェス
        self.fog_surface = pygame.Surface((screen_width, screen_height), pygame.SRCALPHA)
        self.update_fog()
    
    def update_fog(self) -> None:
        """霧を生成"""
        self.fog_surface.fill((0, 0, 0, 0))
        
        # グラデーション霧を作成
        alpha = int(self.density * 100)
        
        for i in range(3):
            y = self.screen_height * (0.3 + i * 0.2)
            height = self.screen_height * 0.3
            
            # 移動する霧の帯
            offset_x = math.sin(self.time + i) * 50
            
            fog_rect = pygame.Surface((self.screen_width + 100, int(height)), pygame.SRCALPHA)
            
            # グラデーション効果
            for j in range(int(height)):
                fade = 1.0 - abs(j - height/2) / (height/2)
                band_alpha = int(alpha * fade)
                pygame.draw.line(fog_rect, (200, 200, 200, band_alpha),
                               (0, j), (self.screen_width + 100, j))
            
            self.fog_surface.blit(fog_rect, (offset_x - 50, y - height/2))
    
    def update(self, dt: float) -> None:
        """更新"""
        self.time += dt * 0.5
        self.update_fog()
    
    def render(self, screen: pygame.Surface) -> None:
        """描画"""
        screen.blit(self.fog_surface, (0, 0))


class LightningEffect:
    """雷エフェクト"""
    
    def __init__(self, screen_width: int, screen_height: int):
        """
        初期化
        
        Args:
            screen_width: 画面幅
            screen_height: 画面高さ
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.flash_timer = 0
        self.flash_duration = 0
        self.flash_intensity = 0
        self.next_flash = random.uniform(3, 10)
    
    def trigger(self, intensity: float = 1.0) -> None:
        """雷を発生させる"""
        self.flash_timer = 0
        self.flash_duration = random.uniform(0.1, 0.3)
        self.flash_intensity = intensity
    
    def update(self, dt: float) -> None:
        """更新"""
        self.flash_timer += dt
        self.next_flash -= dt
        
        # 自動発生
        if self.next_flash <= 0:
            self.trigger(random.uniform(0.5, 1.0))
            self.next_flash = random.uniform(3, 10)
    
    def render(self, screen: pygame.Surface) -> None:
        """描画"""
        if self.flash_timer < self.flash_duration:
            # フラッシュの強度を計算
            progress = self.flash_timer / self.flash_duration
            intensity = (1.0 - progress) * self.flash_intensity
            
            # 白いフラッシュ
            flash_surface = pygame.Surface((self.screen_width, self.screen_height))
            flash_surface.fill((255, 255, 200))
            flash_surface.set_alpha(int(intensity * 100))
            screen.blit(flash_surface, (0, 0))