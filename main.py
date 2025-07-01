import pygame
import math
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad, pad
import json
import os
import time

# Khởi tạo Pygame
pygame.init()

# Cài đặt màn hình
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Giải Mã Kho Báu")

# Màu sắc
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
GREEN = (0, 200, 0)
RED = (200, 0, 0)
GOLD = (255, 215, 0)
DARK_BROWN = (101, 67, 33)
BLUE = (50, 100, 200)
LIGHT_BLUE = (100, 150, 255)
TRANSPARENT_BLACK = (0, 0, 0, 150) # Màu đen trong suốt cho nền hộp phản hồi

# Font
try:
    font = pygame.font.Font("Roboto-Regular.ttf", 24)
    handwritten_font = pygame.font.Font("Roboto-Regular.ttf", 28)
    title_font = pygame.font.Font("Roboto-Regular.ttf", 48)
    small_font = pygame.font.Font("Roboto-Regular.ttf", 20)
    win_font = pygame.font.Font("Roboto-Regular.ttf", 60) # Font cho thông báo chiến thắng
except:
    print("Không tải được font Roboto, dùng font mặc định.")
    font = pygame.font.SysFont("arial", 24)
    handwritten_font = pygame.font.SysFont("comicsansms", 28)
    title_font = pygame.font.SysFont("arial", 48)
    small_font = pygame.font.SysFont("arial", 20)
    win_font = pygame.font.SysFont("arial", 60)

# Âm thanh
success_sound = None
fail_sound = None
win_sound = None
chest_open_sound = None
try:
    pygame.mixer.music.load("NhacNen.wav")
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)
    success_sound = pygame.mixer.Sound("Win.wav")
    fail_sound = pygame.mixer.Sound("Loss.wav")
    win_sound = pygame.mixer.Sound("station.wav")
    chest_open_sound = pygame.mixer.Sound("Win.wav")
    success_sound.set_volume(0.7)
    fail_sound.set_volume(0.7)
    win_sound.set_volume(0.8)
    chest_open_sound.set_volume(0.8)
except:
    print("Thiếu file âm thanh, chạy không có âm thanh.")

# Hình nền
try:
    background = pygame.image.load("BanDO.jpg")
    background = pygame.transform.scale(background, (WIDTH, HEIGHT))
except:
    print("Không tải được hình nền, dùng nền tối.")
    background = pygame.Surface((WIDTH, HEIGHT))
    background.fill(RED) # <--- Đã thay đổi từ DARK_BROWN sang RED

# --- TẢI VÀ CHUẨN BỊ HÌNH ẢNH MỚI ---
player_image = None
station_image = None
treasure_chest_closed_image = None
treasure_chest_open_image = None
document_images = [] # Danh sách chứa 3 ảnh tài liệu

try:
    player_image = pygame.image.load("player.png").convert_alpha()
    player_image = pygame.transform.scale(player_image, (30, 30)) # Kích thước icon nhân vật
except:
    print("Không tải được player.png, dùng hình tròn.")

try:
    station_image = pygame.image.load("station.png").convert_alpha()
    station_image = pygame.transform.scale(station_image, (40, 40)) # Kích thước icon trạm
except:
    print("Không tải được station.png, dùng hình tròn.")

try:
    treasure_chest_closed_image = pygame.image.load("ruongdong.png").convert_alpha()
    treasure_chest_closed_image = pygame.transform.scale(treasure_chest_closed_image, (200, 200))
    treasure_chest_open_image = pygame.image.load("treasure.png").convert_alpha()
    treasure_chest_open_image = pygame.transform.scale(treasure_chest_open_image, (200, 200))
except:
    print("Không tải được hình ảnh rương báu, dùng màu nền.")

# Tải 3 ảnh tài liệu
for i in range(1, 4):
    try:
        doc_img = pygame.image.load(f"mat{i}.png").convert_alpha()
        doc_img = pygame.transform.scale(doc_img, (80, 100)) # Kích thước tài liệu
        document_images.append(doc_img)
    except:
        print(f"Không tải được mat{i}.png, sẽ không hiển thị tài liệu.")
        document_images.append(None) # Thêm None để giữ đúng số lượng


# --- Khởi tạo dữ liệu mã hóa AES ---
def generate_aes_ciphertext():
    plaintext = "GOLDEN"
    key = "Sixteen byte key"
    padded_plaintext = pad(plaintext.encode('utf-8'), AES.block_size)
    cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
    ciphertext_bytes = cipher.encrypt(padded_plaintext)
    return ciphertext_bytes

# Thông điệp mã hóa và kết quả mong đợi
MESSAGES = {
    "Caesar": ("KHOOR", 3, "HELLO"), # Đã sửa: HELLO + 3 = KHOOR
    "Vigenere": ("RIJVS", "KEY", "HELLO"), # Đã sửa: HELLO + KEY = RIJVS
    "RSA": (855, 17, 3233, 123),
    "AES": (generate_aes_ciphertext(), b'Sixteen byte key', "GOLDEN")
}

# Gợi ý
HINTS = {
    "Caesar": "Đây là mật mã dịch chuyển đơn giản. Hãy thử dịch chuyển mỗi ký tự ngược lại 3 vị trí để tìm manh mối đầu tiên. Hãy nhớ các chữ cái A-Z.",
    "Vigenere": "Mật mã này dùng một từ khóa để dịch chuyển. Từ khóa bạn cần là 'KEY'. Mỗi ký tự của từ khóa sẽ dịch chuyển một ký tự của thông điệp.",
    "RSA": "Đây là một số nguyên được mã hóa. Để giải mã, bạn cần tìm số nghịch đảo modulo của 'e' và sử dụng công thức giải mã RSA. Giá trị 'e' là 17 và 'n' là 3233. Hãy cẩn thận với các phép toán modulo!",
    "AES": "Đây là mật mã khối mạnh mẽ. Khóa để giải mã là 'Sixteen byte key'. Hãy nhập chính xác cả khóa và kết quả. Key cần đủ 16 ký tự để giải mã!"
}

