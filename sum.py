import os
from subprocess import call
import glob


def merge_videos_with_audio(input_path, output_file):
    # 영상 파일들을 번호순으로 정렬하여 가져오기
    video_files = sorted(glob.glob(input_path))

    if not video_files:
        print("영상 파일을 찾을 수 없습니다.")
        return

    # 텍스트 파일 생성 (파일 목록)
    with open("file_list.txt", "w", encoding='utf-8') as f:
        for video_file in video_files:
            f.write(f"file '{video_file}'\n")

    # FFmpeg 명령어로 영상 병합
    cmd = [
        'ffmpeg',
        '-f', 'concat',
        '-safe', '0',
        '-i', 'file_list.txt',
        '-c', 'copy',  # 인코딩 없이 스트림 복사
        output_file
    ]

    try:
        call(cmd)
        print(f"완료: {output_file}에 저장되었습니다.")
    except Exception as e:
        print(f"오류 발생: {str(e)}")
    finally:
        # 임시 파일 삭제
        if os.path.exists("file_list.txt"):
            os.remove("file_list.txt")


# 사용 예시
input_path = r"C:\Users\ska00\Desktop\새 폴더 (5)\*.mp4"  # 입력 영상들이 있는 경로
output_file = r"C:\Users\ska00\Desktop\새 폴더 (5)\output.mp4"  # 출력 파일 이름

merge_videos_with_audio(input_path, output_file)