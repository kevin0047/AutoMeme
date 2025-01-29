import cv2
import numpy as np
from PIL import Image
import os
import wave
from pydub import AudioSegment
import subprocess
import winsound
class VideoGenerator:
    def __init__(self, text_path, image_folder, output_path):
        self.text_path = text_path
        self.image_folder = image_folder
        self.output_path = output_path
        self.temp_video_path = os.path.join(os.path.dirname(output_path), "temp_video.mp4")
        self.temp_audio_path = os.path.join(os.path.dirname(output_path), "temp_audio.wav")
        self.width = 1370
        self.height = 1080
        self.fps = 30
        self.sequence_image_duration = 1
        self.images_folder = os.path.join(os.path.dirname(text_path), "..", "Images")  # 수정된 부분
        self.current_subtitles = []
        self.max_subtitles = 4

    def is_sequence_number(self, text):
        """문자열이 숫자로만 이루어져 있는지 확인"""
        return text.strip().isdigit() if text else False

    def get_next_element_type(self, lines, current_index):
        """다음 요소의 타입을 반환 (이미지 또는 텍스트)
        마지막 요소인 경우 'last'를 반환"""
        if current_index + 1 >= len(lines):
            return "last"  # 마지막 요소인 경우

        next_line = lines[current_index + 1]
        return "image" if self.is_sequence_number(next_line) else "text"
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

    def get_gif_info(self, gif_path):
        """GIF 파일의 프레임과 재생 시간 정보를 반환"""
        try:
            gif = Image.open(gif_path)
            frames = []
            durations = []
            total_duration = 0

            try:
                while True:
                    duration = gif.info.get('duration', 100)  # 기본값 100ms
                    frame = cv2.cvtColor(np.array(gif.convert('RGBA')), cv2.COLOR_RGBA2BGRA)
                    frames.append(frame)
                    durations.append(duration)
                    total_duration += duration
                    gif.seek(gif.tell() + 1)
            except EOFError:
                pass

            return frames, durations, total_duration / 1000.0  # 총 재생시간을 초 단위로 반환
        except Exception as e:
            print(f"GIF 처리 중 오류 발생: {e}")
            return None, None, None

    def get_video_info(self, video_path):
        """MP4 파일의 프레임과 재생 시간 정보를 반환"""
        try:
            cap = cv2.VideoCapture(video_path)
            frames = []

            # 비디오 정보 가져오기
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps

            # 모든 프레임 읽기
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                # BGRA 형식으로 변환
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2BGRA)
                frames.append(frame)

            cap.release()
            return frames, duration
        except Exception as e:
            print(f"비디오 처리 중 오류 발생: {e}")
            return None, None

    def find_tts_file(self, index):
        """해당 인덱스의 TTS 파일 찾기"""
        prefix = f"tts{index}_"  # 언더스코어 추가
        matching_files = []
        for filename in os.listdir(self.image_folder):
            if filename.startswith(prefix) and filename.endswith('.wav'):
                matching_files.append(filename)

        if matching_files:
            return os.path.join(self.image_folder, matching_files[0])
        return None

    def resize_image(self, image, max_width=1340, max_height=850):
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
        prefix = f"subtitle_{index}_"  # 언더스코어 추가
        matching_files = []
        for filename in os.listdir(self.image_folder):
            if filename.startswith(prefix) and filename.lower().endswith('.png'):
                matching_files.append(filename)

        if matching_files:
            return os.path.join(self.image_folder, matching_files[0])
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
        """PIL을 사용하여 이미지 읽기 (GIF, MP4 지원)"""
        try:
            if image_path is None:
                print(f"이미지 경로가 None입니다.")
                return None, None, None, None

            if not os.path.exists(image_path):
                print(f"이미지 파일이 존재하지 않습니다: {image_path}")
                return None, None, None, None

            # 파일 확장자 확인
            ext = os.path.splitext(image_path)[1].lower()
            if ext == '.gif':
                frames, durations, total_duration = self.get_gif_info(image_path)
                return frames, durations, total_duration, 'gif'
            elif ext == '.mp4':
                frames, duration = self.get_video_info(image_path)
                return frames, None, duration, 'mp4'
            else:
                pil_image = Image.open(image_path)
                pil_image = pil_image.convert('RGBA')
                numpy_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGBA2BGRA)
                return numpy_image, None, None, 'image'

        except Exception as e:
            print(f"이미지 로딩 에러 ({image_path}): {e}")
            return None, None, None, None

    def find_first_sequence_image(self):
        """Images 폴더에서 첫 번째 이미지 찾기"""
        try:
            for filename in sorted(os.listdir(self.images_folder)):
                if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.mp4','.webp')):
                    return os.path.join(self.images_folder, filename)
            return None
        except Exception as e:
            print(f"첫 번째 이미지 검색 중 오류: {e}")
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

    def overlay_subtitles(self, frame, subtitles):
        """여러 줄의 자막을 오버레이"""
        if not subtitles:
            return

        total_height = sum(subtitle.shape[0] for subtitle, _ in subtitles)
        spacing = 10  # 자막 간 간격
        total_spacing = spacing * (len(subtitles) - 1)
        start_y = self.height - total_height - total_spacing - 50

        current_y = start_y
        for subtitle_img, _ in subtitles:
            subtitle_x_offset = (self.width - subtitle_img.shape[1]) // 2
            self.overlay_image(frame, subtitle_img, current_y, subtitle_x_offset)
            current_y += subtitle_img.shape[0] + spacing

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
        self.current_subtitles = []  # 현재 표시중인 자막 리스트

        # 1. 제목 표시 및 제목 TTS
        title_image_path = self.find_subtitle_image(subtitle_index)
        if title_image_path is None:
            print("제목 이미지를 찾을 수 없습니다.")
            return

        title_img = self.read_image_with_pil(title_image_path)[0]  # 첫 번째 요소만 사용
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

        # 기본 중앙 이미지 로드
        first_image_path = self.find_first_sequence_image()
        current_center_img = None
        if first_image_path:
            result = self.read_image_with_pil(first_image_path)
            if result[3] == 'gif':
                frames, durations, total_duration, _ = result
                for frame_index in range(len(frames)):
                    frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
                    current_frame = self.resize_image(frames[frame_index])

                    # 제목 표시
                    self.overlay_image(frame, title_img, 50, (self.width - title_img.shape[1]) // 2)

                    # GIF 프레임 표시
                    y_offset = (self.height - current_frame.shape[0]) // 2
                    x_offset = (self.width - current_frame.shape[1]) // 2
                    self.overlay_image(frame, current_frame, y_offset, x_offset)

                    frame_duration_sec = durations[frame_index] / 1000.0
                    for _ in range(int(self.fps * frame_duration_sec)):
                        out.write(frame)
                current_time += total_duration * 1000

            elif result[3] == 'mp4':
                frames, _, duration, _ = result
                for frame in frames:
                    resized_frame = self.resize_image(frame)
                    base_frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)

                    # 제목 표시
                    self.overlay_image(base_frame, title_img, 50, (self.width - title_img.shape[1]) // 2)

                    # 비디오 프레임 표시
                    y_offset = (self.height - resized_frame.shape[0]) // 2
                    x_offset = (self.width - resized_frame.shape[1]) // 2
                    self.overlay_image(base_frame, resized_frame, y_offset, x_offset)

                    out.write(base_frame)
                current_time += duration * 1000

            else:  # 일반 이미지
                current_center_img = result[0]
                if current_center_img is not None:
                    current_center_img = self.resize_image(current_center_img)

                    for _ in range(int(self.fps * self.sequence_image_duration)):
                        frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
                        self.overlay_image(frame, title_img, 50, (self.width - title_img.shape[1]) // 2)
                        y_offset = (self.height - current_center_img.shape[0]) // 2
                        x_offset = (self.width - current_center_img.shape[1]) // 2
                        self.overlay_image(frame, current_center_img, y_offset, x_offset)
                        out.write(frame)

                    current_time += self.sequence_image_duration * 1000

        # 나머지 내용 처리
        for i, line in enumerate(lines[1:], 2):
            print(f"처리 중인 줄 {i}: {line}")

            # create_video 메서드 내부의 이미지 처리 부분
            if self.is_sequence_number(line):
                self.current_subtitles = []  # 자막 초기화
                sequence_img_path = self.find_sequence_image(int(line))
                print(f"시퀀스 이미지 경로: {sequence_img_path}")

                # 다음 요소의 타입에 따라 지속시간 결정
                next_element_type = self.get_next_element_type(lines, i - 1)
                # 다음 요소가 이미지이거나 마지막 요소일 경우 3초
                image_duration = 3.0 if (next_element_type == "image" or next_element_type == "last") else 1.0

                if sequence_img_path:
                    result = self.read_image_with_pil(sequence_img_path)

                    if result[3] == 'gif':  # GIF 파일
                        frames, durations, total_duration, _ = result
                        frame_index = 0
                        elapsed_time = 0

                        while elapsed_time < total_duration:
                            frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
                            current_frame = self.resize_image(frames[frame_index])

                            # 제목 표시
                            self.overlay_image(frame, title_img, 50, (self.width - title_img.shape[1]) // 2)

                            # GIF 프레임 표시
                            y_offset = (self.height - current_frame.shape[0]) // 2
                            x_offset = (self.width - current_frame.shape[1]) // 2
                            self.overlay_image(frame, current_frame, y_offset, x_offset)

                            frame_duration_sec = durations[frame_index] / 1000.0
                            for _ in range(int(self.fps * frame_duration_sec)):
                                out.write(frame)

                            elapsed_time += frame_duration_sec
                            frame_index = (frame_index + 1) % len(frames)

                        current_time += total_duration * 1000

                    elif result[3] == 'mp4':  # MP4 파일
                        frames, _, duration, _ = result
                        frame_count = len(frames)

                        for frame_index in range(frame_count):
                            frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)
                            current_frame = self.resize_image(frames[frame_index])

                            # 제목 표시
                            self.overlay_image(frame, title_img, 50, (self.width - title_img.shape[1]) // 2)

                            # 비디오 프레임 표시
                            y_offset = (self.height - current_frame.shape[0]) // 2
                            x_offset = (self.width - current_frame.shape[1]) // 2
                            self.overlay_image(frame, current_frame, y_offset, x_offset)

                            out.write(frame)

                        current_time += duration * 1000


                    else:  # 일반 이미지

                        current_center_img = result[0]

                        if current_center_img is not None:

                            current_center_img = self.resize_image(current_center_img)

                            for _ in range(int(self.fps * image_duration)):  # 수정된 지속시간 사용

                                frame = np.full((self.height, self.width, 3), 255, dtype=np.uint8)

                                self.overlay_image(frame, title_img, 50, (self.width - title_img.shape[1]) // 2)

                                y_offset = (self.height - current_center_img.shape[0]) // 2

                                x_offset = (self.width - current_center_img.shape[1]) // 2

                                self.overlay_image(frame, current_center_img, y_offset, x_offset)

                                out.write(frame)

                            current_time += image_duration * 1000
                continue

            # 일반 자막과 음성 처리
            image_path = self.find_subtitle_image(subtitle_index)
            print(f"자막 이미지 경로 (인덱스 {subtitle_index}): {image_path}")

            subtitle_img = None
            if image_path:
                subtitle_img = self.read_image_with_pil(image_path)[0]  # 첫 번째 요소만 사용
                if subtitle_img is None:
                    print(f"자막 이미지를 로드할 수 없습니다: {image_path}")
                else:
                    # 현재 자막 추가
                    self.current_subtitles.append((subtitle_img, subtitle_index))
                    # 최대 4줄 유지
                    if len(self.current_subtitles) > 4:
                        self.current_subtitles.pop(0)

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

                # 여러 줄의 자막 표시
                total_height = sum(subtitle.shape[0] for subtitle, _ in self.current_subtitles)
                spacing = 10  # 자막 간 간격
                total_spacing = spacing * (len(self.current_subtitles) - 1)
                start_y = self.height - total_height - total_spacing - 50

                current_y = start_y
                for subtitle, _ in self.current_subtitles:
                    subtitle_x_offset = (self.width - subtitle.shape[1]) // 2
                    self.overlay_image(frame, subtitle, current_y, subtitle_x_offset)
                    current_y += subtitle.shape[0] + spacing

                out.write(frame)

            current_time += int(duration * 1000)
            subtitle_index += 1

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

    def combine_videos(self):
        """메인 비디오와 comments 비디오 합치기"""
        comments_path = os.path.join(os.path.dirname(self.output_path), "output_comments.mp4")
        final_output = os.path.join(os.path.dirname(self.output_path), "final_output.mp4")

        # 메인 비디오 길이 확인
        main_cap = cv2.VideoCapture(self.output_path)
        main_duration = main_cap.get(cv2.CAP_PROP_FRAME_COUNT) / main_cap.get(cv2.CAP_PROP_FPS)

        # comments 비디오 속도 조절을 위한 ffmpeg 명령어 생성
        temp_comments = os.path.join(os.path.dirname(self.output_path), "temp_comments.mp4")
        comments_cap = cv2.VideoCapture(comments_path)
        comments_duration = comments_cap.get(cv2.CAP_PROP_FRAME_COUNT) / comments_cap.get(cv2.CAP_PROP_FPS)

        # 속도 조절 계수 계산
        speed = comments_duration / main_duration

        # comments 비디오 속도 조절
        speed_command = [
            'ffmpeg', '-y',
            '-i', comments_path,
            '-filter:v', f'setpts={1 / speed}*PTS',
            '-filter:a', f'atempo={speed}',
            temp_comments
        ]
        subprocess.run(speed_command, check=True)

        # 두 비디오 합치기
        combine_command = [
            'ffmpeg', '-y',
            '-i', self.output_path,
            '-i', temp_comments,
            '-filter_complex', '[0:v][1:v]hstack=inputs=2[v]',
            '-map', '[v]',
            '-map', '0:a',
            final_output
        ]
        subprocess.run(combine_command, check=True)

        # 임시 파일 삭제
        os.remove(temp_comments)
        os.rename(final_output, self.output_path)
        winsound.PlaySound("SystemExit", winsound.SND_ALIAS)


import os


def main():
    base_dir = r"C:\Users\ska00\Desktop\AutoMeme"

    # 숫자 폴더 찾기
    folders = [f for f in os.listdir(base_dir) if f.isdigit()]
    folders.sort(key=int)

    for folder in folders:
        folder_path = os.path.join(base_dir, folder)
        output_path = os.path.join(folder_path, "output.mp4")

        # 이미 영상이 있으면 스킵
        if os.path.exists(output_path):
            print(f"폴더 {folder}의 영상이 이미 존재합니다. 스킵합니다.")
            continue

        text_path = os.path.join(folder_path, "txt", "content.txt")
        image_folder = os.path.join(folder_path, "voice")

        try:
            generator = VideoGenerator(text_path, image_folder, output_path)
            generator.create_video()
            generator.combine_videos()
            print(f"폴더 {folder} 완료")
        except Exception as e:
            print(f"폴더 {folder} 처리 중 오류 발생: {e}")





if __name__ == "__main__":
    main()