# Manh mối cho cốt truyện sau mỗi cấp độ
STORY_CLUES = {
    "Caesar": "Bạn đã giải mã được 'HELLO'! Manh mối đầu tiên là: một bản đồ cổ với ký hiệu 'LL' trên góc phải dưới.",
    "Vigenere": "Tuyệt vời, 'HELLO' đã lộ diện! Manh mối tiếp theo: trên bản đồ có đánh số '1xx', đó là tọa độ đầu tiên cần tìm.",
    "RSA": "Bạn thật sự tài ba! Số '123' đã được giải mã! Manh mối cuối cùng: một ngôi đền cổ có tên 'G__DE_'. Hãy đến đó!",
    "AES": "Xuất sắc! Bạn đã tìm thấy từ 'GOLDEN'! Kho báu chính là ở Ngôi Đền Vàng! Chuẩn bị đến vị trí cuối cùng!"
}

# CÁC TRẠM GIẢI MÃ VÀ TỌA ĐỘ TRÊN BẢN ĐỒ
# Tọa độ này là tương đối, bạn có thể điều chỉnh để phù hợp với hình ảnh bản đồ của bạn
STATIONS = {
    "Start": {"coords": (100, 100), "cipher": None, "label": "Bắt đầu"},
    "Caesar_Station": {"coords": (200, 250), "cipher": "Caesar", "label": "Caesar"},
    "Vigenere_Station": {"coords": (400, 150), "cipher": "Vigenere", "label": "Vigenère"},
    "RSA_Station": {"coords": (550, 350), "cipher": "RSA", "label": "RSA"},
    "AES_Station": {"coords": (300, 450), "cipher": "AES", "label": "AES"},
    "Treasure_Location": {"coords": (650, 500), "cipher": None, "label": "Kho Báu"}
}

# Danh sách các trạm theo thứ tự chơi
STATION_ORDER = ["Start", "Caesar_Station", "Vigenere_Station", "RSA_Station", "AES_Station", "Treasure_Location"]

# Biến trạng thái game
current_level_index = 0
current_station_name = STATION_ORDER[current_level_index]
player_x, player_y = STATIONS[current_station_name]["coords"]
player_radius = 15
player_color = RED

score = 0
attempts_left = 3
input_text = ""
input_key = ""
feedback = ""
game_state = "map" # map, decode, feedback, game_over, treasure_screen, guide
show_hint = False
selected_cipher = ""
input_active = False
input_field = None
last_click_time = 0
guide_scroll_offset = 0 # Biến mới để điều khiển cuộn nội dung cẩm nang
total_guide_content_height = 0 # Biến mới để lưu tổng chiều cao nội dung cẩm nang


# Nội dung cẩm nang (Đã cập nhật chi tiết hướng dẫn giải tay)
GUIDE_CONTENT = """Chào mừng bạn đến với "Giải Mã Kho Báu"!

Mục tiêu của bạn là di chuyển qua các trạm trên bản đồ và giải mã các loại mật mã cổ xưa. Mỗi trạm sẽ có một loại mật mã khác nhau để bạn thử tài.

1.  **Mật mã Caesar:** Đây là mật mã dịch chuyển đơn giản. Mỗi chữ cái trong thông điệp được dịch chuyển một số vị trí cố định trong bảng chữ cái.
    * **Cách giải:** Để giải mã, bạn cần dịch ngược mỗi chữ cái đi đúng số vị trí đó.
    * **Ví dụ:** Nếu thông điệp mã hóa là "FYYFHP" và biết dịch chuyển là 5 (tức là mỗi chữ cái đã bị dịch tiến 5 vị trí khi mã hóa). Để giải mã, bạn dịch ngược 5 vị trí: F-5=A, Y-5=T, Y-5=T, F-5=A, H-5=C, P-5=K. Kết quả sẽ là "ATTACK".

2.  **Mật mã Vigenère:** Mật mã này dùng một từ khóa để dịch chuyển các chữ cái. Từ khóa được lặp lại để tạo thành một chuỗi có độ dài bằng thông điệp.
    * **Cách giải:** Để giải mã, bạn cần dịch ngược mỗi chữ cái của thông điệp mã hóa bằng cách trừ đi giá trị số của chữ cái tương ứng trong từ khóa (theo bảng chữ cái, A=0, B=1,...). Công thức: (Chữ cái mã hóa - Chữ cái khóa) mod 26.
    * **Ví dụ:** Nếu thông điệp mã hóa là "EFBTVC" và từ khóa là "CODE".
        * E(4) - C(2) = 2 (C)
        * F(5) - O(14) = -9 % 26 = 17 (R)
        * B(1) - D(3) = -2 % 26 = 24 (Y)
        * T(19) - E(4) = 15 (P)
        * V(21) - C(2) = 19 (T)
        * C(2) - O(14) = -12 % 26 = 14 (O)
        Kết quả là "CRYPTO".

3.  **Mã hóa RSA:** RSA là một hệ thống mã hóa khóa công khai. Thông điệp được mã hóa thành một số nguyên bằng cách sử dụng khóa công khai (e, n).
    * **Cách giải:** Giải mã RSA rất phức tạp và thường yêu cầu máy tính. Về cơ bản, bạn được cho một số nguyên đã mã hóa (cipher_text), khóa công khai 'e' và modulo 'n'. Để giải mã, bạn cần tìm khóa bí mật 'd' (số nghịch đảo modulo của 'e' theo phi(n), trong đó phi(n) là hàm totient Euler của n). Sau đó, bạn tính 'cipher_text' mũ 'd' modulo 'n'. Trong game này, bạn sẽ nhận được các thông số và cần tìm kết quả cuối cùng.

4.  **Mã hóa AES:** AES là một tiêu chuẩn mã hóa khối rất mạnh mẽ và phức tạp.
    * **Cách giải:** Mật mã AES không thể giải mã thủ công trong game này. Để vượt qua thử thách này, bạn cần tìm được chính xác khóa giải mã và nhập đúng từ khóa cùng với kết quả mong muốn đã được cung cấp.

Hãy sử dụng gợi ý nếu bạn gặp khó khăn và quản lý số lượt thử của mình. Khi giải mã thành công, bạn sẽ nhận được các manh mối dẫn đến Kho Báu! Chúc may mắn!"""


