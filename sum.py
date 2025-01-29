import os
from subprocess import call
import random


def get_video_duration(video_path):
    """영상 길이를 초 단위로 반환"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        video_path
    ]
    try:
        import subprocess
        duration = float(subprocess.check_output(cmd).decode('utf-8').strip())
        return duration
    except:
        return 0


def get_audio_duration(audio_path):
    """오디오 길이를 초 단위로 반환"""
    cmd = [
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        audio_path
    ]
    try:
        import subprocess
        duration = float(subprocess.check_output(cmd).decode('utf-8').strip())
        return duration
    except:
        return 0


def merge_videos_with_bgm(base_folder, transition_video, bgm_folder, output_file):
    # 배경음악 파일 목록
    bgm_files = [f for f in os.listdir(bgm_folder) if f.endswith(('.mp3', '.wav', '.m4a'))]
    if not bgm_files:
        print("배경음악 파일을 찾을 수 없습니다.")
        return

    # 숫자 폴더 정렬
    number_folders = []
    for folder in os.listdir(base_folder):
        if folder.isdigit():
            number_folders.append(folder)
    number_folders.sort(key=int)

    # 각 영상에 배경음악 추가
    processed_videos = []
    for folder in number_folders:
        video_path = os.path.join(base_folder, folder, "final_output.mp4")
        if not os.path.exists(video_path):
            print(f"경고: {folder}폴더에서 final_output.mp4를 찾을 수 없습니다.")
            continue

        # 랜덤 배경음악 선택
        bgm_file = os.path.join(bgm_folder, random.choice(bgm_files))
        print(f"{folder} 폴더 영상의 배경음악: {os.path.basename(bgm_file)}")

        # 비디오와 오디오 길이 확인
        video_duration = get_video_duration(video_path)
        audio_duration = get_audio_duration(bgm_file)

        # 랜덤 시작 지점 선택 (음악이 영상보다 길 경우)
        if audio_duration > video_duration:
            max_start = audio_duration - video_duration
            start_time = random.uniform(0, max_start)
        else:
            start_time = 0

        # 임시 출력 파일
        temp_output = f"temp_with_bgm_{folder}.mp4"

        # 배경음악 추가
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', bgm_file,
            '-filter_complex',
            f'[1:a]atrim=start={start_time}:duration={video_duration},volume=0.07[bgm];[0:a][bgm]amix=duration=first:dropout_transition=0',
            '-c:v', 'copy',
            '-shortest',
            temp_output
        ]
        call(cmd)
        processed_videos.append(temp_output)

    # 전환 영상 포함하여 최종 목록 생성
    final_video_list = []
    for i, video in enumerate(processed_videos):
        final_video_list.append(video)
        if i < len(processed_videos) - 1:  # 마지막이 아니면 전환 영상 추가
            final_video_list.append(transition_video)

    # 임시 TS 파일 생성
    temp_ts_files = []
    for i, video in enumerate(final_video_list):
        temp_ts = f"temp_{i}.ts"
        cmd = [
            'ffmpeg',
            '-i', video,
            '-c', 'copy',
            '-bsf:v', 'h264_mp4toannexb',
            '-f', 'mpegts',
            temp_ts
        ]
        call(cmd)
        temp_ts_files.append(temp_ts)

    # 최종 병합
    concat_list = '|'.join(temp_ts_files)
    cmd = [
        'ffmpeg',
        '-i', f"concat:{concat_list}",
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        output_file
    ]

    try:
        call(cmd)
        print(f"완료: {output_file}에 저장되었습니다.")
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        # 임시 파일 삭제
        for temp_file in temp_ts_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        for temp_file in processed_videos:
            if os.path.exists(temp_file):
                os.remove(temp_file)


# 사용 예시
base_folder = r"C:\Users\ska00\Desktop\AutoMeme"
output_file = r"C:\Users\ska00\Desktop\AutoMeme\final_merged.mp4"
transition_video = "전환.mp4"
bgm_folder = r"C:\Users\ska00\PycharmProjects\AutoMeme\음악"

merge_videos_with_bgm(base_folder, transition_video, bgm_folder, output_file)