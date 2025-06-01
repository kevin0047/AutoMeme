import os
import tkinter as tk
from tkinter import filedialog, messagebox
from moviepy import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips, ColorClip, CompositeVideoClip
from PIL import Image, ImageSequence
import numpy as np


def select_audio_file():
    """오디오 파일 또는 비디오 파일 선택"""
    file_path = filedialog.askopenfilename(
        title="오디오/비디오 파일 선택",
        filetypes=[
            ("모든 지원 파일", "*.mp3;*.wav;*.m4a;*.aac;*.mp4;*.avi;*.mov;*.mkv"),
            ("오디오 파일", "*.mp3;*.wav;*.m4a;*.aac"),
            ("비디오 파일", "*.mp4;*.avi;*.mov;*.mkv"),
            ("모든 파일", "*.*")
        ]
    )
    return file_path


def select_image_files():
    """이미지 또는 GIF 파일 여러개 선택"""
    file_paths = filedialog.askopenfilenames(
        title="이미지/GIF 파일 선택 (여러 개 선택 가능)",
        filetypes=[
            ("이미지 파일", "*.jpg;*.jpeg;*.png;*.bmp;*.gif"),
            ("모든 파일", "*.*")
        ]
    )
    return list(file_paths)


def extract_audio_from_video(video_path):
    """비디오 파일에서 오디오 추출"""
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        return audio
    except Exception as e:
        print(f"오디오 추출 중 오류: {e}")
        return None


def preprocess_image_with_pil(image_path, target_width=1920, target_height=1080, margin_ratio=0.1):
    """PIL을 사용해서 이미지를 리사이즈 (확대/축소 모두 지원)"""
    try:
        # PIL로 이미지 열기
        img = Image.open(image_path)

        # RGBA 모드로 변환 (투명도 지원)
        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        # 마진을 고려한 실제 사용 가능한 영역
        usable_width = int(target_width * (1 - margin_ratio * 2))
        usable_height = int(target_height * (1 - margin_ratio * 2))

        original_width, original_height = img.size
        original_ratio = original_width / original_height
        usable_ratio = usable_width / usable_height

        # 원본이 사용 가능 영역보다 작은지 확인
        if original_width < usable_width and original_height < usable_height:
            print(f"이미지 크기가 작아서 확대합니다: {original_width}x{original_height} -> 목표 영역: {usable_width}x{usable_height}")

        # 비율을 유지하면서 새로운 크기 계산
        if original_ratio > usable_ratio:
            # 원본이 더 넓음 - 너비를 기준으로 맞춤
            new_width = usable_width
            new_height = int(usable_width / original_ratio)
        else:
            # 원본이 더 높음 - 높이를 기준으로 맞춤
            new_height = usable_height
            new_width = int(usable_height * original_ratio)

        print(f"이미지 리사이즈: {original_width}x{original_height} -> {new_width}x{new_height}")

        # 이미지 리사이즈 (확대 또는 축소)
        if new_width > original_width or new_height > original_height:
            # 확대의 경우 고품질 알고리즘 사용
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        else:
            # 축소의 경우 thumbnail 사용
            img.thumbnail((new_width, new_height), Image.Resampling.LANCZOS)
            # thumbnail은 원본보다 작게만 만들므로, 정확한 크기로 맞춤
            if img.size != (new_width, new_height):
                img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 새로운 흰 배경 이미지 생성
        background = Image.new('RGBA', (target_width, target_height), (255, 255, 255, 255))

        # 중앙에 이미지 배치
        x = (target_width - img.width) // 2
        y = (target_height - img.height) // 2
        background.paste(img, (x, y), img)

        # RGB로 변환 (MoviePy 호환성)
        background = background.convert('RGB')

        # 임시 파일로 저장
        temp_path = image_path + "_temp.png"
        background.save(temp_path)

        return temp_path

    except Exception as e:
        print(f"이미지 전처리 중 오류: {e}")
        return None