# Lưu và tải tiến trình
def save_progress():
    try:
        with open("progress.json", "w") as f:
            json.dump({
                "level_index": current_level_index,
                "score": score,
                "player_x": player_x,
                "player_y": player_y,
                "current_station_name": current_station_name
            }, f)
    except Exception as e:
        print(f"Lỗi khi lưu tiến trình: {e}")

def load_progress():
    global current_level_index, score, player_x, player_y, current_station_name
    try:
        if os.path.exists("progress.json"):
            with open("progress.json", "r") as f:
                data = json.load(f)
                current_level_index = data.get("level_index", 0)
                score = data.get("score", 0)
                player_x = data.get("player_x", STATIONS["Start"]["coords"][0])
                player_y = data.get("player_y", STATIONS["Start"]["coords"][1])
                current_station_name = data.get("current_station_name", "Start")
    except Exception as e:
        print(f"Lỗi khi tải tiến trình: {e}")
        current_level_index = 0
        score = 0
        player_x, player_y = STATIONS["Start"]["coords"]
        current_station_name = "Start"
load_progress()

# Các hàm giải mã (giữ nguyên)
def caesar_decrypt(ciphertext, shift):
    result = ""
    for char in ciphertext:
        if 'A' <= char <= 'Z':
            result += chr((ord(char) - ord('A') - shift + 26) % 26 + ord('A'))
        else:
            result += char
    return result

def vigenere_decrypt(ciphertext, key):
    key = key.upper()
    result = ""
    key_index = 0
    for char in ciphertext:
        if 'A' <= char <= 'Z':
            shift = ord(key[key_index % len(key)]) - ord('A')
            result += chr((ord(char) - ord('A') - shift + 26) % 26 + ord('A'))
            key_index += 1
        else:
            result += char
    return result

