import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import textwrap
import random
import os


class CommentVideoGenerator:
    def __init__(self, width=550, height=1080, folder_name=None):
        self.width = width
        self.height = height
        self.bg_color = (18, 18, 18)  # 다크 모드 배경
        self.text_color = (255, 255, 255)  # 흰색 텍스트
        self.author_color = (145, 185, 255)  # 작성자 이름 색상
        self.separator_color = (40, 40, 40)  # 구분선 색상
        self.comment_height = 0
        self.comments = []

        # 폴더명에 따라 동물 리스트 선택
        if folder_name and "마비노기" in folder_name:
            self.animals = [
                "검방", "석궁", "대검", "검술", "궁수", "장궁", "법사", "화법", "빙결", "음유", "댄서", "악사", "도적", "듀블", "격가"
            ]
        elif "젠존제" in folder_name:
            self.animals = [
                "벨","와이즈","이아스","06호","18호","Fairy","까미","아우","쵸퍼대장","틴맨 마스터","아샤","구매","문의","잔돈","수지",
                "엔조","엘피","하이디","양치기","니콜","엔비","빌리","네코마타","콜레다","앤톤","벤","그레이스","리카온","코린","리나",
                "엘렌","11호","트리거","주연","청의","세스","제인","미야비","소우카쿠","야나기","하루마사","아스트라","이블린","휴고",
                "비비안","카이사르","루시","파이퍼","버니스","라이터","펄크라","의현","귤복복","반인호"
            ]
        elif "붕스" in folder_name:
            self.animals = [
                "카일루스","스텔레","Mar.7th","히메코","웰트","단항","폼폼","블랙스완","선데이","카프카","블레이드","은랑","반디","헤르타",
                "완 매","브로냐","게파드","페라","서벌","링스","후크","클라라","나타샤","제레","루카"
            ]
        elif "원신" in folder_name:
            self.animals = [
                "진","치치","각청","알베도","카즈하","아야카","아야토","닐루","알하이탐","푸리나","치오리","클로린드","실로닌","스커크",
                "다이루크","유라","이토","데히야","나비아","키니치","마비카","종려","소","호두","라이덴","신학","사이노","아를레키노","에밀리",
                "에스코피에","모나","클레","코코미","미코","나히다","방랑자","백출","느비예트","라이오슬리","한운","말라니","시틀라리",
                "미즈키","바레사","벤티","타르탈리아","감우","요이미야","야란","타이나리","리니","시그윈","차스카"
            ]
        else:
            self.animals = [
                "강아지", "고양이", "토끼", "다람쥐", "사자", "호랑이", "팬더", "코알라",
                "기린", "코끼리", "여우", "늑대", "곰", "펭귄", "돌고래", "고래",
                "앵무새", "독수리", "부엉이", "참새", "까마귀", "공작새", "두더지", "하마",
                "얼룩말", "캥거루", "알파카", "라마", "낙타", "수달", "비버", "고슴도치",
                "악어", "고래상어", "상어", "치타", "말", "재규어", "스컹크", "토끼",
                "사슴", "펭귄", "해파리", "해골", "개구리", "너구리", "여우원숭이", "캥거루",
                "어류", "황새", "코끼리", "거북이", "도마뱀", "하이에나", "알락꼬리여우원숭이",
                "나무늘보", "수달", "뱀", "살모사", "소", "여우", "호랑이", "개미",
                "조랑말", "코끼리", "기린", "고슴도치", "미어캣", "살쾡이", "노루", "유니콘",
                "펭귄", "참치", "물고기", "카멜레온", "호랑나비", "물개", "여우", "수달"
            ]

    def get_random_animal(self):
        return random.choice(self.animals)

    def truncate_text(self, text, max_length=80):
        if len(text) > max_length:
            return text[:max_length - 3] + "..."
        return text

    def create_comment_image(self, text, is_reply=False):
        # 폰트 설정
        font_size = 24
        try:
            font = ImageFont.truetype("NanumGothic.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # 들여쓰기 및 여백 설정
        padding = 10
        reply_indent = 20 if is_reply else 0
        available_width = self.width - (padding * 2) - reply_indent

        # 작성자 이름 생성
        author = self.get_random_animal()

        # 텍스트 길이 제한 및 래핑
        text = self.truncate_text(text)
        wrapper = textwrap.TextWrapper(width=25)  # 40자에서 줄바꿈
        text_lines = wrapper.wrap(text)

        # 댓글 높이 계산
        line_height = font_size + 4
        author_height = line_height + 2  # 작성자 표시 영역
        text_height = len(text_lines) * line_height + padding * 2 + author_height

        # 구분선을 포함한 전체 높이
        total_height = text_height + 1  # 구분선 높이 1픽셀 추가

        # 이미지 생성
        img = Image.new('RGB', (self.width, total_height), self.bg_color)
        draw = ImageDraw.Draw(img)

        # 댓글 배경
        if is_reply:
            # 대댓글 디자인
            draw.rectangle([0, 0, self.width, text_height], fill=(30, 30, 30))
            # 대댓글 표시선
            draw.line([(reply_indent - 5, 0), (reply_indent - 5, text_height)], fill=(100, 100, 100), width=2)

        # 작성자 이름 그리기
        draw.text((padding + reply_indent, padding), author, font=font, fill=self.author_color)

        # 텍스트 그리기
        y = padding + author_height
        for line in text_lines:
            draw.text((padding + reply_indent, y), line, font=font, fill=self.text_color)
            y += line_height

        # 구분선 그리기
        draw.line([(0, total_height - 1), (self.width, total_height - 1)],
                  fill=self.separator_color, width=1)

        return np.array(img)

    def add_comment(self, text):
        is_reply = text.startswith('┗')
        if is_reply:
            text = text[1:]  # '┗' 제거
        comment_img = self.create_comment_image(text.strip(), is_reply)
        self.comments.append(comment_img)
        self.comment_height += comment_img.shape[0]

    def create_video(self, output_filename):
        base_fps = 30  # 기본 FPS를 30으로 설정
        out = cv2.VideoWriter(output_filename,
                              cv2.VideoWriter_fourcc(*'mp4v'),
                              base_fps,
                              (self.width, self.height))

        visible_comments = []

        for new_comment in self.comments:
            visible_comments.append(new_comment)

            #  랜덤한 시간 생성
            delay_time = random.uniform(0.5, 1.0)
            # 필요한 프레임 수 계산
            frames_to_show = int(delay_time * base_fps)

            # 각 프레임 생성
            for _ in range(frames_to_show):
                frame = np.zeros((self.height, self.width, 3), dtype=np.uint8)
                frame[:] = self.bg_color

                y_offset = self.height
                for comment in reversed(visible_comments):
                    y_offset -= comment.shape[0]
                    if y_offset >= 0:
                        frame[y_offset:y_offset + comment.shape[0], :comment.shape[1]] = comment

                out.write(frame)

        # 마지막 프레임 2초간 유지
        for _ in range(4 * base_fps):
            out.write(frame)

        out.release()