import tkinter as tk
from tkinter import ttk
import cv2
import numpy as np
from PIL import Image
import os
import wave
from pydub import AudioSegment
import subprocess


class VideoGenerator:
    def __init__(self, text_path, image_folder, center_image_path, output_path):
        self.text_path = text_path
        self.image_folder = image_folder
        self.center_image_path = center_image_path
        self.output_path = output_path
        self.temp_video_path = os.path.join(os.path.dirname(output_path), "temp_video.mp4")
        self.temp_audio_path = os.path.join(os.path.dirname(output_path), "temp_audio.wav")
        self.width = 1370
        self.height = 1080
        self.fps = 30
        self.center_image_duration = 2  # 중앙 이미지 표시 시간 (초)

    def get_wav_duration(self, wav_path):
        """WAV 파일의 재생 시간을 초 단위로 반환"""
        try:
            with wave.open(wav_path, 'rb') as wav_file:
                frames = wav_file.getnframes()
                rate = wav_file.getframerate()
                duration = frames / float(rate)
                return duration
        except Exception as e:
            print(f"WAV 파일 읽기 오류: {e}")
            return 3.0

    def find_tts_file(self, index):
        """해당 인덱스의 TTS 파일 찾기 - 번호를 기준으로 모든 패턴 검색"""
        prefix = f"tts{index}"
        for filename in os.listdir(self.image_folder):
            if filename.startswith(prefix) and filename.endswith('.wav'):
                return os.path.join(self.image_folder, filename)
        return None

    # [기존 이미지 처리 메서드들은 동일하게 유지]
    def resize_image(self, image, max_width=800, max_height=600):
        h, w = image.shape[:2]
        aspect = min(max_width / w, max_height / h)
        new_size = (int(w * aspect), int(h * aspect))

        if image.shape[2] == 4:
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA))
        else:
            pil_img = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        pil_img = pil_img.resize(new_size, Image.Resampling.LANCZOS)

        if image.shape[2] == 4:
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGBA2BGRA)
        else:
            return cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)

    def read_text_file(self):
        with open(self.text_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]

    def find_subtitle_image(self, index):
        prefix = f"subtitle_{index}_"
        for filename in os.listdir(self.image_folder):
            if filename.startswith(prefix) and filename.lower().endswith('.png'):
                return os.path.join(self.image_folder, filename)
        return None

    def read_image_with_pil(self, image_path):
        try:
            pil_image = Image.open(image_path)
            pil_image = pil_image.convert('RGBA')
            numpy_image = np.array(pil_image)
            return cv2.cvtColor(numpy_image, cv2.COLOR_RGBA2BGRA)
        except Exception as e:
            print(f"이미지 로딩 에러: {e}")
            return None

    def overlay_image(self, frame, overlay_img, y_offset, x_offset):
        try:
            if overlay_img.shape[2] == 4:
                alpha = overlay_img[:, :, 3] / 255.0
                alpha = np.expand_dims(alpha, axis=2)
                for c in range(3):
                    frame[y_offset:y_offset + overlay_img.shape[0],
                    x_offset:x_offset + overlay_img.shape[1], c] = \
                        (1 - alpha[:, :, 0]) * frame[y_offset:y_offset + overlay_img.shape[0],
                                               x_offset:x_offset + overlay_img.shape[1], c] + \
                        alpha[:, :, 0] * overlay_img[:, :, c]
            else:
                frame[y_offset:y_offset + overlay_img.shape[0],
                x_offset:x_offset + overlay_img.shape[1]] = overlay_img[:, :, :3]
        except Exception as e:
            print(f"오버레이 에러: {e}")
            print(f"Frame shape: {frame.shape}")
            print(f"Overlay shape: {overlay_img.shape}")
            print(f"Offsets: ({x_offset}, {y_offset})")

    def create_video(self):
        lines = self.read_text_file()
        if not lines:
            print("텍스트 파일이 비어있습니다.")
            return

        # 비디오 생성 (오디오 없이)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.temp_video_path, fourcc, self.fps, (self.width, self.height))

        # 오디오 세그먼트 준비 - 처음에 충분한 길이의 무음으로 시작
        total_duration = 0
        audio_segments = []
        current_time = 0

        # 1. 제목 표시 및 제목 TTS
        title_image_path = self.find_subtitle_image(1)
        title_img = self.read_image_with_pil(title_image_path)
        title_tts_path = self.find_tts_file(1)
        title_duration = self.get_wav_duration(title_tts_path) if title_tts_path else 3.0
        total_duration += title_duration * 1000  # 밀리초로 변환

        if title_tts_path:
            title_audio = AudioSegment.from_wav(title_tts_path)
            silence_before = AudioSegment.silent(duration=current_time)
            audio_segments.append(silence_before + title_audio)

        # 제목 프레임 생성
        for _ in range(int(self.fps * title_duration)):
            frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
            title_y_offset = 50
            title_x_offset = (self.width - title_img.shape[1]) // 2
            self.overlay_image(frame, title_img, title_y_offset, title_x_offset)
            out.write(frame)

        current_time += int(title_duration * 1000)  # 밀리초로 변환

        # 2. 중앙 이미지 표시 (오디오 없음)
        for _ in range(self.fps * self.center_image_duration):
            frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
            self.overlay_image(frame, title_img, 50, (self.width - title_img.shape[1]) // 2)

            center_img = self.read_image_with_pil(self.center_image_path)
            if center_img is not None:
                center_img = self.resize_image(center_img)
                y_offset = (self.height - center_img.shape[0]) // 2
                x_offset = (self.width - center_img.shape[1]) // 2
                self.overlay_image(frame, center_img, y_offset, x_offset)
            out.write(frame)

        current_time += self.center_image_duration * 1000

        # 3. 나머지 자막 및 TTS
        for i, line in enumerate(lines[1:], 2):
            image_path = self.find_subtitle_image(i)
            subtitle_img = self.read_image_with_pil(image_path)
            tts_path = self.find_tts_file(i)
            duration = self.get_wav_duration(tts_path) if tts_path else 3.0

            # TTS 오디오 추가
            if tts_path:
                audio = AudioSegment.from_wav(tts_path)
                silence_before = AudioSegment.silent(duration=current_time)
                audio_segments.append(silence_before + audio)
                print(f"Adding audio at position {current_time}ms: {tts_path}")

            # 프레임 생성
            for _ in range(int(self.fps * duration)):
                frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)

                # 제목 표시 (상단)
                self.overlay_image(frame, title_img, 50, (self.width - title_img.shape[1]) // 2)

                # 중앙 이미지
                center_img = self.read_image_with_pil(self.center_image_path)
                if center_img is not None:
                    center_img = self.resize_image(center_img)
                    center_y_offset = (self.height - center_img.shape[0]) // 2
                    center_x_offset = (self.width - center_img.shape[1]) // 2
                    self.overlay_image(frame, center_img, center_y_offset, center_x_offset)

                # 현재 자막
                if subtitle_img is not None:
                    subtitle_y_offset = self.height - subtitle_img.shape[0] - 50
                    subtitle_x_offset = (self.width - subtitle_img.shape[1]) // 2
                    self.overlay_image(frame, subtitle_img, subtitle_y_offset, subtitle_x_offset)

                out.write(frame)

            current_time += int(duration * 1000)

        out.release()

        # 모든 오디오 세그먼트 합치기
        if audio_segments:
            # 가장 긴 세그먼트의 길이 찾기
            max_length = max(segment.duration_seconds for segment in audio_segments) * 1000
            # 충분한 길이의 빈 오디오 생성
            final_audio = AudioSegment.silent(duration=int(max_length))

            # 각 세그먼트를 해당 위치에 오버레이
            for segment in audio_segments:
                final_audio = final_audio.overlay(segment, position=0)

            # WAV 형식으로 저장
            final_audio.export(self.temp_audio_path, format="wav", parameters=["-ac", "2", "-ar", "44100"])
            print(f"Audio file created: {self.temp_audio_path}")

        # 비디오와 오디오 합치기
        print("비디오와 오디오를 합치는 중...")
        import subprocess

        try:
            # FFmpeg를 사용하여 비디오와 오디오 합치기
            command = [
                'ffmpeg', '-y',
                '-i', self.temp_video_path,
                '-i', self.temp_audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                self.output_path
            ]
            print("Executing FFmpeg command:", ' '.join(command))

            subprocess.run(command, check=True)
            print("비디오와 오디오 합성이 완료되었습니다.")

            # 임시 파일 삭제
            os.remove(self.temp_video_path)
            os.remove(self.temp_audio_path)
        except subprocess.CalledProcessError as e:
            print(f"FFmpeg 실행 중 오류 발생: {e}")
        except Exception as e:
            print(f"오류 발생: {e}")

        print("비디오 생성이 완료되었습니다.")


def main():
    # 경로 설정
    text_path = r"C:\Users\ska00\Desktop\AutoMeme\txt\content.txt"
    image_folder = r"C:\Users\ska00\Desktop\AutoMeme\voice"
    center_image_path = r"C:\Users\ska00\Desktop\AutoMeme\Images\center_image.png"
    output_path = r"C:\Users\ska00\Desktop\AutoMeme\output.mp4"

    # 비디오 생성
    generator = VideoGenerator(text_path, image_folder, center_image_path, output_path)
    generator.create_video()


if __name__ == "__main__":
    main()