def mod_inverse(e, phi):
    def egcd(a, b):
        if a == 0:
            return b, 0, 1
        g, x, y = egcd(b % a, a)
        return g, y - (b // a) * x, x
    g, x, y = egcd(e, phi)
    if g != 1:
        raise Exception('Nghịch đảo modulo không tồn tại')
    return x % phi

def rsa_decrypt(ciphertext, e, n):
    p, q = 61, 53
    if p * q != n:
        print(f"Lỗi RSA: p*q ({p*q}) không khớp với n ({n})")
        return None
    phi = (p - 1) * (q - 1)
    try:
        d = mod_inverse(e, phi)
        decrypted_value = pow(ciphertext, d, n)
        return decrypted_value
    except Exception as ex:
        print(f"Lỗi RSA decryption: {ex}")
        return None

def aes_decrypt(ciphertext_bytes, key_bytes):
    try:
        if len(key_bytes) not in [16, 24, 32]:
            raise ValueError(f"AES key must be 16, 24, or 32 bytes long, got {len(key_bytes)}.")
            
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        decrypted_padded_data = cipher.decrypt(ciphertext_bytes)
        
        return unpad(decrypted_padded_data, AES.block_size).decode('utf-8')
    except ValueError as e:
        print(f"Lỗi padding trong giải mã AES: {e}. Khóa có thể sai.")
        return None
    except Exception as e:
        print(f"Lỗi giải mã AES: {e}")
        return None

# Kiểm tra giải mã
def check_decryption():
    global feedback, game_state, score, attempts_left, current_level_index, player_x, player_y, current_station_name
    global input_text, input_key, selected_cipher

    correct = False
    
    current_cipher_type = STATIONS[current_station_name]["cipher"]
    if not current_cipher_type:
        game_state = "feedback"
        feedback = "Lỗi game: Không có mật mã tại trạm này để giải mã."
        return

    current_message_data = MESSAGES[current_cipher_type]
    
    input_text_clean = input_text.strip().upper()
    input_key_clean = input_key.strip()
    
    if current_cipher_type == "Caesar":
        expected_plaintext = current_message_data[2]
        if input_text_clean == expected_plaintext:
            correct = True
    elif current_cipher_type == "Vigenere":
        expected_plaintext = current_message_data[2]
        expected_key = current_message_data[1]
        if input_text_clean == expected_plaintext and input_key_clean.upper() == expected_key:
            correct = True
    elif current_cipher_type == "RSA":
        expected_plaintext_int = current_message_data[3]
        decrypted_rsa = rsa_decrypt(current_message_data[0], current_message_data[1], current_message_data[2])
        if decrypted_rsa is not None and str(decrypted_rsa) == input_text_clean:
            correct = True
    elif current_cipher_type == "AES":
        expected_plaintext = current_message_data[2]
        expected_key = current_message_data[1].decode('utf-8')
        
        if len(input_key_clean) != 16:
            feedback = "Lỗi: Khóa AES phải có độ dài chính xác 16 ký tự!"
            attempts_left -= 1
            if fail_sound: fail_sound.play()
            return

        if input_key_clean == expected_key and input_text_clean == expected_plaintext:
            decrypted_aes = aes_decrypt(current_message_data[0], input_key_clean.encode('utf-8'))
            
            if decrypted_aes == expected_plaintext:
                correct = True
            else:
                feedback = "Kết quả bạn nhập đúng nhưng giải mã thực tế thất bại. Khóa có thể sai hoặc có ký tự ẩn."
                attempts_left -= 1
                if fail_sound: fail_sound.play()
                if attempts_left == 0:
                    feedback = "Hết lượt! Game Over."
                    game_state = "game_over"
                return
        else:
            feedback = "Sai! Khóa hoặc kết quả không đúng."
            attempts_left -= 1
            if fail_sound: fail_sound.play()
            if attempts_left == 0:
                feedback = "Hết lượt! Game Over."
                game_state = "game_over"
            return

    if correct:
        score_multiplier = attempts_left / 3
        if current_cipher_type == "Caesar":
            score_gain = 100
        elif current_cipher_type == "Vigenere":
            score_gain = 200
        elif current_cipher_type == "RSA":
            score_gain = 300
        elif current_cipher_type == "AES":
            score_gain = 400
        else:
            score_gain = 0

        score += int(score_gain * score_multiplier)
        feedback = STORY_CLUES[current_cipher_type] # Đây là thông điệp cần hiển thị đầy đủ
        if success_sound: success_sound.play()
        
        if current_level_index < len(STATION_ORDER) - 1:
            current_level_index += 1
            current_station_name = STATION_ORDER[current_level_index]
            player_x, player_y = STATIONS[current_station_name]["coords"]
            attempts_left = 3
            game_state = "feedback"
        
        if current_station_name == "Treasure_Location":
             game_state = "treasure_screen"
             # Nhạc chiến thắng sẽ được chơi khi rương mở ra
             
        save_progress()
    else:
        attempts_left -= 1
        if fail_sound: fail_sound.play()
        if attempts_left > 0:
            feedback = f"Sai! Còn {attempts_left} lần thử. Hãy suy nghĩ kỹ hơn!"
        else:
            feedback = "Hết lượt! Bạn đã thất bại trong nhiệm vụ giải mã."
            game_state = "game_over"

    input_text = ""
    input_key = ""
    input_active = False
    input_field = None


# HÀM: VẼ VĂN BẢN NGẮT DÒNG
def draw_wrapped_text(text, x, y, max_width, color=WHITE, font_type=font, center_x=False):
    """Vẽ văn bản lên màn hình với tính năng ngắt dòng tự động."""
    words = text.split(' ')
    lines = []
    current_line = ""
    for word in words:
        test_line = current_line + word + " "
        if font_type.size(test_line)[0] < max_width:
            current_line = test_line
        else:
            lines.append(current_line.strip())
            current_line = word + " "
    lines.append(current_line.strip())

    line_height = font_type.get_linesize()
    
    # Tính toán lại x nếu center_x là True
    if center_x:
        for i, line in enumerate(lines):
            text_surface = font_type.render(line, True, color)
            text_rect = text_surface.get_rect(centerx=x) # centerx sẽ căn giữa theo x truyền vào
            text_rect.y = y + i * line_height
            screen.blit(text_surface, text_rect)
    else:
        for i, line in enumerate(lines):
            text_surface = font_type.render(line, True, color)
            screen.blit(text_surface, (x, y + i * line_height))

    # Trả về chiều cao tổng của văn bản đã vẽ để tính toán vị trí các thành phần khác
    return len(lines) * line_height


# Giao diện
def draw_text(text, x, y, color=WHITE, font_type=handwritten_font, center_x=False):
    """Vẽ văn bản lên màn hình. Có thể căn giữa theo chiều ngang."""
    text_surface = font_type.render(text, True, color)
    text_rect = text_surface.get_rect()
    if center_x:
        text_rect.centerx = x
    else:
        text_rect.x = x
    text_rect.y = y
    screen.blit(text_surface, text_rect)

def draw_button(text, x, y, w, h, color, hover_color, text_color=WHITE, enabled=True):
    """Vẽ nút bấm và kiểm tra click. Bao gồm trạng thái bật/tắt."""
    global last_click_time
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    
    current_color = color
    is_hovered = False
    if enabled:
        if x < mouse[0] < x + w and y < mouse[1] < y + h:
            current_color = hover_color
            is_hovered = True
    else:
        current_color = BLUE # Màu cho nút bị vô hiệu hóa
        text_color = LIGHT_GRAY # Làm mờ chữ khi vô hiệu hóa

    pygame.draw.rect(screen, current_color, (x, y, w, h), border_radius=15)
    pygame.draw.rect(screen, GOLD, (x, y, w, h), 3, border_radius=15)
    
    text_surface = font.render(text, True, text_color)
    text_rect = text_surface.get_rect(center=(x + w // 2, y + h // 2))
    screen.blit(text_surface, text_rect)

    if enabled and is_hovered and click[0] == 1 and (pygame.time.get_ticks() - last_click_time) > 300:
        last_click_time = pygame.time.get_ticks()
        return True
    return False

def draw_input_box(x, y, w, h, display_text, active, label="", is_password=False):
    """Vẽ hộp nhập liệu."""
    border_color = GREEN if active else GRAY
    bg_color = DARK_BROWN

    pygame.draw.rect(screen, border_color, (x, y, w, h), 3, border_radius=15)
    pygame.draw.rect(screen, bg_color, (x + 2, y + 2, w - 4, h - 4), border_radius=12)

    if label:
        label_x = x - font.size(label)[0] - 10
        if label_x < 0:
            label_x = 5
        draw_text(label, label_x, y + 5, WHITE, font)

    display_value = display_text
    if is_password:
        display_value = '*' * len(display_text)

    draw_text(display_value, x + 10, y + 10, WHITE, font)

def draw_progress_bar():
    """Vẽ thanh tiến trình cấp độ dựa trên current_level_index."""
    bar_x, bar_y, bar_w, bar_h = 250, 90, 300, 20
    
    pygame.draw.rect(screen, LIGHT_GRAY, (bar_x, bar_y, bar_w, bar_h), border_radius=10)
    
    total_cipher_stations = len(STATION_ORDER) - 2
    progress_level_completed = max(0, current_level_index - 1)
    
    if total_cipher_stations > 0:
        progress_width = (progress_level_completed / total_cipher_stations) * bar_w
    else:
        progress_width = 0

    if current_station_name == "Treasure_Location":
        progress_width = bar_w

    pygame.draw.rect(screen, GREEN, (bar_x, bar_y, progress_width, bar_h), border_radius=10)
    pygame.draw.rect(screen, GOLD, (bar_x, bar_y, bar_w, bar_h), 2, border_radius=10)
    
    draw_text(f"Đã giải: {progress_level_completed}/{total_cipher_stations}", bar_x + bar_w + 20, bar_y - 5, WHITE, font)


# Vòng lặp game chính
running = True
clock = pygame.time.Clock()

treasure_opened = False

while running:
    screen.blit(background, (0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            save_progress()
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            mouse_pos = event.pos
            if game_state == "map":
                # Xử lý click vào các trạm
                for i, station_name in enumerate(STATION_ORDER):
                    station_info = STATIONS[station_name]
                    station_coords = station_info["coords"]
                    
                    click_region_size = 40
                    station_rect = pygame.Rect(station_coords[0] - click_region_size // 2, station_coords[1] - click_region_size // 2, click_region_size, click_region_size)
                    
                    can_click = False
                    # Cho phép click vào trạm hiện tại và trạm tiếp theo
                    if i == current_level_index:
                        can_click = True
                    elif i == current_level_index + 1:
                        can_click = True

                    if can_click and station_rect.collidepoint(mouse_pos):
                        current_time = pygame.time.get_ticks()
                        if (current_time - last_click_time) > 300:
                            last_click_time = current_time
                            
                            player_x, player_y = station_coords
                            current_station_name = station_name

                            
                            if station_info["cipher"]:
                                selected_cipher = station_info["cipher"]
                                attempts_left = 3
                                input_text = ""
                                input_key = ""
                                input_active = False
                                show_hint = False
                                game_state = "decode" # Chuyển sang màn hình giải mã
                            elif station_name == "Treasure_Location":
                                game_state = "treasure_screen"
                                # Nhạc chiến thắng sẽ được chơi khi rương mở
                            elif station_name == "Start":
                                pass
                            
                            input_text = ""
                            input_key = ""
                            input_active = False
                            input_field = None
                            show_hint = False
            
            elif game_state == "decode":
                key_box_rect = pygame.Rect(300, 200, 250, 40)
                text_box_rect = pygame.Rect(300, 250, 250, 40)
                
                if selected_cipher in ["Vigenere", "AES"] and key_box_rect.collidepoint(mouse_pos):
                    input_active = True
                    input_field = "key"
                elif text_box_rect.collidepoint(mouse_pos):
                    input_active = True
                    input_field = "text"
                elif selected_cipher in ["Caesar", "RSA"] and key_box_rect.collidepoint(mouse_pos):
                    input_active = True
                    input_field = "text"
                else:
                    input_active = False
                    input_field = None
            
            elif game_state == "treasure_screen":
                open_chest_button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT - 100, 200, 50)
                if open_chest_button_rect.collidepoint(mouse_pos) and not treasure_opened:
                    current_time = pygame.time.get_ticks()
                    if (current_time - last_click_time) > 300:
                        last_click_time = current_time
                        treasure_opened = True
                        if chest_open_sound: chest_open_sound.play() # Chơi âm thanh mở rương
                        pygame.mixer.music.stop() # Dừng nhạc nền
                        if win_sound: win_sound.play() # Chơi nhạc chiến thắng
            
            # --- Xử lý cuộn bằng chuột trong màn hình cẩm nang ---
            elif game_state == "guide":
                # Tính toán lại các giá trị cần thiết cho việc cuộn
                guide_box_width = WIDTH - 100
                guide_box_height = HEIGHT - 100
                guide_box_y = (HEIGHT - guide_box_height) // 2
                content_y_start = guide_box_y + 20 + title_font.get_linesize() + 20
                button_area_height = 80
                content_height_visible = guide_box_height - (content_y_start - guide_box_y) - button_area_height
                
                max_scroll_offset = max(0, total_guide_content_height - content_height_visible)

                if event.button == 4: # Cuộn lên (mouse wheel up)
                    guide_scroll_offset = max(0, guide_scroll_offset - small_font.get_linesize() * 3) # Cuộn lên 3 dòng
                    guide_scroll_offset = min(guide_scroll_offset, max_scroll_offset) # Đảm bảo không cuộn quá giới hạn
                elif event.button == 5: # Cuộn xuống (mouse wheel down)
                    guide_scroll_offset = min(max_scroll_offset, guide_scroll_offset + small_font.get_linesize() * 3) # Cuộn xuống 3 dòng
                    guide_scroll_offset = max(0, guide_scroll_offset) # Đảm bảo không cuộn quá giới hạn


        elif event.type == pygame.KEYDOWN and game_state == "decode" and input_active and input_field:
            if event.key == pygame.K_BACKSPACE:
                if input_field == "key":
                    input_key = input_key[:-1]
                else:
                    input_text = input_text[:-1]
            elif event.key == pygame.K_RETURN:
                check_decryption()
            elif event.unicode.isprintable():
                if input_field == "key":
                    if len(input_key) < 32:
                        input_key += event.unicode
                else:
                    if len(input_text) < 32:
                        input_text += event.unicode

    # --- Logic vẽ màn hình theo trạng thái game ---
    if game_state == "map":
        draw_text("Bản Đồ Kho Báu", WIDTH // 2, 20, GOLD, title_font, center_x=True)
        draw_text(f"Điểm của bạn: {score}", 50, 50, WHITE, font)
        draw_progress_bar()

        for i, station_name in enumerate(STATION_ORDER):
            station_info = STATIONS[station_name]
            x, y = station_info["coords"]
            label = station_info["label"]
            
            station_draw_color = GRAY
            if i <= current_level_index:
                station_draw_color = GREEN
                if station_name == current_station_name:
                    station_draw_color = LIGHT_BLUE
                elif station_name == "Treasure_Location" and i == current_level_index:
                    station_draw_color = GOLD
            
            if i > 0:
                prev_station_coords = STATIONS[STATION_ORDER[i-1]]["coords"]
                if i -1 <= current_level_index: 
                    pygame.draw.line(screen, WHITE, prev_station_coords, (x, y), 2)
        
            if station_image:
                screen.blit(station_image, (x - station_image.get_width() // 2, y - station_image.get_height() // 2))
                pygame.draw.circle(screen, station_draw_color, (x, y), station_image.get_width() // 2 + 2, 2)
            else:
                pygame.draw.circle(screen, station_draw_color, (x, y), 20)
                pygame.draw.circle(screen, WHITE, (x, y), 20, 2)
            
            label_surface = small_font.render(label, True, WHITE)
            label_rect = label_surface.get_rect(center=(x, y + 25 + small_font.get_linesize() // 2))
            screen.blit(label_surface, label_rect)
        
        if player_image:
            screen.blit(player_image, (player_x - player_image.get_width() // 2, player_y - player_image.get_height() // 2))
        else:
            pygame.draw.circle(screen, player_color, (player_x, player_y), player_radius)
            pygame.draw.circle(screen, WHITE, (player_x, player_y), player_radius, 2)

        button_y_start = HEIGHT - 120
        
        current_station_data = STATIONS[current_station_name]
        if current_station_data["cipher"] and current_station_name != "Treasure_Location":
            if draw_button(f"Giải mã {current_station_data['cipher']}", WIDTH // 2 - 125, button_y_start, 250, 50, GREEN, GOLD):
                selected_cipher = current_station_data["cipher"]
                game_state = "decode"
                attempts_left = 3
                input_text = input_key = ""
                input_active = False
                show_hint = False

        if current_station_data["cipher"]:
            if draw_button(f"Gợi ý {current_station_data['cipher']}", WIDTH // 2 - 125, button_y_start + 60, 250, 50, GRAY, BLUE):
                show_hint = not show_hint
            
            # --- Cải thiện hiển thị hộp gợi ý trên bản đồ ---
            hint_box_x = 30
            hint_box_y = 400
            hint_box_width = WIDTH - 2 * hint_box_x
            hint_box_height = 120
            
            if show_hint:
                # Vẽ nền trong suốt cho hộp gợi ý
                s = pygame.Surface((hint_box_width, hint_box_height), pygame.SRCALPHA) # Kích thước surface
                s.fill(TRANSPARENT_BLACK) # Đổ màu đen trong suốt
                screen.blit(s, (hint_box_x, hint_box_y))
                
                pygame.draw.rect(screen, GOLD, (hint_box_x, hint_box_y, hint_box_width, hint_box_height), 2, border_radius=10)
                
                draw_text("Gợi ý:", hint_box_x + 10, hint_box_y + 5, GOLD, font)
                draw_wrapped_text(HINTS[current_station_data["cipher"]], hint_box_x + 10, hint_box_y + 30, hint_box_width - 20, WHITE, small_font)
        else:
            if draw_button("Gợi ý (Chung)", WIDTH // 2 - 125, button_y_start + 60, 250, 50, GRAY, BLUE):
                 show_hint = not show_hint
            if show_hint:
                hint_box_x = 30
                hint_box_y = 400
                hint_box_width = WIDTH - 2 * hint_box_x
                hint_box_height = 120
                
                # Vẽ nền trong suốt cho hộp gợi ý
                s = pygame.Surface((hint_box_width, hint_box_height), pygame.SRCALPHA)
                s.fill(TRANSPARENT_BLACK)
                screen.blit(s, (hint_box_x, hint_box_y))

                pygame.draw.rect(screen, GOLD, (hint_box_x, hint_box_y, hint_box_width, hint_box_height), 2, border_radius=10)
                draw_text("Gợi ý:", hint_box_x + 10, hint_box_y + 5, GOLD, font)
                draw_wrapped_text("Bạn đang ở trên bản đồ. Di chuyển đến các trạm để bắt đầu giải mã các loại mật mã khác nhau!", hint_box_x + 10, hint_box_y + 30, hint_box_width - 20, WHITE, small_font)
        
        # Nút "Cẩm nang" mới (Đã điều chỉnh vị trí để không bị tràn)
        if draw_button("Cẩm nang", WIDTH - 150, 20, 134, 50, BLUE, LIGHT_BLUE):
            game_state = "guide"

    elif game_state == "decode":
        draw_text(f"Giải mã {selected_cipher}", WIDTH // 2, 20, GOLD, title_font, center_x=True)
        
        cipher_message_info = MESSAGES[selected_cipher]
        message_y = 150
        
        if selected_cipher == "Caesar" or selected_cipher == "Vigenere":
            draw_text(f"Thông điệp mã hóa: {cipher_message_info[0]}", 50, message_y, WHITE, font)
        elif selected_cipher == "RSA":
            draw_wrapped_text(f"Thông điệp mã hóa (số): {cipher_message_info[0]}, e={cipher_message_info[1]}, n={cipher_message_info[2]}", 50, message_y, WIDTH - 100, WHITE, font)
        elif selected_cipher == "AES":
            draw_wrapped_text(f"Thông điệp mã hóa (Hex): {cipher_message_info[0].hex().upper()}", 50, message_y, WIDTH - 100, WHITE, font)

        input_box_x = WIDTH // 2 - 125
        if selected_cipher in ["Vigenere", "AES"]:
            draw_input_box(input_box_x, 200, 250, 40, input_key, input_active and input_field == "key", label="Khóa:")
            draw_input_box(input_box_x, 250, 250, 40, input_text, input_active and input_field == "text", label="Kết quả:")
        else:
            draw_input_box(input_box_x, 200, 250, 40, input_text, input_active and input_field == "text", label="Nhập câu trả lời:")

        draw_text(f"Còn {attempts_left} lần thử", 50, 320, WHITE, font)
        
        button_decode_y_start = HEIGHT - 150
        if draw_button("Kiểm tra", WIDTH // 2 - 75, button_decode_y_start, 150, 40, GREEN, GOLD):
            check_decryption()
        
        if draw_button("Quay lại bản đồ", WIDTH // 2 - 100, button_decode_y_start + 50, 200, 40, GRAY, GREEN):
            game_state = "map"
            input_active = False
            input_field = None
            input_text = ""
            input_key = ""
            feedback = ""

    elif game_state == "feedback":
        # Điều chỉnh vị trí và kích thước hộp phản hồi để nó nằm giữa màn hình
        feedback_box_width = WIDTH - 100 # Rộng hơn để chứa nội dung tốt hơn
        feedback_box_height = 200 # Chiều cao cố định, có thể điều chỉnh
        feedback_box_x = (WIDTH - feedback_box_width) // 2
        feedback_box_y = (HEIGHT - feedback_box_height) // 2 - 50 # Dịch lên trên một chút

        # Vẽ nền trong suốt cho hộp phản hồi
        s = pygame.Surface((feedback_box_width, feedback_box_height), pygame.SRCALPHA) # Kích thước surface
        s.fill(TRANSPARENT_BLACK) # Đổ màu đen trong suốt
        screen.blit(s, (feedback_box_x, feedback_box_y))

        pygame.draw.rect(screen, GOLD, (feedback_box_x, feedback_box_y, feedback_box_width, feedback_box_height), 3, border_radius=15)
        
        # Tiêu đề "Phản hồi:"
        draw_text("Phản hồi:", WIDTH // 2, feedback_box_y + 20, GOLD, title_font, center_x=True)
        
        # Văn bản phản hồi (manh mối cốt truyện)
        # Bắt đầu vẽ văn bản dưới tiêu đề một chút
        feedback_text_y = feedback_box_y + 20 + title_font.get_linesize() + 10 # Dưới tiêu đề
        feedback_text_x = feedback_box_x + 20 # Cách lề trái hộp
        feedback_text_width = feedback_box_width - 40 # Giảm 2 lần 20px lề
        
        # Gọi draw_wrapped_text, lấy chiều cao đã vẽ để tính toán vị trí nút
        text_drawn_height = draw_wrapped_text(
            feedback,
            feedback_text_x,
            feedback_text_y,
            feedback_text_width,
            GREEN if "thành công" in feedback or "Xuất sắc" in feedback else RED,
            font,
            center_x=False # Không căn giữa theo X để dễ kiểm soát lề trái/phải
        )
        
        # Vị trí nút "Tiếp tục hành trình"
        # Đặt nút dưới văn bản phản hồi và nằm giữa hộp phản hồi
        button_y_feedback = feedback_box_y + feedback_box_height - 60 # Đặt nút cách đáy hộp 60px
        
        if draw_button("Tiếp tục hành trình", WIDTH // 2 - 125, button_y_feedback, 250, 50, GREEN, GOLD):
            game_state = "map"
            input_active = False
            input_field = None
            input_text = ""
            input_key = ""
            feedback = ""

    elif game_state == "game_over":
        # Điều chỉnh vị trí và kích thước hộp Game Over để nó nằm giữa màn hình
        gameover_box_width = WIDTH - 100 # Rộng hơn
        gameover_box_height = 250 # Chiều cao đủ lớn
        gameover_box_x = (WIDTH - gameover_box_width) // 2
        gameover_box_y = (HEIGHT - gameover_box_height) // 2 - 50 # Dịch lên trên một chút

        # Vẽ nền trong suốt cho hộp Game Over
        s = pygame.Surface((gameover_box_width, gameover_box_height), pygame.SRCALPHA)
        s.fill(TRANSPARENT_BLACK)
        screen.blit(s, (gameover_box_x, gameover_box_y))

        pygame.draw.rect(screen, GOLD, (gameover_box_x, gameover_box_y, gameover_box_width, gameover_box_height), 3, border_radius=15)

        # Tiêu đề "Trò chơi kết thúc!"
        draw_text("Trò chơi kết thúc!", WIDTH // 2, gameover_box_y + 20, GOLD, title_font, center_x=True)
        
        # Văn bản phản hồi (thông báo thất bại/thắng)
        feedback_text_y = gameover_box_y + 20 + title_font.get_linesize() + 10
        feedback_text_x = gameover_box_x + 20
        feedback_text_width = gameover_box_width - 40

        # Gọi draw_wrapped_text, lấy chiều cao đã vẽ
        text_drawn_height = draw_wrapped_text(
            feedback,
            feedback_text_x,
            feedback_text_y,
            feedback_text_width,
            GREEN if "kho báu" in feedback else RED, # Kiểm tra nếu game over do tìm thấy kho báu
            font,
            center_x=False # Không căn giữa theo X để dễ kiểm soát lề trái/phải
        )
        
        # Tổng điểm của bạn
        score_text_y = feedback_text_y + text_drawn_height + 10 # Dưới văn bản feedback
        draw_text(f"Tổng điểm của bạn: {score}", WIDTH // 2, score_text_y, GOLD, font, center_x=True)
        
        # Nút "Chơi lại"
        button_y_gameover = gameover_box_y + gameover_box_height - 60 # Đặt nút cách đáy hộp 60px
        
        if draw_button("Chơi lại", WIDTH // 2 - 75, button_y_gameover, 150, 40, GREEN, GOLD):
            current_level_index = 0
            current_station_name = STATION_ORDER[0]
            player_x, player_y = STATIONS["Start"]["coords"]
            score = 0
            attempts_left = 3
            game_state = "map"
            save_progress()
            treasure_opened = False
            pygame.mixer.music.play(-1)
            input_active = False
            input_field = None
            input_text = ""
            input_key = ""
            feedback = ""

    elif game_state == "treasure_screen":
        draw_text("Bạn đã tìm thấy Kho Báu!", WIDTH // 2, 50, GOLD, win_font, center_x=True)
        
        chest_image = treasure_chest_open_image if treasure_opened else treasure_chest_closed_image
        if chest_image:
            # Căn giữa rương
            chest_x = WIDTH // 2 - chest_image.get_width() // 2
            chest_y = HEIGHT // 2 - chest_image.get_height() // 2 - 50
            screen.blit(chest_image, (chest_x, chest_y))
        else:
            pygame.draw.rect(screen, GOLD, (WIDTH // 2 - 100, HEIGHT // 2 - 100, 200, 200))

        if not treasure_opened:
            if draw_button("Mở Rương Báu", WIDTH // 2 - 100, HEIGHT - 100, 200, 50, GREEN, GOLD):
                pass
        else:
            # --- Hiển thị 3 ảnh tài liệu trên rương đã mở ---
            if document_images and all(doc is not None for doc in document_images):
                # Vị trí tương đối trên rương đã mở (điều chỉnh để phù hợp với rương của bạn)
                # Các ảnh sẽ nằm trên nắp rương, hơi nghiêng về phía người chơi
                # Vị trí này là tương đối, bạn có thể cần điều chỉnh x_offset và y_offset
                # để phù hợp với hình ảnh rương thực tế của bạn.

                base_chest_top_center_x = chest_x + chest_image.get_width() // 2
                base_chest_top_center_y = chest_y + chest_image.get_height() // 2 - 80 # Điểm trên nắp rương

                # Ảnh 1 (trái)
                if document_images[0]:
                    screen.blit(document_images[0], (base_chest_top_center_x - document_images[0].get_width() - 30, base_chest_top_center_y - 20))
                # Ảnh 2 (giữa)
                if document_images[1]:
                    screen.blit(document_images[1], (base_chest_top_center_x - document_images[1].get_width() // 2, base_chest_top_center_y))
                # Ảnh 3 (phải)
                if document_images[2]:
                    screen.blit(document_images[2], (base_chest_top_center_x + 30, base_chest_top_center_y - 20))
            
            win_message = "Chúc mừng bạn đã chinh phục được trò chơi!"
            draw_wrapped_text(win_message, WIDTH // 2, HEIGHT // 2 + chest_image.get_height() // 2 + 30, WIDTH - 100, WHITE, font, center_x=True)
            draw_text(f"Tổng điểm của bạn: {score}", WIDTH // 2, HEIGHT // 2 + chest_image.get_height() // 2 + 100, GOLD, font, center_x=True)
            
            if draw_button("Chơi lại", WIDTH // 2 - 75, HEIGHT - 50, 150, 40, GRAY, GREEN):
                current_level_index = 0
                current_station_name = STATION_ORDER[0]
                player_x, player_y = STATIONS["Start"]["coords"]
                score = 0
                attempts_left = 3
                game_state = "map"
                treasure_opened = False
                pygame.mixer.music.play(-1)
                save_progress()
                input_active = False
                input_field = None
                input_text = ""
                input_key = ""
                feedback = ""

    elif game_state == "guide": # <--- Logic vẽ màn hình cẩm nang
        # Vẽ nền trong suốt toàn màn hình
        s = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        s.fill(TRANSPARENT_BLACK)
        screen.blit(s, (0, 0))

        # Khung hộp cẩm nang
        guide_box_width = WIDTH - 100
        guide_box_height = HEIGHT - 100
        guide_box_x = (WIDTH - guide_box_width) // 2
        guide_box_y = (HEIGHT - guide_box_height) // 2

        pygame.draw.rect(screen, GOLD, (guide_box_x, guide_box_y, guide_box_width, guide_box_height), 3, border_radius=15)
        pygame.draw.rect(screen, DARK_BROWN, (guide_box_x + 3, guide_box_y + 3, guide_box_width - 6, guide_box_height - 6), border_radius=12)

        # Tiêu đề
        draw_text("Cẩm nang giải mã", WIDTH // 2, guide_box_y + 20, GOLD, title_font, center_x=True)

        # Nội dung cẩm nang
        content_x = guide_box_x + 30
        content_y_start = guide_box_y + 20 + title_font.get_linesize() + 20
        content_width = guide_box_width - 60 # Giữ nguyên chiều rộng cho nội dung
        
        # Tính chiều cao hiển thị được của nội dung (khu vực văn bản)
        button_area_height = 80 # Khoảng trống cho nút 'Quay lại bản đồ' và padding
        content_height_visible = guide_box_height - (content_y_start - guide_box_y) - button_area_height

        # Đặt vùng cắt (clipping area) cho nội dung văn bản
        content_rect_for_clip = pygame.Rect(content_x, content_y_start, content_width, content_height_visible)
        screen.set_clip(content_rect_for_clip)

        # --- LOGIC MỚI để hiển thị văn bản cuộn được, giữ nguyên các đoạn văn bản ---
        line_height = small_font.get_linesize()
        current_drawn_y_offset_in_box = 0 # Vị trí y tương đối trong tổng nội dung

        paragraphs = GUIDE_CONTENT.split('\n')
        total_content_calc_height = 0 # Tính toán tổng chiều cao thực của nội dung

        for paragraph in paragraphs:
            words = paragraph.split(' ')
            current_line_for_paragraph = ""
            lines_to_draw_for_paragraph = []

            for word in words:
                test_line = current_line_for_paragraph + word + " "
                if small_font.size(test_line)[0] < content_width:
                    current_line_for_paragraph = test_line
                else:
                    lines_to_draw_for_paragraph.append(current_line_for_paragraph.strip())
                    current_line_for_paragraph = word + " "
            lines_to_draw_for_paragraph.append(current_line_for_paragraph.strip())

            for line_text in lines_to_draw_for_paragraph:
                # Tính toán vị trí y tuyệt đối trên màn hình
                abs_y_on_screen = content_y_start + current_drawn_y_offset_in_box - guide_scroll_offset
                
                # Chỉ vẽ nếu dòng nằm trong vùng hiển thị của clipping rect
                if abs_y_on_screen < content_y_start + content_height_visible and abs_y_on_screen + line_height > content_y_start:
                    text_surface = small_font.render(line_text, True, WHITE)
                    screen.blit(text_surface, (content_x, abs_y_on_screen))
                
                current_drawn_y_offset_in_box += line_height
            
            # Thêm một khoảng trống nhỏ giữa các đoạn văn bản
            if paragraph != paragraphs[-1]:
                current_drawn_y_offset_in_box += line_height // 2 # Nửa khoảng cách dòng
            
            total_content_calc_height = current_drawn_y_offset_in_box # Cập nhật tổng chiều cao đã tính

        # REMOVED 'global' keyword here, as it's not needed outside of a function to modify a global variable.
        total_guide_content_height = total_content_calc_height
        
        # Đặt lại vùng cắt
        screen.set_clip(None)

        # Logic cuộn: Tính toán max_scroll_offset và kẹp guide_scroll_offset
        max_scroll_offset = max(0, total_guide_content_height - content_height_visible)
        
        # Kẹp guide_scroll_offset (quan trọng cho thay đổi kích thước cửa sổ hoặc nội dung)
        guide_scroll_offset = min(guide_scroll_offset, max_scroll_offset)
        guide_scroll_offset = max(0, guide_scroll_offset)

       

        # Nút Quay lại bản đồ
        if draw_button("Quay lại bản đồ", WIDTH // 2 - 100, guide_box_y + guide_box_height - 60, 200, 40, GRAY, GREEN):
            game_state = "map"
            guide_scroll_offset = 0 # Đặt lại cuộn khi rời cẩm nang



    pygame.display.flip()
    clock.tick(60)

pygame.quit()