def preprocess_gif_with_pil(gif_path, target_width=1920, target_height=1080, margin_ratio=0.1, target_duration=1.0):
    """PIL을 사용해서 GIF를 프레임별로 처리하고 새로운 GIF 생성"""
    try:
        # PIL로 GIF 열기
        gif = Image.open(gif_path)

        # 마진을 고려한 실제 사용 가능한 영역
        usable_width = int(target_width * (1 - margin_ratio * 2))
        usable_height = int(target_height * (1 - margin_ratio * 2))

        # 원본 정보 수집
        original_width, original_height = gif.size
        original_ratio = original_width / original_height
        usable_ratio = usable_width / usable_height

        print(f"GIF 원본 크기: {original_width}x{original_height}")

        # 프레임 수집
        frames = []
        durations = []

        for frame_num, frame in enumerate(ImageSequence.Iterator(gif)):
            # 프레임을 RGBA로 변환
            frame = frame.convert('RGBA')
            durations.append(frame.info.get('duration', 100))  # 기본 100ms
            frames.append(frame)

        print(f"총 프레임 수: {len(frames)}")
        print(f"원본 프레임 지속시간들: {durations[:5]}..." if len(durations) > 5 else f"원본 프레임 지속시간들: {durations}")

        # 목표 FPS 계산 (1초에 맞추기)
        total_duration_ms = sum(durations)
        target_duration_ms = target_duration * 1000
        speed_factor = total_duration_ms / target_duration_ms if total_duration_ms > target_duration_ms else 1

        print(f"원본 총 길이: {total_duration_ms}ms, 목표: {target_duration_ms}ms, 속도 배율: {speed_factor:.2f}")

        # 새로운 크기 계산
        if original_ratio > usable_ratio:
            new_width = usable_width
            new_height = int(usable_width / original_ratio)
        else:
            new_height = usable_height
            new_width = int(usable_height * original_ratio)

        print(f"GIF 리사이즈: {original_width}x{original_height} -> {new_width}x{new_height}")

        # 중앙 배치 좌표 계산
        x = (target_width - new_width) // 2
        y = (target_height - new_height) // 2
        print(f"GIF 중앙 배치 좌표: ({x}, {y})")

        # 프레임 처리
        processed_frames = []

        # 속도 조절을 위한 프레임 선택
        if speed_factor > 1:
            # 빠르게 재생 - 일부 프레임 건너뛰기
            selected_indices = np.linspace(0, len(frames) - 1, max(12, int(len(frames) / speed_factor)), dtype=int)
            selected_frames = [frames[i] for i in selected_indices]
            frame_duration = target_duration_ms / len(selected_frames)
            print(f"속도 조절: {len(frames)}프레임 -> {len(selected_frames)}프레임 선택")
        else:
            # 정상 속도 또는 느리게
            selected_frames = frames
            frame_duration = target_duration_ms / len(selected_frames)

        for frame in selected_frames:
            # 프레임 리사이즈
            resized_frame = frame.resize((new_width, new_height), Image.Resampling.LANCZOS)

            # 흰 배경 생성
            background = Image.new('RGBA', (target_width, target_height), (255, 255, 255, 255))

            # 중앙에 프레임 배치
            background.paste(resized_frame, (x, y), resized_frame)

            # RGB로 변환
            processed_frames.append(background.convert('RGB'))

        # 새로운 GIF 저장
        temp_gif_path = gif_path + "_processed.gif"

        if processed_frames:
            processed_frames[0].save(
                temp_gif_path,
                save_all=True,
                append_images=processed_frames[1:],
                duration=int(frame_duration),
                loop=0
            )
            print(f"처리된 GIF 저장: {len(processed_frames)}프레임, 프레임당 {frame_duration:.1f}ms")
            return temp_gif_path
        else:
            print("처리된 프레임이 없습니다.")
            return None

    except Exception as e:
        print(f"GIF 전처리 중 오류: {e}")
        return None


