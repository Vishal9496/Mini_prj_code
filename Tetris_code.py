import pygame
import random
import speech_recognition as sr
import threading

# Initialize
pygame.init()
WIDTH, HEIGHT = 450, 600  # Increased width for sidebar
win = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Voice Controlled Tetris")

ROWS, COLS = 20, 10
CELL_SIZE = 30

BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
WHITE = (255, 255, 255)
COLORS = [
    (0, 255, 255),
    (255, 0, 0),
    (0, 255, 0),
    (255, 255, 0),
    (255, 165, 0)
]

SHAPES = {
    'I': [[1, 1, 1, 1]],
    'O': [[1, 1], [1, 1]],
    'T': [[0, 1, 0], [1, 1, 1]],
    'S': [[0, 1, 1], [1, 1, 0]],
    'Z': [[1, 1, 0], [0, 1, 1]],
    'J': [[1, 0, 0], [1, 1, 1]],
    'L': [[0, 0, 1], [1, 1, 1]],
}


def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]


class Piece:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = SHAPES[shape]
        self.color = random.choice(COLORS)


class Tetris:
    def __init__(self):
        self.grid = [[BLACK for _ in range(COLS)] for _ in range(ROWS)]
        self.current_piece = self.get_new_piece()
        self.next_piece = self.get_new_piece()
        self.score = 0
        self.game_over = False

    def get_new_piece(self):
        return Piece(COLS // 2 - 2, 0, random.choice(list(SHAPES.keys())))

    def valid_move(self, shape, x, y):
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell:
                    if x + j < 0 or x + j >= COLS or y + i >= ROWS:
                        return False
                    if y + i >= 0 and self.grid[y + i][x + j] != BLACK:
                        return False
        return True

    def lock_piece(self):
        for i, row in enumerate(self.current_piece.shape):
            for j, cell in enumerate(row):
                if cell and self.current_piece.y + i >= 0:
                    self.grid[self.current_piece.y + i][
                        self.current_piece.x + j
                    ] = self.current_piece.color
        self.clear_lines()
        self.current_piece = self.next_piece
        self.next_piece = self.get_new_piece()
        if not self.valid_move(
            self.current_piece.shape,
            self.current_piece.x,
            self.current_piece.y
        ):
            self.game_over = True

    def clear_lines(self):
        new_grid = []
        lines_cleared = 0
        for row in self.grid:
            if all(cell != BLACK for cell in row):
                lines_cleared += 1
            else:
                new_grid.append(row)
        for _ in range(lines_cleared):
            new_grid.insert(0, [BLACK for _ in range(COLS)])
        self.grid = new_grid
        self.score += lines_cleared * 100

    def move(self, dx):
        if self.valid_move(
            self.current_piece.shape,
            self.current_piece.x + dx,
            self.current_piece.y
        ):
            self.current_piece.x += dx

    def drop(self):
        while self.valid_move(
            self.current_piece.shape,
            self.current_piece.x,
            self.current_piece.y + 1
        ):
            self.current_piece.y += 1
        self.lock_piece()

    def rotate(self):
        new_shape = rotate(self.current_piece.shape)
        if self.valid_move(
            new_shape,
            self.current_piece.x,
            self.current_piece.y
        ):
            self.current_piece.shape = new_shape

    def step(self):
        if self.valid_move(
            self.current_piece.shape,
            self.current_piece.x,
            self.current_piece.y + 1
        ):
            self.current_piece.y += 1
        else:
            self.lock_piece()

    def draw_ui(self):
        font = pygame.font.SysFont("Arial", 24)
        score_text = font.render(f"Score: {self.score}", True, WHITE)
        win.blit(score_text, (WIDTH - 140, 30))

        next_text = font.render("Next:", True, WHITE)
        win.blit(next_text, (WIDTH - 140, 100))

        for i, row in enumerate(self.next_piece.shape):
            for j, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        win,
                        self.next_piece.color,
                        (
                            WIDTH - 140 + j * CELL_SIZE,
                            130 + i * CELL_SIZE,
                            CELL_SIZE,
                            CELL_SIZE
                        )
                    )

    def draw_grid(self):
        for y in range(ROWS):
            for x in range(COLS):
                pygame.draw.rect(
                    win, self.grid[y][x],
                    (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE)
                )
                pygame.draw.rect(
                    win, GRAY,
                    (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1
                )

        for i, row in enumerate(self.current_piece.shape):
            for j, cell in enumerate(row):
                if cell:
                    pygame.draw.rect(
                        win, self.current_piece.color,
                        (
                            (self.current_piece.x + j) * CELL_SIZE,
                            (self.current_piece.y + i) * CELL_SIZE,
                            CELL_SIZE,
                            CELL_SIZE
                        )
                    )

        self.draw_ui()


# 🎤 Voice Control
command = ""


def listen():
    global command
    recognizer = sr.Recognizer()
    
    # Increase the energy threshold for better detection
    recognizer.energy_threshold = 300
    # Adjust the pause threshold to better detect the end of speech
    recognizer.pause_threshold = 0.8
    # Allow for more dynamic audio by adjusting the dynamic energy threshold
    recognizer.dynamic_energy_threshold = True
    
    try:
        mic = sr.Microphone()
        print("Microphone initialized successfully!")
    except Exception as e:
        print(
            "Microphone not found or PyAudio not installed. "
            "Voice commands will not work."
        )
        print(f"Error: {e}")
        return
        
    with mic as source:
        print("Adjusting for ambient noise... Please wait...")
        recognizer.adjust_for_ambient_noise(source, duration=2)
        print("Noise profile adjusted. Ready to accept commands!")
        
        while True:
            try:
                print("Listening...")
                audio = recognizer.listen(
                    source, timeout=5, phrase_time_limit=3
                )
                print("Processing audio...")
                
                # Try multiple language recognition to improve detection
                text = ""
                try:
                    # Try English first
                    text = recognizer.recognize_google(
                        audio, language="en-US"
                    ).lower()
                except Exception:
                    try:
                        # Try Telugu if English fails
                        text = recognizer.recognize_google(
                            audio, language="te-IN"
                        ).lower()
                    except Exception:
                        try:
                            # Try Hindi if Telugu fails
                            text = recognizer.recognize_google(
                                audio, language="hi-IN"
                            ).lower()
                        except Exception:
                            # If all fail, try with no language specified
                            text = recognizer.recognize_google(audio).lower()
                
                print(f"Heard: {text}")
                command = text
                
            except sr.RequestError:
                print("API unavailable or unresponsive.")
                continue
            except sr.UnknownValueError:
                print("Could not understand audio.")
                continue
            except sr.WaitTimeoutError:
                print("Listening timed out. Restarting...")
                continue
            except Exception as e:
                print(f"Voice recognition error: {e}")
                continue


def handle_voice(tetris):
    global command
    if command:
        cmd = command.lower().strip()
        print(f"DEBUG: Recognized command: '{cmd}'")  # Debug print
    
        # English, Telugu, Hindi voice commands - expanded with variations
        left_cmds = [
            "left", "move left", "go left", "to left", 
            "edama", "edamavaipu", "లెఫ్ట్", "ఎడమ", "ఎడమవైపు",
            "baayen", "baayein", "baayen", "baayaan", "बाएं", "बायें", "बाएँ",
            "बायां"
        ]

        right_cmds = [
            "right", "move right", "go right", "to right", 
            "kudi", "kudivaipu", "రైట్", "కుడి", "కుడివైపు",
            "daayaan", "daayen", "daayen", "daahina",
            "दायां", "दाएं", "दाएँ", "दाहिना"
        ]

        rotate_cmds = [
            "rotate", "turn", "spin", "flip", "twist",
            "thirugu", "tiragandi", "రొటేట్", "తిరుగు", "తిరగండి",
            "ghumao", "ghuma", "ghumaaiye", "घुमाओ", "घुमा", "घुमाइए"
        ]

        down_cmds = [
            "down", "move down", "go down", 
            "kinda", "డౌన్", "కింద",
            "neeche", "neeche jao", "नीचे", "नीचे जाओ"
        ]

        drop_cmds = [
            "drop", "fall", "place", 
            "vadalandi", "drop", "డ్రాప్", "వదలండి",
            "chhodo", "drop", "छोड़ो", "ड्रॉप"
        ]

        # Debug: Print all our command lists for verification
        print(f"DEBUG: Looking for matches in: {cmd}")
        
        # More robust word matching
        words = cmd.split()
        
        # Function to check if any command matches either as a whole word
        # or substring
        def matches_command(cmd_text, cmd_list):
            # For non-English text, we need special handling
            # Check if any command is a direct word in the text
            if any(word in cmd_list for word in words):
                return True
            # Check if the command contains any of the command strings
            if any(cmd_word in cmd_text for cmd_word in cmd_list):
                return True
            # Check if any command is similar to the text (approximate 
            # matching)
            for cmd_word in cmd_list:
                if cmd_word in cmd_text:
                    return True
                # Special case for Telugu/Hindi characters
                if any(char not in 'abcdefghijklmnopqrstuvwxyz ' for char in
                        cmd_text):
                    # If input has non-Latin characters, be more lenient with
                    #  matching
                    if len(cmd_word) > 2 and (
                        cmd_word[:3] in cmd_text or cmd_text[:3] in cmd_word
                    ):
                        return True
            return False
        
        # Try to match commands in order of priority
        if matches_command(cmd, left_cmds):
            tetris.move(-1)
            print("DEBUG: Matched LEFT command")
        elif matches_command(cmd, right_cmds):
            tetris.move(1)
            print("DEBUG: Matched RIGHT command")
        elif matches_command(cmd, rotate_cmds):
            tetris.rotate()
            print("DEBUG: Matched ROTATE command")
        elif matches_command(cmd, down_cmds):
            tetris.step()
            print("DEBUG: Matched DOWN command")
        elif matches_command(cmd, drop_cmds):
            tetris.drop()
            print("DEBUG: Matched DROP command")
        else:
            print("DEBUG: No matching command found")
            
            # More verbose debugging for non-matching commands
            print(f"DEBUG: Word list is: {words}")
            print("DEBUG: Available commands:")
            print(f"  Left: {left_cmds}")
            print(f"  Right: {right_cmds}")
            print(f"  Rotate: {rotate_cmds}")
            print(f"  Down: {down_cmds}")
            print(f"  Drop: {drop_cmds}")
        
        print(f"Command executed: {cmd}")
        command = ""


# 🔁 Game Loop
def main():
    global fall_delay, command
    clock = pygame.time.Clock()
    tetris = Tetris()
    fall_delay = 200
    fall_time = 0
    start_ticks = pygame.time.get_ticks()

    voice_thread = threading.Thread(target=listen, daemon=True)
    voice_thread.start()

    # Display keyboard controls
    print("=== KEYBOARD CONTROLS FOR DEBUGGING ===")
    print("Left Arrow: Move Left")
    print("Right Arrow: Move Right")
    print("Up Arrow: Rotate")
    print("Down Arrow: Step Down")
    print("Space: Drop")
    print("======================================")

    running = True
    while running:
        win.fill(BLACK)
        fall_time += clock.get_rawtime()
        clock.tick(30)

        elapsed = (pygame.time.get_ticks() - start_ticks) // 1000
        fall_delay = max(
            100,
            500 - (elapsed // 30) * 50
        )  # Increase speed every 30s

        if fall_time > fall_delay:
            fall_time = 0
            tetris.step()

        handle_voice(tetris)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Add keyboard controls for easier testing
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    tetris.move(-1)
                    print("DEBUG: Keyboard LEFT")
                elif event.key == pygame.K_RIGHT:
                    tetris.move(1)
                    print("DEBUG: Keyboard RIGHT")
                elif event.key == pygame.K_UP:
                    tetris.rotate()
                    print("DEBUG: Keyboard ROTATE")
                elif event.key == pygame.K_DOWN:
                    tetris.step()
                    print("DEBUG: Keyboard DOWN")
                elif event.key == pygame.K_SPACE:
                    tetris.drop()
                    print("DEBUG: Keyboard DROP")
                # Test voice commands by simulating them with keyboard
                elif event.key == pygame.K_1:
                    command = "left"
                    print("DEBUG: Simulating voice 'left'")
                elif event.key == pygame.K_2:
                    command = "right"
                    print("DEBUG: Simulating voice 'right'")
                elif event.key == pygame.K_3:
                    command = "rotate"
                    print("DEBUG: Simulating voice 'rotate'")
                elif event.key == pygame.K_4:
                    command = "down"
                    print("DEBUG: Simulating voice 'down'")
                elif event.key == pygame.K_5:
                    command = "drop"
                    print("DEBUG: Simulating voice 'drop'")

        tetris.draw_grid()
        pygame.display.update()

        if tetris.game_over:
            print("Game Over!")
            pygame.time.delay(3000)
            running = False

    pygame.quit()


if __name__ == "__main__":
    main()