"""
背古诗大挑战 - Python 版（完整版）
适合：小学4年级
功能：随机出题、4选1、计分、段位系统、音效、精美界面、难度选择
"""

import tkinter as tk
from tkinter import messagebox, font
import random
import os
import sys
import csv
import subprocess

# ========================
# 音效模块（跨平台兼容）
# ========================
IS_WINDOWS = sys.platform.startswith('win')
IS_MAC = sys.platform.startswith('darwin')

if IS_WINDOWS:
    try:
        import winsound
    except ImportError:
        IS_WINDOWS = False

def play_system_sound(sound_name):
    """播放系统音效（跨平台，异步不阻塞）"""
    if IS_WINDOWS:
        import winsound
        winsound.PlaySound(sound_name, winsound.SND_ASYNC)
    elif IS_MAC:
        sound_map = {
            'correct': 'Glass',
            'wrong': 'Basso',
            'rankup': 'Pop'
        }
        sound = sound_map.get(sound_name, 'Glass')
        subprocess.Popen(['afplay', f'/System/Library/Sounds/{sound}.aiff'],
                      stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def play_correct_sound():
    """播放答对音效"""
    if IS_WINDOWS:
        import winsound
        winsound.Beep(523, 150)
        winsound.Beep(659, 150)
        winsound.Beep(784, 200)
        winsound.Beep(1047, 300)
    elif IS_MAC:
        play_system_sound('correct')

def play_wrong_sound():
    """播放答错音效"""
    if IS_WINDOWS:
        import winsound
        winsound.Beep(400, 300)
        winsound.Beep(300, 500)
    elif IS_MAC:
        play_system_sound('wrong')

def play_rankup_sound():
    """播放段位晋升音效"""
    if IS_WINDOWS:
        import winsound
        for freq in [523, 659, 784, 1047, 784, 1047]:
            winsound.Beep(freq, 120)
    elif IS_MAC:
        play_system_sound('rankup')

# ========================
# 古诗数据（从 CSV 文件读取）
# ========================
def load_poems_from_csv():
    """从 CSV 文件加载古诗数据"""
    csv_path = os.path.join(os.path.dirname(__file__), "data.csv")
    poems = []
    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                difficulty = int(row.get('难度', 1))
                poems.append({
                    '标题': row['标题'],
                    '上句': row['上句'],
                    '下句': row['下句'],
                    '难度': difficulty
                })
        print(f"从 CSV 加载了 {len(poems)} 首古诗")

        # 统计各级别数量
        level_counts = {}
        for p in poems:
            lvl = p['难度']
            level_counts[lvl] = level_counts.get(lvl, 0) + 1
        print(f"各级别数量: {level_counts}")

        return poems
    except Exception as e:
        print(f"读取 CSV 失败: {e}，使用默认数据")
        return [
            {"标题": "静夜思", "上句": "床前明月光", "下句": "疑是地上霜", "难度": 1},
            {"标题": "静夜思", "上句": "举头望明月", "下句": "低头思故乡", "难度": 1},
        ]

POEMS = load_poems_from_csv()

# 难度配置
DIFFICULTY_CONFIG = {
    1: {"name": "一星", "emoji": "⭐", "color": "#4CAF50", "points": 5},
    2: {"name": "二星", "emoji": "⭐⭐", "color": "#8BC34A", "points": 10},
    3: {"name": "三星", "emoji": "⭐⭐⭐", "color": "#FFC107", "points": 15},
    4: {"name": "四星", "emoji": "⭐⭐⭐⭐", "color": "#FF9800", "points": 20},
    5: {"name": "五星", "emoji": "⭐⭐⭐⭐⭐", "color": "#F44336", "points": 30},
}

# 段位配置
RANK_INFO = {
    "黑铁": ("⚫", "#808080"),
    "青铜": ("🟤", "#CD7F32"),
    "白银": ("⚪", "#C0C0C0"),
    "黄金": ("🟡", "#FFD700"),
}

def get_rank(score):
    if score >= 300:
        return "黄金"
    elif score >= 200:
        return "白银"
    elif score >= 100:
        return "青铜"
    else:
        return "黑铁"

def get_poems_by_difficulty(level):
    """获取指定难度的诗词"""
    return [p for p in POEMS if p['难度'] == level]

# ========================
# 主程序
# ========================
class PoetryGame:
    def __init__(self, root):
        self.root = root
        self.root.title("背古诗大挑战 🏆")

        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        window_width = min(800, screen_width - 100)
        window_height = min(750, screen_height - 50)
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.root.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.root.minsize(400, 450)

        # 游戏状态
        self.score = 0
        self.question_count = 0
        self.correct_index = 0
        self.current_options = []
        self.buttons = []
        self.answered = False
        self.current_difficulty = 1  # 默认一星难度

        self.setup_ui()
        self.new_question()

    def load_student_images(self):
        """加载答题者图片"""
        self.student_images = []
        img_files = ["boy.png", "girl.png"]
        for fname in img_files:
            path = os.path.join(os.path.dirname(__file__), fname)
            if os.path.exists(path):
                img = tk.PhotoImage(file=path)
                orig_h = img.height()
                img = img.subsample(max(1, orig_h // 150))
                self.student_images.append(img)
        if self.student_images:
            self.student_img_label.config(image=self.student_images[self.current_student_gender])
        else:
            self.student_img_label.config(text="❓", font=("Arial", 40))

    def switch_student_up(self):
        self.current_student_gender = 0
        if self.student_images:
            self.student_img_label.config(image=self.student_images[0])

    def switch_student_down(self):
        self.current_student_gender = 1
        if len(self.student_images) > 1:
            self.student_img_label.config(image=self.student_images[1])

    def select_difficulty(self, level):
        """选择难度并重新出题"""
        self.current_difficulty = level
        # 更新按钮样式
        for btn, lvl in zip(self.difficulty_buttons, range(1, 6)):
            if lvl == level:
                btn.config(bg=DIFFICULTY_CONFIG[lvl]["color"], fg="red", relief="sunken")
            else:
                btn.config(bg="#E0E0E0", fg="#333", relief="raised")
        # 显示当前难度
        self.difficulty_label.config(
            text=f"难度：{DIFFICULTY_CONFIG[level]['emoji']} {DIFFICULTY_CONFIG[level]['name']}（答对+{DIFFICULTY_CONFIG[level]['points']}分）",
            fg=DIFFICULTY_CONFIG[level]["color"]
        )
        # 重新出题
        self.new_question()

    def setup_ui(self):
        self.base_size = 14
        self.title_font = ("微软雅黑", int(self.base_size * 1.4), "bold")
        self.poem_font = ("微软雅黑", int(self.base_size * 1.2), "bold")
        self.btn_font = ("微软雅黑", self.base_size)
        self.info_font = ("微软雅黑", int(self.base_size * 0.9))
        self.small_font = ("微软雅黑", int(self.base_size * 0.8))

        # Canvas
        self.canvas = tk.Canvas(self.root, bg="#FFF8DC", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#FFF8DC")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

        # 标题
        top_frame = tk.Frame(self.scrollable_frame, bg="#FFF8DC")
        top_frame.pack(pady=(10, 3))

        self.title_label = tk.Label(
            top_frame, text="📜 背古诗大挑战 📜",
            font=self.title_font, bg="#FFF8DC", fg="#8B4513"
        )
        self.title_label.pack()

        # 分数和段位
        score_frame = tk.Frame(self.scrollable_frame, bg="#FFF8DC")
        score_frame.pack(pady=3)

        self.score_label = tk.Label(
            score_frame, text="🏅 得分：0",
            font=self.info_font, bg="#FFF8DC", fg="#333"
        )
        self.score_label.pack(side="left", padx=15)

        self.rank_label = tk.Label(
            score_frame, text="⚫ 段位：黑铁",
            font=self.info_font, bg="#FFF8DC", fg="#808080"
        )
        self.rank_label.pack(side="left", padx=15)

        # 难度显示
        self.difficulty_label = tk.Label(
            score_frame, text=f"难度：{DIFFICULTY_CONFIG[1]['emoji']}（答对+{DIFFICULTY_CONFIG[1]['points']}分）",
            font=self.info_font, bg="#FFF8DC", fg=DIFFICULTY_CONFIG[1]["color"]
        )
        self.difficulty_label.pack(side="left", padx=15)

        # 题目计数
        self.count_label = tk.Label(
            self.scrollable_frame, text="第 1 题",
            font=self.small_font, bg="#FFF8DC", fg="#888"
        )
        self.count_label.pack(pady=(2, 0))

        # 分隔线
        sep = tk.Frame(self.scrollable_frame, height=2, bg="#D2B48C")
        sep.pack(fill="x", padx=40, pady=6)

        # 角色展示区
        roles_frame = tk.Frame(self.scrollable_frame, bg="#FFF8DC")
        roles_frame.pack(pady=(3, 5))

        # 难度选择区域（出题者左侧）
        difficulty_area = tk.Frame(roles_frame, bg="#FFF8DC")
        difficulty_area.pack(side="left", padx=(0, 10))

        difficulty_title = tk.Label(
            difficulty_area, text="🎯 难度",
            font=self.small_font, bg="#FFF8DC", fg="#555"
        )
        difficulty_title.pack(pady=(0, 5))

        self.difficulty_buttons = []
        for lvl in range(1, 6):
            config = DIFFICULTY_CONFIG[lvl]
            btn = tk.Button(
                difficulty_area,
                text=f"{config['emoji']}\n{config['name']}",
                font=("微软雅黑", 8),
                width=4,
                height=2,
                bg="#E0E0E0" if lvl != 1 else config["color"],
                fg="red" if lvl == 1 else "#333",
                relief="raised" if lvl != 1 else "sunken",
                cursor="hand2",
                command=lambda l=lvl: self.select_difficulty(l)
            )
            btn.pack(pady=2)
            self.difficulty_buttons.append(btn)

        # 出题者区域
        poet_area = tk.Frame(roles_frame, bg="#FFF8DC")
        poet_area.pack(side="left", padx=10)

        # 出题者画像
        poet_img_path = os.path.join(os.path.dirname(__file__), "challenger.png")
        try:
            if os.path.exists(poet_img_path):
                self.poet_photo = tk.PhotoImage(file=poet_img_path)
                orig_h = self.poet_photo.height()
                self.poet_photo = self.poet_photo.subsample(max(1, orig_h // 200))
                self.poet_label = tk.Label(poet_area, image=self.poet_photo, bg="#FFF8DC")
                self.poet_label.pack(pady=5)
            else:
                self.poet_label = tk.Label(poet_area, text="📜", font=("Arial", 40), bg="#FFF8DC", fg="#5D4037")
                self.poet_label.pack(pady=5)
        except Exception as e:
            self.poet_label = tk.Label(poet_area, text="📜", font=("Arial", 40), bg="#FFF8DC", fg="#5D4037")
            self.poet_label.pack(pady=5)

        self.poet_name_label = tk.Label(
            poet_area, text="📜 出题者",
            font=self.small_font, bg="#FFF8DC", fg="#5D4037"
        )
        self.poet_name_label.pack(pady=(2, 0))

        # VS
        vs_label = tk.Label(
            roles_frame, text="VS",
            font=("Arial Black", 20, "bold"),
            bg="#FFF8DC", fg="#FF5722"
        )
        vs_label.pack(side="left", padx=15)

        # 答题者区域
        student_area = tk.Frame(roles_frame, bg="#FFF8DC")
        student_area.pack(side="left", padx=20)

        student_content = tk.Frame(student_area, bg="#FFF8DC")
        student_content.pack()

        self.student_img_label = tk.Label(student_content, bg="#FFF8DC")
        self.student_img_label.pack(side="left", pady=5)

        switch_btn_frame = tk.Frame(student_content, bg="#FFF8DC")
        switch_btn_frame.pack(side="left", padx=(10, 0))

        btn_style = {"font": ("Arial", 12), "width": 3, "bg": "#E3F2FD", "activebackground": "#BBDEFB"}
        btn_up = tk.Button(switch_btn_frame, text="▲", command=self.switch_student_up, **btn_style)
        btn_up.pack(pady=2)
        btn_down = tk.Button(switch_btn_frame, text="▼", command=self.switch_student_down, **btn_style)
        btn_down.pack(pady=2)

        self.student_name_label = tk.Label(
            student_area, text="✏️ 答题者",
            font=self.small_font, bg="#FFF8DC", fg="#37474F"
        )
        self.student_name_label.pack(pady=(2, 0))

        self.current_student_gender = 0
        self.student_images = []
        self.load_student_images()

        # 出题者提示
        self.role_label = tk.Label(
            self.scrollable_frame, text="",
            font=self.small_font, bg="#FFF8DC", fg="#555"
        )
        self.role_label.pack(pady=(3, 0))

        # 上句显示
        self.question_label = tk.Label(
            self.scrollable_frame, text="",
            font=self.poem_font,
            bg="#FFF8DC", fg="#1B5E20",
            wraplength=500,
            justify="center"
        )
        self.question_label.pack(pady=5)

        # 提示文字
        self.tip_label = tk.Label(
            self.scrollable_frame, text="👇 请选出对应的下句：",
            font=self.small_font, bg="#FFF8DC", fg="#555"
        )
        self.tip_label.pack(pady=(3, 5))

        # 选项按钮
        self.options_frame = tk.Frame(self.scrollable_frame, bg="#FFF8DC")
        self.options_frame.pack(pady=3, fill="x", padx=15)

        for i in range(4):
            btn = tk.Button(
                self.options_frame,
                text="",
                font=self.btn_font,
                height=1,
                wraplength=450,
                bg="#F5F0E1",
                fg="#333",
                activebackground="#FFE4B5",
                relief="raised",
                bd=2,
                cursor="hand2",
                command=lambda idx=i: self.check_answer(idx)
            )
            btn.pack(pady=3, fill="x", padx=20)
            self.buttons.append(btn)

        # 反馈
        self.feedback_label = tk.Label(
            self.scrollable_frame, text="",
            font=("微软雅黑", self.base_size, "bold"),
            bg="#FFF8DC"
        )
        self.feedback_label.pack(pady=5)

        # 下一题按钮
        self.next_button = tk.Button(
            self.scrollable_frame, text="➡️ 下一题",
            font=self.btn_font,
            bg="#87CEEB", fg="#000",
            activebackground="#5BB5E5",
            relief="flat", bd=0,
            padx=25, pady=6,
            cursor="hand2",
            command=self.new_question
        )

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(-1 * (event.delta // 120), "units")

    def on_canvas_resize(self, event):
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def scroll_to_top(self):
        self.canvas.yview_moveto(0)

    def new_question(self):
        self.answered = False
        self.feedback_label.config(text="")
        self.next_button.pack_forget()

        for btn in self.buttons:
            btn.config(bg="#F5F0E1", fg="#333", state="normal", relief="raised", bd=2)

        # 根据难度获取诗词
        level_poems = get_poems_by_difficulty(self.current_difficulty)
        if not level_poems:
            self.feedback_label.config(text="该难度暂无诗词！", fg="#F44336")
            return

        # 从当前难度中随机选一首
        poem_idx = random.randint(0, len(level_poems) - 1)
        poem = level_poems[poem_idx]

        # 获取在总列表中的索引（用于干扰项）
        all_indices = [i for i, p in enumerate(POEMS) if p['难度'] == self.current_difficulty]

        self.question_label.config(text=f"「{poem['上句']}」")
        self.role_label.config(text=f"📜 出题者问道（出自《{poem['标题']}》）：")

        # 生成3个干扰项（从同难度中选择）
        available = list(range(len(level_poems)))
        available.remove(poem_idx)
        wrong_indices = random.sample(available, min(3, len(available)))

        # 4个选项打乱
        all_options = [poem_idx] + wrong_indices
        random.shuffle(all_options)
        self.current_options = all_options
        self.correct_poem_idx = poem_idx  # 当前难度列表中的索引

        # 更新按钮文字
        for i, btn in enumerate(self.buttons):
            if i < len(all_options):
                lower_text = level_poems[all_options[i]]['下句']
                btn.config(text=f"{'ABCD'[i]}. {lower_text}")
                btn.pack(pady=3, fill="x", padx=20)
            else:
                btn.pack_forget()

        # 更新题目计数
        self.question_count += 1
        self.count_label.config(text=f"第 {self.question_count} 题")

        self.root.after(50, self.scroll_to_top)

    def check_answer(self, btn_index):
        if self.answered:
            return
        self.answered = True

        selected_idx = self.current_options[btn_index]
        is_correct = (selected_idx == self.correct_poem_idx)

        for btn in self.buttons:
            btn.config(state="disabled")

        if is_correct:
            points = DIFFICULTY_CONFIG[self.current_difficulty]["points"]
            self.score += points
            old_rank = get_rank(self.score - points)
            new_rank = get_rank(self.score)

            play_correct_sound()

            self.feedback_label.config(
                text=f"🎉 你太棒了！ +{points}分",
                fg="#228B22"
            )
            self.buttons[btn_index].config(bg="#A5D6A7", fg="#1B5E20", relief="sunken")

            if old_rank != new_rank:
                play_rankup_sound()
                emoji, color = RANK_INFO[new_rank]
                messagebox.showinfo(
                    "🏆 段位晋升！",
                    f"太厉害了！\n你已晋升为【{new_rank}】段位！\n\n{emoji*3}"
                )

            self.update_score_display()
        else:
            play_wrong_sound()
            level_poems = get_poems_by_difficulty(self.current_difficulty)
            correct_lower = level_poems[self.correct_poem_idx]['下句']

            self.feedback_label.config(
                text=f"💪 继续努力！正确答案：「{correct_lower}」",
                fg="#C62828"
            )
            self.buttons[btn_index].config(bg="#EF9A9A", fg="#B71C1C", relief="sunken")

            for i, btn in enumerate(self.buttons):
                if self.current_options[i] == self.correct_poem_idx:
                    btn.config(bg="#A5D6A7", fg="#1B5E20")

        self.next_button.pack(pady=(5, 0))

    def update_score_display(self):
        rank = get_rank(self.score)
        emoji, color = RANK_INFO[rank]
        self.score_label.config(text=f"🏅 得分：{self.score}")
        self.rank_label.config(text=f"{emoji} 段位：{rank}", fg=color)

if __name__ == "__main__":
    root = tk.Tk()
    app = PoetryGame(root)
    root.mainloop()