def process_gif(gif_path, duration=1.0):
    """GIF 파일을 1초로 조정하고 1920x1080으로 리사이즈 (PIL 전처리 사용)"""
    try:
        # PIL로 GIF 전처리
        processed_gif_path = preprocess_gif_with_pil(gif_path, target_duration=duration)
        if not processed_gif_path:
            return None

        # 전처리된 GIF를 VideoFileClip으로 로드
        gif_clip = VideoFileClip(processed_gif_path)

        print(f"처리된 GIF 클립 길이: {gif_clip.duration}초")

        # 정확히 1초로 조정
        if abs(gif_clip.duration - duration) > 0.1:
            try:
                gif_clip = gif_clip.set_duration(duration)
            except:
                pass

        # 임시 파일 삭제를 위한 안전한 처리
        def cleanup_temp_file():
            """임시 파일을 안전하게 삭제"""
            import time
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    if processed_gif_path != gif_path and os.path.exists(processed_gif_path):
                        os.remove(processed_gif_path)
                        print(f"임시 파일 삭제 완료: {processed_gif_path}")
                    break
                except (PermissionError, OSError) as e:
                    if attempt < max_attempts - 1:
                        print(f"임시 파일 삭제 재시도 {attempt + 1}/{max_attempts}: {e}")
                        time.sleep(0.5)  # 0.5초 대기 후 재시도
                    else:
                        print(f"임시 파일 삭제 실패 (무시됨): {e}")

        # 나중에 정리할 수 있도록 gif_clip에 정리 함수 추가
        gif_clip._cleanup_temp_file = cleanup_temp_file
        gif_clip._temp_file_path = processed_gif_path

        return gif_clip

    except Exception as e:
        print(f"GIF 처리 중 오류: {e}")
        # 오류 발생시에도 임시 파일 정리 시도
        try:
            if 'processed_gif_path' in locals() and processed_gif_path != gif_path and os.path.exists(
                    processed_gif_path):
                os.remove(processed_gif_path)
        except:
            pass
        return None


def process_image(image_path, duration=1.0):
    """이미지를 1920x1080으로 리사이즈하고 1초 클립 생성 (마진 포함)"""
    try:
        # PIL로 이미지 전처리 (확대/축소 모두 지원)
        processed_image_path = preprocess_image_with_pil(image_path)
        if not processed_image_path:
            return None

        # 전처리된 이미지로 클립 생성
        image_clip = ImageClip(processed_image_path, duration=duration)

        # 임시 파일 삭제
        if processed_image_path != image_path and os.path.exists(processed_image_path):
            os.remove(processed_image_path)

        return image_clip

    except Exception as e:
        print(f"이미지 처리 중 오류: {e}")
        return None


def create_video(audio_path, image_path, output_path):
    """최종 비디오 생성 (1920x1080, 흰 배경, 마진 포함)"""
    try:
        # 오디오 로드
        if audio_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
            # 비디오 파일에서 오디오 추출
            audio = extract_audio_from_video(audio_path)
            if not audio:
                return False
        else:
            # 오디오 파일 직접 로드
            audio = AudioFileClip(audio_path)

        # 오디오를 1초로 자르기
        try:
            audio = audio.subclipped(0, min(1.0, audio.duration))
        except AttributeError:
            try:
                audio = audio.subclip(0, min(1.0, audio.duration))
            except AttributeError:
                audio = audio.set_duration(min(1.0, audio.duration))

        # 이미지/GIF 처리
        if image_path.lower().endswith('.gif'):
            # GIF 파일 처리 (PIL 전처리 사용)
            video_clip = process_gif(image_path, 1.0)
            if not video_clip:
                return False
        else:
            # 일반 이미지 파일 처리
            video_clip = process_image(image_path, 1.0)
            if not video_clip:
                return False

        # 오디오와 비디오 결합
        try:
            final_video = video_clip.set_audio(audio)
        except AttributeError:
            try:
                final_video = video_clip.with_audio(audio)
            except AttributeError:
                # CompositeVideoClip의 경우
                final_video = video_clip.set_audio(audio) if hasattr(video_clip, 'set_audio') else video_clip

        # 출력 파일 저장 (1920x1080, 24fps)
        final_video.write_videofile(
            output_path,
            fps=24,
            codec='libx264',
            audio_codec='aac',
            preset='medium',
            bitrate='8000k'
        )

        # 리소스 정리
        audio.close()
        video_clip.close()
        final_video.close()

        # GIF 임시 파일 정리 (video_clip이 닫힌 후)
        if hasattr(video_clip, '_cleanup_temp_file'):
            video_clip._cleanup_temp_file()

        return True

    except Exception as e:
        print(f"비디오 생성 중 오류: {e}")

        # 오류 발생시에도 리소스 정리
        try:
            if 'audio' in locals():
                audio.close()
            if 'video_clip' in locals():
                if hasattr(video_clip, '_cleanup_temp_file'):
                    video_clip._cleanup_temp_file()
                video_clip.close()
            if 'final_video' in locals():
                final_video.close()
        except:
            pass

        return False


