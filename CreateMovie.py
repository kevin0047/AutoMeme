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
    def __init__(self, text_path, image_folder, output_path):
        self.text_path = text_path
        self.image_folder = image_folder  # voice 폴더 (자막, 음성파일용)
        self.output_path = output_path
        self.temp_video_path = os.path.join(os.path.dirname(output_path), "temp_video.mp4")
        self.temp_audio_path = os.path.join(os.path.dirname(output_path), "temp_audio.wav")
        self.width = 1370
        self.height = 1080
        self.fps = 30
        self.sequence_image_duration = 2  # 숫자로 불러온 이미지 표시 대기 시간 (초)
        self.images_folder = r"C:\Users\ska00\Desktop\AutoMeme\Images"  # 순차 이미지 폴더

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
        """해당 인덱스의 TTS 파일 찾기"""
        prefix = f"tts{index}"
        for filename in os.listdir(self.image_folder):
            if filename.startswith(prefix) and filename.endswith('.wav'):
                return os.path.join(self.image_folder, filename)
        return None

    def resize_image(self, image, max_width=800, max_height=600):
        """이미지 크기 조정"""
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
        """텍스트 파일 읽기"""
        with open(self.text_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return [line.strip() for line in lines if line.strip()]

    def find_subtitle_image(self, index):
        """자막 이미지 파일 찾기"""
        prefix = f"subtitle_{index}_"
        for filename in os.listdir(self.image_folder):
            if filename.startswith(prefix) and filename.lower().endswith('.png'):
                return os.path.join(self.image_folder, filename)
        return None

    def find_sequence_image(self, number):
        """숫자에 해당하는 시퀀스 이미지 찾기"""
        number_str = str(number).zfill(2)
        for filename in os.listdir(self.images_folder):
            if filename.startswith(f"{number_str}_"):
                return os.path.join(self.images_folder, filename)
        return None

    def is_sequence_number(self, text):
        """문자열이 숫자로만 이루어져 있는지 확인"""
        return text.strip().isdigit()

    def read_image_with_pil(self, image_path):
        """PIL을 사용하여 이미지 읽기"""
        try:
            if image_path is None:
                print(f"이미지 경로가 None입니다.")
                return None

            if not os.path.exists(image_path):
                print(f"이미지 파일이 존재하지 않습니다: {image_path}")
                return None

            pil_image = Image.open(image_path)
            pil_image = pil_image.convert('RGBA')
            numpy_image = np.array(pil_image)
            return cv2.cvtColor(numpy_image, cv2.COLOR_RGBA2BGRA)
        except Exception as e:
            print(f"이미지 로딩 에러 ({image_path}): {e}")
            return None

    def overlay_image(self, frame, overlay_img, y_offset, x_offset):
        """이미지 오버레이"""
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
        """비디오 생성"""
        lines = self.read_text_file()
        if not lines:
            print("텍스트 파일이 비어있습니다.")
            return

        print("텍스트 파일 내용:")
        for i, line in enumerate(lines):
            print(f"{i + 1}: {line}")

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.temp_video_path, fourcc, self.fps, (self.width, self.height))

        audio_segments = []
        current_time = 0
        subtitle_index = 1  # 자막 인덱스 별도 관리

        # 1. 제목 표시 및 제목 TTS
        title_image_path = self.find_subtitle_image(subtitle_index)
        if title_image_path is None:
            print("제목 이미지를 찾을 수 없습니다.")
            return

        title_img = self.read_image_with_pil(title_image_path)
        if title_img is None:
            print("제목 이미지를 로드할 수 없습니다.")
            return

        title_tts_path = self.find_tts_file(subtitle_index)
        title_duration = self.get_wav_duration(title_tts_path) if title_tts_path else 3.0
        subtitle_index += 1  # 제목 처리 후 인덱스 증가

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

        current_time += int(title_duration * 1000)
        current_center_img = None

        # 나머지 내용 처리
        for i, line in enumerate(lines[1:], 2):
            print(f"처리 중인 줄 {i}: {line}")

            if self.is_sequence_number(line):
                # 숫자를 만나면 새로운 중앙 이미지로 교체
                sequence_img_path = self.find_sequence_image(int(line))
                print(f"시퀀스 이미지 경로: {sequence_img_path}")

                if sequence_img_path:
                    current_center_img = self.read_image_with_pil(sequence_img_path)
                    if current_center_img is not None:
                        current_center_img = self.resize_image(current_center_img)
                    else:
                        print(f"시퀀스 이미지를 로드할 수 없습니다: {sequence_img_path}")

                # 숫자 이미지 전환 시 대기 시간 추가
                for _ in range(int(self.fps * self.sequence_image_duration)):
                    frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
                    # 제목 표시
                    self.overlay_image(frame, title_img, 50, (self.width - title_img.shape[1]) // 2)
                    # 중앙 이미지 표시
                    if current_center_img is not None:
                        y_offset = (self.height - current_center_img.shape[0]) // 2
                        x_offset = (self.width - current_center_img.shape[1]) // 2
                        self.overlay_image(frame, current_center_img, y_offset, x_offset)
                    out.write(frame)

                current_time += self.sequence_image_duration * 1000
                continue

            # 일반 자막과 음성 처리
            image_path = self.find_subtitle_image(subtitle_index)
            print(f"자막 이미지 경로 (인덱스 {subtitle_index}): {image_path}")

            subtitle_img = None
            if image_path:
                subtitle_img = self.read_image_with_pil(image_path)
                if subtitle_img is None:
                    print(f"자막 이미지를 로드할 수 없습니다: {image_path}")

            tts_path = self.find_tts_file(subtitle_index)
            print(f"TTS 파일 경로 (인덱스 {subtitle_index}): {tts_path}")

            duration = self.get_wav_duration(tts_path) if tts_path else 3.0

            if tts_path:
                audio = AudioSegment.from_wav(tts_path)
                silence_before = AudioSegment.silent(duration=current_time)
                audio_segments.append(silence_before + audio)

            for _ in range(int(self.fps * duration)):
                frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
                # 제목 표시
                self.overlay_image(frame, title_img, 50, (self.width - title_img.shape[1]) // 2)
                # 현재 중앙 이미지 표시
                if current_center_img is not None:
                    y_offset = (self.height - current_center_img.shape[0]) // 2
                    x_offset = (self.width - current_center_img.shape[1]) // 2
                    self.overlay_image(frame, current_center_img, y_offset, x_offset)
                # 자막 표시
                if subtitle_img is not None:
                    subtitle_y_offset = self.height - subtitle_img.shape[0] - 50
                    subtitle_x_offset = (self.width - subtitle_img.shape[1]) // 2
                    self.overlay_image(frame, subtitle_img, subtitle_y_offset, subtitle_x_offset)
                out.write(frame)

            current_time += int(duration * 1000)
            subtitle_index += 1  # 일반 텍스트 처리 후 자막 인덱스 증가

        out.release()

        # 오디오 처리 및 비디오 합성
        if audio_segments:
            max_length = max(segment.duration_seconds for segment in audio_segments) * 1000
            final_audio = AudioSegment.silent(duration=int(max_length))
            for segment in audio_segments:
                final_audio = final_audio.overlay(segment, position=0)
            final_audio.export(self.temp_audio_path, format="wav", parameters=["-ac", "2", "-ar", "44100"])

        try:
            command = [
                'ffmpeg', '-y',
                '-i', self.temp_video_path,
                '-i', self.temp_audio_path,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                self.output_path
            ]
            subprocess.run(command, check=True)
            os.remove(self.temp_video_path)
            os.remove(self.temp_audio_path)
        except Exception as e:
            print(f"오류 발생: {e}")

        print("비디오 생성이 완료되었습니다.")


def main():
    # 경로 설정
    text_path = r"C:\Users\ska00\Desktop\AutoMeme\txt\content.txt"
    image_folder = r"C:\Users\ska00\Desktop\AutoMeme\voice"
    output_path = r"C:\Users\ska00\Desktop\AutoMeme\output.mp4"

    # 비디오 생성
    generator = VideoGenerator(text_path, image_folder, output_path)
    generator.create_video()


if __name__ == "__main__":
    main()