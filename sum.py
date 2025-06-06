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


def get_random_transition_video(transition_folder, folder_name):
    """폴더명과 일치하는 폴더에서 랜덤한 전환 영상 선택"""
    transition_subfolder = os.path.join(transition_folder, folder_name)

    if not os.path.exists(transition_subfolder):
        print(f"경고: {folder_name} 전환영상 폴더를 찾을 수 없습니다.")
        return None

    # 지원하는 비디오 확장자
    video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.wmv']

    # 폴더 내 모든 비디오 파일 찾기
    video_files = []
    for file in os.listdir(transition_subfolder):
        if any(file.lower().endswith(ext) for ext in video_extensions):
            video_files.append(os.path.join(transition_subfolder, file))

    if not video_files:
        print(f"경고: {folder_name} 폴더에서 전환 영상을 찾을 수 없습니다.")
        return None

    # 랜덤하게 선택
    selected_video = random.choice(video_files)
    print(f"{folder_name} 폴더에서 선택된 전환영상: {os.path.basename(selected_video)}")
    return selected_video


def merge_videos_with_bgm(base_folder, transition_folder, bgm_folder):
    # 배경음악 파일 목록
    bgm_files = [f for f in os.listdir(bgm_folder) if f.endswith(('.mp3', '.wav', '.m4a'))]
    if not bgm_files:
        print("배경음악 파일을 찾을 수 없습니다.")
        return

    # base_folder 내의 한글 폴더들을 순회
    for korean_folder in os.listdir(base_folder):
        korean_folder_path = os.path.join(base_folder, korean_folder)
        if not os.path.isdir(korean_folder_path):
            continue

        print(f"\n처리 중인 폴더: {korean_folder}")

        # 각 한글 폴더별 processed_videos 리스트 초기화
        processed_videos = []

        # 숫자 폴더들 찾아서 정렬
        number_folders = []
        for folder in os.listdir(korean_folder_path):
            if folder.isdigit():
                number_folders.append(folder)
        number_folders.sort(key=int)

        # 각 숫자 폴더의 영상 처리
        for folder in number_folders:
            video_path = os.path.join(korean_folder_path, folder, "final_output.mp4")
            if not os.path.exists(video_path):
                print(f"경고: {korean_folder}/{folder} 폴더에서 final_output.mp4를 찾을 수 없습니다.")
                continue

            # 랜덤 배경음악 선택
            bgm_file = os.path.join(bgm_folder, random.choice(bgm_files))
            print(f"{korean_folder}/{folder} 폴더 영상의 배경음악: {os.path.basename(bgm_file)}")

            video_duration = get_video_duration(video_path)
            audio_duration = get_audio_duration(bgm_file)

            if audio_duration > video_duration:
                max_start = audio_duration - video_duration
                start_time = random.uniform(0, max_start)
            else:
                start_time = 0

            temp_output = f"temp_with_bgm_{korean_folder}_{folder}.mp4"

            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', bgm_file,
                '-filter_complex',
                f'[0:a]volume=0.5[orig];[1:a]atrim=start={start_time},aloop=loop=-1:size={int(video_duration * 44100)},atrim=duration={video_duration},volume=0.05[bgm];[orig][bgm]amix=duration=first:dropout_transition=0:normalize=0',
                '-c:v', 'copy',
                '-shortest',
                temp_output
            ]
            call(cmd)
            processed_videos.append(temp_output)

        # 각 한글 폴더별로 개별 병합 진행
        if processed_videos:
            # 전환 영상들을 포함하여 최종 목록 생성 (각 전환마다 랜덤 선택)
            final_video_list = []
            for i, video in enumerate(processed_videos):
                final_video_list.append(video)
                if i < len(processed_videos) - 1:  # 마지막이 아니면 전환 영상 추가
                    transition_video = get_random_transition_video(transition_folder, korean_folder)
                    if transition_video:
                        final_video_list.append(transition_video)
                    else:
                        print(f"경고: {korean_folder}에 대한 전환 영상을 찾을 수 없어 건너뜁니다.")

            # 임시 TS 파일 생성
            temp_ts_files = []
            for i, video in enumerate(final_video_list):
                temp_ts = f"temp_{korean_folder}_{i}.ts"
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
            output_file = os.path.join(base_folder, f"{korean_folder}_final.mp4")
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


# 메인 실행 부분
if __name__ == "__main__":
    base_folder = "AutoMeme"
    bgm_folder = "음악"
    transition_folder = "전환영상"
    merge_videos_with_bgm(base_folder, transition_folder, bgm_folder)