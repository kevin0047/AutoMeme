import winsound
from threading import Thread
from commentVideo import CommentVideoGenerator
import requests
from bs4 import BeautifulSoup
from os.path import getsize
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
from PIL import Image, ImageDraw, ImageFont
import os
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pyaudio
import wave
from pydub import AudioSegment
from pydub.silence import split_on_silence, detect_nonsilent
import time
class DataCollectorGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("자료수집기")
        self.root.geometry("600x500")

        # URL 입력
        url_frame = ttk.LabelFrame(root, text="URL 입력", padding="10")
        url_frame.pack(fill="x", padx=10, pady=5)

        self.url_entry = ttk.Entry(url_frame, width=50)
        self.url_entry.pack(side="left", padx=5)

        # 경로 설정
        path_frame = ttk.LabelFrame(root, text="저장 경로 설정", padding="10")
        path_frame.pack(fill="x", padx=10, pady=5)

        self.save_path = tk.StringVar(value="C:/Users/ska00/Desktop/AutoMeme")
        path_entry = ttk.Entry(path_frame, textvariable=self.save_path, width=50)
        path_entry.pack(side="left", padx=5)

        # 진행 상태
        status_frame = ttk.LabelFrame(root, text="진행 상태", padding="10")
        status_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.status_text = tk.Text(status_frame, height=10, width=50)
        self.status_text.pack(padx=5, pady=5)

        # 진행바
        self.progress = ttk.Progressbar(root, length=400, mode='determinate')
        self.progress.pack(pady=10)

        # 실행 버튼
        self.start_button = ttk.Button(root, text="수집 시작", command=self.start_collection)
        self.start_button.pack(pady=10)

    def update_status(self, message):
        self.status_text.insert(tk.END, f"{message}\n")
        self.status_text.see(tk.END)

    def start_collection(self):
        if not self.url_entry.get():
            messagebox.showerror("오류", "URL을 입력해주세요.")
            return

        self.start_button.config(state="disabled")
        self.progress['value'] = 0
        Thread(target=self.collect_data).start()

    def clean_and_process_text(self, content_path):
        output_path = content_path.replace('content.txt', 'recontent.txt')

        with open(content_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()

        filtered_lines = []
        i = 0
        while i < len(lines):
            current_line = lines[i].strip()

            if current_line.startswith('https://youtube.com'):
                while i < len(lines) and not lines[i].strip().endswith('youtube.com'):
                    i += 1
                i += 1
                continue

            if current_line.startswith('http'):
                if i + 3 < len(lines):

                    if lines[i + 3].strip()[0].isascii() and lines[i + 3].strip()[0].isalpha():
                        i += 4  # 해당 블록 전체 스킵
                        continue
                    else:
                        i += 1  # https 줄만 스킵
                        continue
                else:
                    i += 1  # https 줄만 스킵
                    continue

            if '[원본 보기]' in current_line:
                i += 1
                continue

            filtered_lines.append(lines[i])
            i += 1

        # 빈 줄과 숫자만 있는 줄 제거
        non_empty_lines = [line.strip() for line in filtered_lines if line.strip() and not line.strip().isdigit()]

        # 마침표 추가 및 텍스트 정제
        cleaned_lines = []
        for line in non_empty_lines:
            clean_line = line.strip() + '.'
            clean_line = clean_line.replace('ㅋ', '.').replace('ㅂㄷ', '부들') \
                .replace('ㄹㅈㄷ', '레전드').replace('ㄱㅊ', '괜찮') \
                .replace('ㄳ', '감사').replace('ㄱㅅ', '감사') \
                .replace('ㅇㅇ', '.').replace('ㅉㅉ', '쯧쯧') \
                .replace('ㄷ', '.').replace('ㄹㅇ', '레알') \
                .replace('ㅠ', '.').replace('ㅜ', '.') \
                .replace('jpg', '.').replace('png', '.') \
                .replace('JPG', '.').replace('TXT', '.') \
                .replace('txt', '.').replace('GIF', '.') \
                .replace('gif', '.').replace('|', '.') \
                .replace('-', '.').replace('❗', '.') \
                .replace('!', '.').replace('❓', '.') \
                .replace('♥', '.').replace('♡', '.') \
                .replace('✋', '.').replace('ㅅㅂ', '.') \
                .replace('ㅆㅂ', '.').replace('ㅂㅅ', '.') \
                .replace('ㅄ', '.').replace('ㅁㅌㅊ', '몇타치') \
                .replace('ㄱㅆㅅㅌㅊ', '개씹상타치').replace('ㅆㅅㅌㅊ', '씹상타치') \
                .replace('ㅅㅌㅊ', '상타치').replace('ㅈㄴ', '존나') \
                .replace('ㅇㅈㄹ', '이지랄').replace('ㅇㅈ', '인정') \
                .replace('ㅈ', '좃').replace('1돌', '일돌') \
                .replace('2돌', '이돌').replace('3돌', '삼돌') \
                .replace('4돌', '사돌').replace('5돌', '오돌') \
                .replace('6돌', '육돌').replace('4성', '사성') \
                .replace('5성', '오성').replace('ㄴㄴ', '노노') \
                .replace('관련게시물 : ', '.') .replace('[단독]', '.')\

            while '..' in clean_line:
                clean_line = clean_line.replace('..', '.')
            cleaned_lines.append(clean_line)

        # 결과 저장
        text = '\n'.join(cleaned_lines).rstrip('.')
        with open(output_path, 'w', encoding='utf-8') as file:
            file.write(text)

    def download_images(self, url):
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
            "Accept-Language": "ko-KR,ko;q=0.9"
        }

        try:
            res = requests.get(url, headers=headers)
            res.raise_for_status()
            soup = BeautifulSoup(res.text, 'html.parser')

            image_download_contents = soup.select("div.appending_file_box ul li")

            if not image_download_contents:
                self.update_status("이미지를 찾을 수 없습니다.")
                return

            # 기본 저장 경로 설정
            base_path = self.save_path.get()
            image_path = f"{base_path}/Images"

            # 전체 경로가 존재하지 않으면 생성
            try:
                os.makedirs(base_path, exist_ok=True)
                os.makedirs(image_path, exist_ok=True)
                self.update_status(f"저장 경로 생성: {image_path}")
            except Exception as e:
                self.update_status(f"경로 생성 중 오류 발생: {str(e)}")
                return

            for li in image_download_contents:
                img_tag = li.find('a', href=True)
                if not img_tag:
                    continue

                img_url = img_tag['href']
                savename = img_url.split("no=")[2]
                headers['Referer'] = url

                try:
                    response = requests.get(img_url, headers=headers)
                    path = os.path.join(image_path, savename)

                    file_size = len(response.content)

                    if os.path.isfile(path):
                        if getsize(path) != file_size:
                            new_path = os.path.join(image_path, f"[1]{savename}")
                            self.update_status(f"다운로드 중: {savename} (다른 크기)")
                            with open(new_path, "wb") as file:
                                file.write(response.content)
                        else:
                            self.update_status(f"건너뜀: {savename} (이미 존재)")
                    else:
                        self.update_status(f"다운로드 중: {savename}")
                        with open(path, "wb") as file:
                            file.write(response.content)

                except Exception as e:
                    self.update_status(f"이미지 다운로드 중 오류 발생: {str(e)}")

            self.update_status("이미지 다운로드 완료!")

        except Exception as e:
            self.update_status(f"오류 발생: {str(e)}")

        finally:
            self.progress['value'] = 90  # 프로그레스바 업데이트

    def generate_subtitles(self):
        try:
            # Define input and output paths
            input_file = f"{self.save_path.get()}/txt/content.txt"
            output_folder = f"{self.save_path.get()}/voice"
            font_size = 30  # Default font size, you can make this configurable

            if not os.path.exists(input_file):
                messagebox.showerror("오류", "content.txt 파일을 찾을 수 없습니다.")
                return

            # Create output directory if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)

            try:
                font = ImageFont.truetype("malgun.ttf", font_size)  # 맑은 고딕
            except IOError:
                font = ImageFont.load_default()

            with open(input_file, 'r', encoding='utf-8') as file:
                lines = file.readlines()

            total_lines = len([line for line in lines if line.strip()])
            current_line = 0

            for i, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue

                # Skip lines that contain only numbers
                if line.replace(' ', '').isdigit():
                    self.update_status(f"숫자로만 된 줄 건너뜀: {line}")
                    continue

                # Create temporary image to calculate text size
                temp_image = Image.new('RGB', (100, 100), color=(192, 192, 192))
                temp_draw = ImageDraw.Draw(temp_image)
                bbox = temp_draw.textbbox((0, 0), line, font=font)

                # Calculate actual image dimensions
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]

                # Create actual image
                image = Image.new('RGB', (width + 20, height + 30), color=(255, 255, 255))
                draw = ImageDraw.Draw(image)
                draw.text((10, 10), line, font=font, fill=(0, 0, 102))

                # Save image
                sanitized_line = re.sub(r'[\\/*?:"<>|]', '', line)[:50]  # Limit filename length
                output_path = os.path.join(output_folder, f'subtitle_{i + 1}_{sanitized_line}.png')
                image.save(output_path)

                current_line += 1
                self.progress['value'] = (current_line / total_lines) * 100
                self.update_status(f"자막 생성 중... ({current_line}/{total_lines})")
                self.root.update()

            self.update_status("자막 생성이 완료되었습니다!")

        except Exception as e:
            self.update_status(f"자막 생성 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"자막 생성 중 오류가 발생했습니다: {str(e)}")

    def generate_tts(self):
        try:
            # Define input and output paths
            input_file = f"{self.save_path.get()}/txt/recontent.txt"
            output_folder = f"{self.save_path.get()}/voice"

            if not os.path.exists(input_file):
                messagebox.showerror("오류", "recontent.txt 파일을 찾을 수 없습니다.")
                return

            # Create output directory if it doesn't exist
            os.makedirs(output_folder, exist_ok=True)

            # Initialize Chrome driver
            options = webdriver.ChromeOptions()
            driver = webdriver.Chrome(options=options)
            driver.get('https://papago.naver.com/?sk=ko&tk=en')

            # Read sentences from recontent.txt
            with open(input_file, 'r', encoding='utf-8') as file:
                sentences = file.read().split('\n')

            # Initialize PyAudio
            p = pyaudio.PyAudio()
            time.sleep(3)  # Wait for page to load

            # Audio recording parameters
            CHUNK = 1024
            FORMAT = pyaudio.paInt16
            CHANNELS = 2
            RATE = 44100
            CHARS_PER_SECOND = 7
            ADDITIONAL_DELAY = 1.5

            total_sentences = len([s for s in sentences if s.strip()])
            current_sentence = 0

            for i, sentence in enumerate(sentences, start=1):
                if not sentence.strip():
                    continue

                # Find and clear input box
                input_box = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, '//*[@id="txtSource"]')))
                input_box.clear()
                input_box.send_keys(sentence)
                time.sleep(2)

                # Calculate recording duration
                RECORD_SECONDS = len(sentence) / CHARS_PER_SECOND + ADDITIONAL_DELAY
                frames = []

                # Click TTS button
                button = driver.find_element(By.XPATH, '//*[@id="btn-toolbar-source"]/span[1]')
                button.click()

                # Record audio
                stream = p.open(format=FORMAT,
                                channels=CHANNELS,
                                rate=RATE,
                                input=True,
                                frames_per_buffer=CHUNK)

                for _ in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
                    data = stream.read(CHUNK)
                    frames.append(data)

                stream.stop_stream()
                stream.close()

                # Clean sentence for filename
                cleaned_sentence = ''.join(e for e in sentence if e.isalnum())
                if len(cleaned_sentence) > 15:
                    cleaned_sentence = cleaned_sentence[:15]

                # Save audio files
                temp_filename = os.path.join(output_folder, f"temp_tts{i}_{cleaned_sentence}.wav")
                final_filename = os.path.join(output_folder, f"tts{i}_{cleaned_sentence}.wav")

                # Write temporary WAV file
                wf = wave.open(temp_filename, 'wb')
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(p.get_sample_size(FORMAT))
                wf.setframerate(RATE)
                wf.writeframes(b''.join(frames))
                wf.close()

                # Process audio (remove silence)
                sound = AudioSegment.from_wav(temp_filename)
                chunks = split_on_silence(sound,
                                          min_silence_len=500,
                                          silence_thresh=-40
                                          )

                # Combine chunks with short silence between them
                final_audio = AudioSegment.empty()
                for chunk in chunks:
                    final_audio += chunk + AudioSegment.silent(duration=100)

                final_audio.export(final_filename, format="wav")
                os.remove(temp_filename)  # Clean up temporary file

                current_sentence += 1
                self.progress['value'] = (current_sentence / total_sentences) * 100
                self.update_status(f"TTS 생성 중... ({current_sentence}/{total_sentences})")
                self.root.update()

            driver.quit()
            p.terminate()

            self.update_status("TTS 생성이 완료되었습니다!")

        except Exception as e:
            self.update_status(f"TTS 생성 중 오류 발생: {str(e)}")
            messagebox.showerror("오류", f"TTS 생성 중 오류가 발생했습니다: {str(e)}")
            if 'driver' in locals():
                driver.quit()
            if 'p' in locals():
                p.terminate()

    def collect_data(self):
        try:
            # 저장 경로의 모든 파일 삭제
            base_path = self.save_path.get()
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                        except Exception as e:
                            self.update_status(f"파일 삭제 중 오류 발생: {str(e)}")

            self.update_status("브라우저 실행 중...")
            options = webdriver.ChromeOptions()
            driver = webdriver.Chrome(options=options)

            self.update_status("페이지 로딩 중...")
            driver.get(self.url_entry.get())
            self.progress['value'] = 20

            # 제목 추출
            title_ = driver.find_element(By.XPATH,
                                         '//*[@id="container"]/section/article[2]/div[1]/header/div/h3/span[2]')
            title = title_.text
            self.update_status(f"제목 추출: {title}")
            self.progress['value'] = 40

            # 내용 추출
            element = driver.find_element(By.XPATH, '//div[@class="write_div"]')
            content = re.sub("- dc official App|이미지 순서 ON|마우스 커서를 올리면|이미지 순서를 ON/OFF 할 수 있습니다.", "", element.text)

            self.progress['value'] = 60

            # 댓글 추출 및 처리
            self.update_status("댓글 추출 중...")
            parent_elements = driver.find_elements(By.XPATH,
                                                   '//div[@class="clear cmt_txtbox"] | //div[@class="clear cmt_txtbox btn_reply_write_all"]')
            filter_words = ["틱톡", "https", "실베", "kakao",".com","gall","store","MeritTV","도배","디시","디씨","갤러리","🍀","⭐","고고혓","@@"]  # 원하는 필터 단어 추가
            seen_comments = set()
            is_first_comment = True
            comment_text = []
            for element in parent_elements:
                comments = element.find_elements(By.XPATH, './/p[@class="usertxt ub-word"]')
                for comment in comments:
                    clean_comment = re.sub("- dc App|파파 너글|착한말하기|1일차", "", comment.text)

                    if any(word in clean_comment for word in filter_words):
                        continue

                    if clean_comment in seen_comments:
                        continue

                    if is_first_comment and "clear cmt_txtbox" == element.get_attribute("class"):
                        is_first_comment = False
                        continue

                    if "clear cmt_txtbox" == element.get_attribute("class"):
                        clean_comment = "┗ " + clean_comment

                    clean_comment = clean_comment.replace('\n', ' ')
                    seen_comments.add(clean_comment)
                    comment_text.append(clean_comment + "\n")
                    is_first_comment = False

            self.progress['value'] = 80

            # 파일 저장
            self.update_status("파일 저장 중...")
            base_path = self.save_path.get()

            # 텍스트 저장
            os.makedirs(f"{base_path}/txt", exist_ok=True)
            content_path = f"{base_path}/txt/content.txt"

            with open(content_path, 'a', encoding='utf-8') as f:
                f.write(f"{title}\n{content}\n")

            # 정제된 텍스트 생성
            self.clean_and_process_text(content_path)

            with open(f"{base_path}/txt/comment.txt", 'w', encoding='utf-8') as f:
                for comment in comment_text:
                    f.write(comment)
            driver.quit()

            # 댓글 영상 생성
            self.update_status("댓글 영상 생성 중...")
            try:
                comment_file = f"{base_path}/txt/comment.txt"
                video_output = f"{base_path}/output_comments.mp4"
                generator = CommentVideoGenerator()

                with open(comment_file, 'r', encoding='utf-8') as f:
                    comments = f.readlines()

                for comment in comments:
                    if comment.strip():  # 빈 줄 제외
                        generator.add_comment(comment)

                generator.create_video(video_output)
                self.update_status("댓글 영상 생성 완료!")
            except Exception as e:
                self.update_status(f"댓글 영상 생성 실패: {str(e)}")

            self.download_images(self.url_entry.get())
            self.generate_subtitles()
            self.generate_tts()
            self.progress['value'] = 100

            winsound.PlaySound("SystemExit", winsound.SND_ALIAS)
            self.update_status("작업 완료!")
            self.start_button.config(state="normal")

        except Exception as e:
            self.update_status(f"오류 발생: {str(e)}")
            self.start_button.config(state="normal")
            messagebox.showerror("오류", str(e))







if __name__ == "__main__":
    root = tk.Tk()
    app = DataCollectorGUI(root)
    root.mainloop()