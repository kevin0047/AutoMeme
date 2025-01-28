import os
from subprocess import call
import random

def merge_videos_with_bgm(base_folder, transition_video, bgm_folder, output_file):
    # 배경음악 랜덤 선택
    bgm_files = [f for f in os.listdir(bgm_folder) if f.endswith(('.mp3', '.wav', '.m4a'))]
    if not bgm_files:
        print("배경음악 파일을 찾을 수 없습니다.")
        return
    bgm_file = os.path.join(bgm_folder, random.choice(bgm_files))
    print(f"선택된 배경음악: {os.path.basename(bgm_file)}")

    number_folders = []
    for folder in os.listdir(base_folder):
        if folder.isdigit():
            number_folders.append(folder)
    number_folders.sort(key=int)

    video_files = []
    for folder in number_folders:
        video_path = os.path.join(base_folder, folder, "final_output.mp4")
        if os.path.exists(video_path):
            video_files.append(video_path)
            if folder != number_folders[-1]:
                video_files.append(transition_video)
        else:
            print(f"경고: {folder}폴더에서 final_output.mp4를 찾을 수 없습니다.")

    if not video_files:
        print("병합할 영상 파일을 찾을 수 없습니다.")
        return

    # 중간 파일 생성
    temp_files = []
    for i, video in enumerate(video_files):
        temp_output = f"temp_{i}.ts"
        cmd = [
            'ffmpeg',
            '-i', video,
            '-c', 'copy',
            '-bsf:v', 'h264_mp4toannexb',
            '-f', 'mpegts',
            temp_output
        ]
        call(cmd)
        temp_files.append(temp_output)

    # 중간 병합 파일 생성
    temp_merged = "temp_merged.mp4"
    concat_list = '|'.join(temp_files)
    cmd = [
        'ffmpeg',
        '-i', f"concat:{concat_list}",
        '-c', 'copy',
        '-bsf:a', 'aac_adtstoasc',
        temp_merged
    ]
    call(cmd)

    # 배경음악 추가 (영상 길이에 맞춰서)
    cmd = [
        'ffmpeg',
        '-i', temp_merged,
        '-i', bgm_file,
        '-filter_complex',
        '[1:a]aloop=loop=-1:size=2e+09[a];[a]volume=0.07[bgm];[0:a][bgm]amix=duration=first:dropout_transition=0',
        '-c:v', 'copy',
        '-shortest',
        output_file
    ]

    try:
        call(cmd)
        print(f"완료: {output_file}에 저장되었습니다.")
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        # 임시 파일 삭제
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        if os.path.exists(temp_merged):
            os.remove(temp_merged)

# 사용 예시
base_folder = r"C:\Users\ska00\Desktop\AutoMeme"  # AutoMeme 폴더 경로
output_file = r"C:\Users\ska00\Desktop\AutoMeme\final_merged.mp4"  # 최종 출력 파일 경로
transition_video = "전환.mp4"  # 전환 영상 경로
bgm_folder = r"C:\Users\ska00\PycharmProjects\AutoMeme\음악"  # 배경음악 폴더 경로

merge_videos_with_bgm(base_folder, transition_video, bgm_folder, output_file)