def generate_output_path(audio_path, image_path, output_dir):
    """출력 파일 경로 자동 생성"""
    # 오디오 파일명 (확장자 제거)
    audio_name = os.path.splitext(os.path.basename(audio_path))[0]

    # 이미지 파일명 (확장자 제거)
    image_name = os.path.splitext(os.path.basename(image_path))[0]

    # 출력 파일명: 오디오명_이미지명.mp4
    output_filename = f"{audio_name}_{image_name}.mp4"

    # 전체 경로
    output_path = os.path.join(output_dir, output_filename)

    # 파일이 이미 존재하면 번호 추가
    counter = 1
    while os.path.exists(output_path):
        output_filename = f"{audio_name}_{image_name}_{counter}.mp4"
        output_path = os.path.join(output_dir, output_filename)
        counter += 1

    return output_path


def main():
    """메인 함수"""
    root = tk.Tk()
    root.withdraw()  # 메인 윈도우 숨기기

    print("=== 1초 영상 제작기 (1920x1080, 흰 배경, 마진 포함, 다중 파일 지원) ===")

    # 오디오/비디오 파일 선택
    print("1. 오디오 파일 또는 비디오 파일을 선택하세요...")
    audio_path = select_audio_file()
    if not audio_path:
        print("파일 선택이 취소되었습니다.")
        return

    print(f"선택된 오디오/비디오: {os.path.basename(audio_path)}")

    # 이미지/GIF 파일 여러개 선택
    print("2. 이미지 또는 GIF 파일을 선택하세요 (여러 개 선택 가능)...")
    image_paths = select_image_files()
    if not image_paths:
        print("파일 선택이 취소되었습니다.")
        return

    print(f"선택된 이미지 파일 수: {len(image_paths)}")
    for i, path in enumerate(image_paths, 1):
        print(f"  {i}. {os.path.basename(path)}")

    # 출력 폴더 선택
    output_dir = filedialog.askdirectory(
        title="출력 비디오 파일을 저장할 폴더 선택"
    )

    if not output_dir:
        print("저장 폴더 선택이 취소되었습니다.")
        return

    print(f"출력 폴더: {output_dir}")
    print(f"\n3. {len(image_paths)}개의 1920x1080 비디오 생성 시작...")

    # 각 이미지에 대해 비디오 생성
    success_count = 0
    fail_count = 0
    failed_files = []

    for i, image_path in enumerate(image_paths, 1):
        print(f"\n[{i}/{len(image_paths)}] 처리 중: {os.path.basename(image_path)}")

        # 출력 파일 경로 자동 생성
        output_path = generate_output_path(audio_path, image_path, output_dir)

        print(f"출력 파일: {os.path.basename(output_path)}")

        # 비디오 생성
        success = create_video(audio_path, image_path, output_path)

        if success:
            print(f"✅ 성공: {os.path.basename(output_path)}")
            success_count += 1
        else:
            print(f"❌ 실패: {os.path.basename(image_path)}")
            fail_count += 1
            failed_files.append(os.path.basename(image_path))

    # 결과 요약
    print(f"\n=== 작업 완료 ===")
    print(f"총 파일 수: {len(image_paths)}")
    print(f"성공: {success_count}개")
    print(f"실패: {fail_count}개")

    if failed_files:
        print(f"실패한 파일들: {', '.join(failed_files)}")

    # 메시지 박스로 결과 표시
    if fail_count == 0:
        messagebox.showinfo("완료", f"모든 비디오가 성공적으로 생성되었습니다!\n\n총 {success_count}개 파일\n저장 위치: {output_dir}")
    else:
        messagebox.showwarning("완료",
                               f"비디오 생성이 완료되었습니다.\n\n성공: {success_count}개\n실패: {fail_count}개\n\n저장 위치: {output_dir}")


if __name__ == "__main__":
    main()