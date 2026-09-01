"""
AI Robot Car Controller
ESP8266 (AP mode, IP 192.168.4.1) + YOLOv11 + Python

Usage:
    python robot.py                                      # webcam + AP mode defaults
    python robot.py --camera 0 --esp-ip 192.168.4.1
    python robot.py --camera "http://IP:8080/video" --esp-ip 192.168.20.9 --ai-brain mistral

Controls (OpenCV window):
    Q / ESC  quit
"""

import argparse
import json
import platform
import subprocess
import threading
import time
from collections import deque
from enum import Enum
from typing import Dict, List, Optional, Tuple

print("[1/5] Importing OpenCV...")
import cv2
print("[2/5] Importing NumPy & Requests...")
import numpy as np
import requests
print("[3/5] Importing FilterPy (Kalman)...")
from filterpy.kalman import KalmanFilter
print("[4/5] Importing PyTorch...")
import torch
import torch.nn as nn
import torch.optim as optim
print("[5/5] Importing Ultralytics YOLO...")
from ultralytics import YOLO
print("[✓] All imports done.\n")


# ─────────────────────────────────────────
# State & Task enum
# ─────────────────────────────────────────

class RobotState(Enum):
    SEARCH   = "SEARCH"
    CENTER   = "CENTER"
    APPROACH = "APPROACH"
    CAUTIOUS = "CAUTIOUS"
    STOP     = "STOP"
    HOLD     = "HOLD"
    PATROL   = "PATROL"
    TASK     = "TASK"


class Task:
    def __init__(self, name: str):
        self.name = name
        self.started = False
        self.done = False

    def execute(self, ai: 'RobotCarAI') -> str:
        return "stop"


class ExploreTask(Task):
    def __init__(self):
        super().__init__("Explore")
        self.start_ts = 0

    def execute(self, ai: 'RobotCarAI') -> str:
        if not self.started:
            self.started = True
            self.start_ts = time.time()

        if time.time() - self.start_ts > 15:
            self.done = True
            return "stop"

        if ai.last_error_norm < -0.3: return "left"
        if ai.last_error_norm > 0.3: return "right"
        return "forward"


class FindTask(Task):
    def __init__(self, label: str):
        super().__init__(f"Find({label})")
        self.label = label

    def execute(self, ai: 'RobotCarAI') -> str:
        if ai.last_label == self.label and (time.time() - ai.last_det_time < 0.5):
            self.done = True
            return "stop"

        # Simple search behavior
        now = time.time()
        if now - ai.last_search_switch > 2.0:
            ai.search_left = not ai.search_left
            ai.last_search_switch = now
        return "left" if ai.search_left else "right"


class GoToTask(Task):
    def __init__(self, tx, ty):
        super().__init__(f"GoTo({tx},{ty})")
        self.tx, self.ty = tx, ty

    def execute(self, ai: 'RobotCarAI') -> str:
        dx = self.tx - ai.mapper.car_pos[0]
        dy = self.ty - ai.mapper.car_pos[1]
        dist = np.sqrt(dx*dx + dy*dy)
        if dist < 1.0:
            self.done = True
            return "stop"

        target_angle = np.degrees(np.arctan2(dy, dx))
        diff_angle = (target_angle - ai.mapper.car_angle + 180) % 360 - 180

        if abs(diff_angle) > 15:
            return "left" if diff_angle < 0 else "right"
        return "forward"


class TaskManager:
    def __init__(self):
        self.queue: deque[Task] = deque()
        self.current: Optional[Task] = None

    def add(self, task: Task, priority=False):
        if priority:
            self.queue.appendleft(task)
            self.current = None # Force switch
        else:
            self.queue.append(task)

    def step(self, ai: 'RobotCarAI') -> str:
        if not self.current:
            if not self.queue: return "stop"
            self.current = self.queue.popleft()

        act = self.current.execute(ai)
        if self.current.done:
            self.current = None
        return act


# ─────────────────────────────────────────
# Survival & Health
# ─────────────────────────────────────────

class SurvivalSystem:
    def __init__(self, battery_level=100.0):
        self.battery = battery_level
        self.is_stuck = False
        self.last_pos = [0.0, 0.0]
        self.last_move_ts = time.time()
        self.low_battery_threshold = 20.0

    def update(self, ai: 'RobotCarAI', action: str):
        # Deplete battery
        if action != "stop":
            self.battery -= 0.05
        else:
            self.battery -= 0.01

        self.battery = max(0, self.battery)

        # Stuck detection
        now = time.time()
        if action != "stop" and (now - self.last_move_ts) > 3.0:
            dist = np.sqrt((ai.mapper.car_pos[0] - self.last_pos[0])**2 +
                           (ai.mapper.car_pos[1] - self.last_pos[1])**2)
            if dist < 0.2:
                self.is_stuck = True
            else:
                self.is_stuck = False
                self.last_pos = [ai.mapper.car_pos[0], ai.mapper.car_pos[1]]
                self.last_move_ts = now
        elif action == "stop":
            self.last_move_ts = now
            self.last_pos = [ai.mapper.car_pos[0], ai.mapper.car_pos[1]]

    def needs_charge(self) -> bool:
        return self.battery < self.low_battery_threshold


# ─────────────────────────────────────────
# Neural network (optional, trained online)
# ─────────────────────────────────────────

class AIBrain(nn.Module):
    def __init__(self, input_size=7, hidden_size=64, output_size=5):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_size, hidden_size), nn.ReLU(),
            nn.Linear(hidden_size, hidden_size), nn.ReLU(),
            nn.Linear(hidden_size, output_size),
        )

    def forward(self, x):
        return self.net(x)

    def get_action(self, state_vec: List[float]) -> int:
        self.eval()
        with torch.no_grad():
            t = torch.FloatTensor([state_vec])
            out = self.forward(t)
            return int(torch.argmax(out, dim=1).item())

    def train_step(self, optimizer, s, a, r, s2, done, gamma=0.95):
        self.train()
        s_t = torch.FloatTensor([s])
        s2_t = torch.FloatTensor([s2])

        # Simple DQN-like update
        target = r
        if not done:
            target = r + gamma * torch.max(self.forward(s2_t)).item()

        output = self.forward(s_t)
        actual = output[0][a]
        loss = nn.MSELoss()(actual, torch.tensor(target, dtype=torch.float32))

        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
        return loss.item()


# ─────────────────────────────────────────
# Q-Learning agent
# ─────────────────────────────────────────

class QLearningAgent:
    ACTIONS = ["stop", "left", "right", "forward"]

    def __init__(self, alpha=0.1, gamma=0.9, epsilon=0.1):
        self.alpha   = alpha
        self.gamma   = gamma
        self.epsilon = epsilon
        self.q: Dict[tuple, Dict[str, float]] = {}

    def _key(self, state) -> tuple:
        return tuple(round(float(v), 2) if isinstance(v, (int, float)) else v for v in state)

    def choose(self, state) -> str:
        k = self._key(state)
        if np.random.rand() < self.epsilon or k not in self.q:
            return np.random.choice(self.ACTIONS)
        return max(self.q[k], key=self.q[k].get)

    def learn(self, s, a, reward, s2):
        k, k2 = self._key(s), self._key(s2)
        self.q.setdefault(k,  {a: 0.0 for a in self.ACTIONS})
        self.q.setdefault(k2, {a: 0.0 for a in self.ACTIONS})
        predict = self.q[k][a]
        target  = reward + self.gamma * max(self.q[k2].values())
        self.q[k][a] += self.alpha * (target - predict)


# ─────────────────────────────────────────
# ESP8266 HTTP controller
# ─────────────────────────────────────────

class RobotController:
    VALID = {"forward", "backward", "left", "right", "stop"}

    def __init__(self, esp_ip: str, timeout: float = 0.08, min_interval: float = 0.06):
        self.base_url     = f"http://{esp_ip}"
        self.session      = requests.Session()
        self.timeout      = timeout
        self.min_interval = min_interval
        self.last_cmd     = None
        self.last_ts      = 0.0

    def send(self, endpoint: str) -> bool:
        now = time.time()
        if self.last_cmd == endpoint and (now - self.last_ts) < self.min_interval:
            return True
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        try:
            self.session.get(url, timeout=self.timeout)
            self.last_cmd = endpoint
            self.last_ts  = now
            return True
        except requests.RequestException:
            self.last_cmd = None
            return False

    def forward(self):  self.send("forward")
    def backward(self): self.send("backward")
    def left(self):     self.send("left")
    def right(self):    self.send("right")
    def stop(self):     self.send("stop")


# ─────────────────────────────────────────
# Mapping & SLAM
# ─────────────────────────────────────────

class MapManager:
    def __init__(self, landmark_dist_threshold=2.0):
        self.landmarks: List[Dict] = []  # List of {"x", "y", "label", "count"}
        self.car_pos = [0.0, 0.0]
        self.car_angle = 0.0
        self.dist_threshold = landmark_dist_threshold

    def update_odometry(self, action: str, move_speed: float, turn_speed: float):
        if action == "forward":
            self.car_pos[0] += move_speed * np.cos(np.radians(self.car_angle))
            self.car_pos[1] += move_speed * np.sin(np.radians(self.car_angle))
        elif action == "backward":
            self.car_pos[0] -= move_speed * np.cos(np.radians(self.car_angle))
            self.car_pos[1] -= move_speed * np.sin(np.radians(self.car_angle))
        elif action == "left":
            self.car_angle -= turn_speed
        elif action == "right":
            self.car_angle += turn_speed
        self.car_angle %= 360

    def add_landmark(self, rel_x: float, rel_y: float, label: str):
        # Convert relative to absolute
        rad = np.radians(self.car_angle)
        abs_x = self.car_pos[0] + (rel_x * np.cos(rad) - rel_y * np.sin(rad))
        abs_y = self.car_pos[1] + (rel_x * np.sin(rad) + rel_y * np.cos(rad))

        # Check if landmark already exists nearby
        found = False
        for lm in self.landmarks:
            dist = np.sqrt((lm["x"] - abs_x)**2 + (lm["y"] - abs_y)**2)
            if dist < self.dist_threshold and lm["label"] == label:
                # Simple moving average for landmark position
                lm["x"] = lm["x"] * 0.9 + abs_x * 0.1
                lm["y"] = lm["y"] * 0.9 + abs_y * 0.1
                lm["count"] += 1
                found = True
                break

        if not found:
            self.landmarks.append({"x": abs_x, "y": abs_y, "label": label, "count": 1})
            if len(self.landmarks) > 500:
                self.landmarks.pop(0)

    def get_map_data(self):
        return [(lm["x"], lm["y"], lm["label"]) for lm in self.landmarks]


# ─────────────────────────────────────────
# Simple moving-average error filter
# ─────────────────────────────────────────

class ErrorFilter:
    def __init__(self, window: int = 8):
        self._w = deque(maxlen=window)

    def add(self, v: float) -> float:
        self._w.append(v)
        return float(np.mean(self._w))


# ─────────────────────────────────────────
# Speech output (optional)
# ─────────────────────────────────────────

class SpeechOutput:
    def __init__(self, enabled: bool = False):
        self.enabled = enabled
        self.engine  = None
        if not enabled:
            return
        try:
            import pyttsx3
            self.engine = pyttsx3.init()
        except Exception:
            if platform.system() == "Darwin":
                self._mac = True
            else:
                self.enabled = False

    def speak(self, text: str):
        if not self.enabled:
            return
        if self.engine:
            try:
                self.engine.say(text)
                self.engine.runAndWait()
            except Exception:
                pass
        elif getattr(self, "_mac", False):
            subprocess.Popen(["say", text])


# ─────────────────────────────────────────
# Ollama / Mistral Agent
# ─────────────────────────────────────────

class OllamaAgent:
    def __init__(self, url: str, model: str):
        self.url = url
        self.model = model
        self.history = [
            {"role": "system", "content": "You are a robot car's AI. Keep responses very short and witty."}
        ]

    def chat(self, text: str, ai: Optional['RobotCarAI'] = None) -> str:
        context = ""
        if ai:
            context = (
                f"\n[Status] Pos: {ai.mapper.car_pos}, Batt: {ai.survival.battery:.1f}%, "
                f"State: {ai.state.value}, Landmarks: {len(ai.mapper.landmarks)}"
            )

        self.history.append({"role": "user", "content": text + context})

        # Check for task-related keywords to see if we should return JSON
        task_mode = any(kw in text.lower() for kw in ["go to", "find", "explore", "task"])

        if task_mode:
            self.history[-1]["content"] += "\nReply with JSON: {\"thought\": \"...\", \"task\": \"Explore|Find|GoTo\", \"params\": [...], \"speech\": \"...\"}"

        try:
            r = requests.post(
                self.url,
                json={"model": self.model, "messages": self.history, "stream": False},
                timeout=8.0
            )
            r.raise_for_status()
            ans = r.json().get("message", {}).get("content", "...")
            self.history.append({"role": "assistant", "content": ans})

            if len(self.history) > 12:
                self.history.pop(1)
                self.history.pop(1)

            if task_mode and "{" in ans:
                try:
                    s, e = ans.find("{"), ans.rfind("}")
                    data = json.loads(ans[s:e+1])
                    if ai: self._apply_task(data, ai)
                    return data.get("speech", "Task accepted.")
                except Exception:
                    pass

            return ans
        except Exception:
            return "I lost my train of thought."

    def _apply_task(self, data: dict, ai: 'RobotCarAI'):
        t_type = data.get("task")
        params = data.get("params", [])
        if t_type == "Explore":
            ai.tasks.add(ExploreTask())
            ai.state = RobotState.TASK
        elif t_type == "Find" and params:
            ai.tasks.add(FindTask(params[0]))
            ai.state = RobotState.TASK
        elif t_type == "GoTo" and len(params) >= 2:
            ai.tasks.add(GoToTask(params[0], params[1]))
            ai.state = RobotState.TASK


# ─────────────────────────────────────────
# Main AI controller
# ─────────────────────────────────────────

class RobotCarAI:
    def __init__(self, args: argparse.Namespace):
        self.camera_source  = self._norm_src(args.camera)
        self.target_label   = args.target.lower()
        self.frame_w        = args.width
        self.frame_h        = args.height
        self.confidence     = args.conf
        self.infer_imgsz    = max(160, args.imgsz)
        self.detect_every   = max(1, args.detect_every)
        self.camera_flush   = max(0, args.camera_flush)
        self.ai_brain_mode  = args.ai_brain.lower()
        self.ollama_url     = args.ollama_url
        self.mistral_model  = args.mistral_model
        self.mistral_timeout = args.mistral_timeout
        self.ai_interval    = max(0.2, args.ai_interval)
        self.last_ai_ts     = 0.0

        # Mapping State
        self.mapper = MapManager()
        self.tasks  = TaskManager()
        self.survival = SurvivalSystem()

        # State / memory
        self.state              = RobotState.SEARCH
        self.search_left        = True
        self.last_search_switch = time.time()
        self.error_filter       = ErrorFilter(window=10)
        self.last_det_time      = 0.0
        self.last_error_norm    = 0.0
        self.last_close_ratio   = 0.0
        self.last_bbox          = None
        self.last_label         = "None"
        self.speak_ts           = 0.0

        # Kalman tracker (center_x, center_y, vx, vy)
        kf = KalmanFilter(dim_x=4, dim_z=2)
        kf.x = np.zeros(4)
        kf.F = np.array([[1,0,1,0],[0,1,0,1],[0,0,1,0],[0,0,0,1]], dtype=float)
        kf.H = np.array([[1,0,0,0],[0,1,0,0]], dtype=float)
        kf.P *= 1000.0
        kf.R = np.eye(2) * 10.0
        kf.Q = np.eye(4)
        self.kalman = kf

        # Sub-systems
        self.robot   = RobotController(args.esp_ip, timeout=args.esp_timeout)
        self.speech  = SpeechOutput(enabled=args.voice)
        self.ollama  = OllamaAgent(args.ollama_url.replace("generate", "chat"), args.mistral_model)
        self.ai_brain = AIBrain()
        self.optimizer = optim.Adam(self.ai_brain.parameters(), lr=0.001)
        self.rl_agent  = QLearningAgent()
        self.last_rl_state  = None
        self.last_rl_action = None

        # Optional spaCy NLP for voice
        try:
            import spacy
            self.nlp = spacy.load("en_core_web_sm")
        except Exception:
            self.nlp = None

        # Voice command thread
        self.voice_cmd   = None
        self.voice_state = None
        if args.voice:
            t = threading.Thread(target=self._voice_loop, daemon=True)
            t.start()

        # Load YOLO
        print(f"[*] Loading YOLO model '{args.model}' ...")
        self.model  = YOLO(args.model)
        self.names  = {int(k): str(v).lower() for k, v in self.model.names.items()}
        print(f"[✓] YOLO ready — {len(self.names)} classes")

    # ── helpers ───────────────────────────

    @staticmethod
    def _norm_src(src: str):
        try:
            return int(src)
        except ValueError:
            return src

    def _speak(self, text: str):
        if time.time() - self.speak_ts < 1.5:
            return
        self.speak_ts = time.time()
        self.speech.speak(text)

    # ── detection helpers ─────────────────

    def _extract(self, result):
        if result.boxes is None or len(result.boxes) == 0:
            return [], [], []
        xyxy   = result.boxes.xyxy.cpu().numpy()
        cls    = result.boxes.cls.cpu().numpy().astype(int)
        confs  = result.boxes.conf.cpu().numpy().astype(float)
        return xyxy, cls, confs

    def _best_target(self, boxes, cls, confs):
        best, best_score = None, 0.0
        cx = self.frame_w / 2.0
        for i, c in enumerate(cls):
            if self.names.get(c, "?") != self.target_label:
                continue
            x1, y1, x2, y2 = boxes[i]
            area = (x2 - x1) * (y2 - y1)
            cw   = 1.0 - min(abs((x1+x2)/2 - cx) / cx, 1.0)
            score = confs[i] * area * (0.6 + 0.4 * cw)
            if score > best_score:
                best_score = score
                best = {"box": (int(x1), int(y1), int(x2), int(y2)),
                        "label": self.names[c], "conf": confs[i]}
        return best

    def _obstacles(self, boxes, cls, confs):
        obs = []
        for i, c in enumerate(cls):
            if self.names.get(c, "?") == self.target_label:
                continue
            x1, y1, x2, y2 = boxes[i]
            if y2 > self.frame_h / 2:
                obs.append((x1, y1, x2, y2, self.names.get(c, "?")))
        return obs

    # ── state / action selection ──────────

    def _select_state(self, detected: bool, err: float, close: float) -> RobotState:
        if not detected:
            return RobotState.SEARCH
        if close >= 0.72:
            return RobotState.STOP
        if close >= 0.50:
            return RobotState.CAUTIOUS
        if abs(err) < 0.12:
            return RobotState.APPROACH
        return RobotState.CENTER

    def _select_action(self, state: RobotState, err: float, close: float, obs: list) -> str:
        # Obstacle avoidance first
        if obs:
            avg_x = np.mean([(o[0]+o[2])/2 for o in obs])
            return "right" if avg_x < self.frame_w/2 else "left"

        if state == RobotState.TASK:
            return self.tasks.step(self)

        if state == RobotState.SEARCH:
            now = time.time()
            if now - self.last_search_switch > 2.0:
                self.search_left = not self.search_left
                self.last_search_switch = now
            return "left" if self.search_left else "right"

        if state == RobotState.STOP:
            return "stop"

        if state in (RobotState.CAUTIOUS, RobotState.CENTER, RobotState.APPROACH):
            if abs(err) < 0.08:
                return "forward"
            return "left" if err < 0 else "right"

        return "stop"

    def _mistral_action(self, state, err, close, obs, detected) -> Tuple[str, str]:
        now = time.time()
        if now - self.last_ai_ts < self.ai_interval:
            return self._select_action(state, err, close, obs), "throttle"
        self.last_ai_ts = now

        payload = {
            "target": self.target_label, "state": state.value,
            "detected": detected, "error_norm": round(err, 3),
            "close_ratio": round(close, 3), "obstacles": len(obs),
        }
        prompt = (
            "You control a robot car. Pick ONE action: forward, left, right, stop.\n"
            "Rules: if close_ratio>=0.72 → stop. If obstacles>0 → prefer left/right/stop.\n"
            f"Input: {json.dumps(payload)}\n"
            'Reply ONLY compact JSON like {"action":"left","reason":"..."}'
        )
        try:
            r = requests.post(
                self.ollama_url,
                json={"model": self.mistral_model, "prompt": prompt,
                      "stream": False, "options": {"temperature": 0.1}},
                timeout=self.mistral_timeout,
            )
            r.raise_for_status()
            txt = r.json().get("response", "")
            s, e = txt.find("{"), txt.rfind("}")
            if s != -1 and e > s:
                action = json.loads(txt[s:e+1]).get("action", "stop").strip().lower()
                if action in {"forward", "left", "right", "stop"}:
                    return action, "mistral"
        except Exception:
            pass
        return self._select_action(state, err, close, obs), "fallback"

    def _safety(self, action: str, close: float, obs: list) -> str:
        if close >= 0.72:
            return "stop"
        if obs and action == "forward":
            return "stop"
        return action

    # ── voice ─────────────────────────────

    def _voice_loop(self):
        try:
            import speech_recognition as sr
        except ImportError:
            print("[WARN] speech_recognition not installed — voice disabled")
            return
        rec = sr.Recognizer()
        with sr.Microphone() as src:
            rec.adjust_for_ambient_noise(src, duration=0.5)
            while True:
                try:
                    audio = rec.listen(src, timeout=2, phrase_time_limit=4)
                    text = rec.recognize_google(audio).lower()
                    print(f"You said: {text}")
                    if not self._parse_voice(text):
                        # Not a hardcoded command, so chat with Mistral
                        if self.ai_brain_mode == "mistral":
                            # self is RobotCarAI, pass it for context
                            response = self.ollama.chat(text, ai=self)
                            print(f"Robot: {response}")
                            self._speak(response)
                except Exception:
                    pass

    def _parse_voice(self, cmd: str) -> bool:
        mapping = {
            "stop": "stop", "halt": "stop",
            "left": "left",  "right": "right",
            "forward": "forward", "go": "forward",
        }
        for kw, act in mapping.items():
            if kw in cmd:
                self.voice_cmd = act
                return True
        
        if "explore" in cmd:
            self.tasks.add(ExploreTask())
            self.voice_state = RobotState.TASK
            return True
        if "search" in cmd:
            self.voice_state = RobotState.SEARCH
            return True
        elif "hold" in cmd or "stay" in cmd:
            self.voice_state = RobotState.HOLD
            return True
        elif "follow" in cmd or "start" in cmd:
            self.voice_state = None
            return True
        return False

    # ── overlay drawing ───────────────────

    def _draw(self, frame, state: RobotState, action: str, err: float,
              close: float, ai_src: str, bbox, obs: list):
        h, w = frame.shape[:2]
        # Crosshair
        cv2.line(frame, (w//2, 0), (w//2, h), (255,255,0), 1)
        cv2.line(frame, (0, h//2), (w, h//2), (255,255,0), 1)
        # Target box
        if bbox:
            x1, y1, x2, y2 = bbox
            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,220,0), 2)
            cv2.circle(frame, ((x1+x2)//2, (y1+y2)//2), 5, (0,220,0), -1)
        # Obstacle boxes
        for ox1, oy1, ox2, oy2, lbl in obs:
            cv2.rectangle(frame, (int(ox1),int(oy1)), (int(ox2),int(oy2)), (0,0,220), 2)
            cv2.putText(frame, lbl, (int(ox1), int(oy1)-6), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0,0,220), 1)
        # HUD text
        lines = [
            f"State:  {state.value}",
            f"Action: {action}",
            f"AI:     {ai_src}",
            f"Pos:    ({self.mapper.car_pos[0]:.1f}, {self.mapper.car_pos[1]:.1f})",
            f"Angle:  {self.mapper.car_angle:.0f}",
            f"Target: {self.target_label}",
            f"Task:   {self.tasks.current.name if self.tasks.current else 'None'}",
            f"Batt:   {self.survival.battery:.1f}%",
        ]
        for i, ln in enumerate(lines):
            cv2.putText(frame, ln, (10, 24 + i*22),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (230,230,230), 1)

        # Draw Mini-Map (Bottom Right)
        map_size = 120
        map_origin = (w - map_size - 10, h - map_size - 10)
        cv2.rectangle(frame, map_origin, (w-10, h-10), (50,50,50), -1)
        cv2.rectangle(frame, map_origin, (w-10, h-10), (150,150,150), 1)
        
        # Draw car on map
        center = (map_origin[0] + map_size//2, map_origin[1] + map_size//2)
        cv2.circle(frame, center, 3, (0,255,255), -1)
        
        # Draw map dots
        for mx, my, mlbl in self.mapper.get_map_data():
            dx = int((mx - self.mapper.car_pos[0]) * 2)
            dy = int((my - self.mapper.car_pos[1]) * 2)
            pt = (center[0] + dx, center[1] + dy)
            if map_origin[0] < pt[0] < w-10 and map_origin[1] < pt[1] < h-10:
                cv2.circle(frame, pt, 1, (0,0,255), -1)

    # ── main loop ─────────────────────────

    def run(self):
        # Open camera (Windows: try CAP_DSHOW first)
        cap = None
        if platform.system() == "Windows" and isinstance(self.camera_source, int):
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, 0]:
                cap = cv2.VideoCapture(self.camera_source, backend)
                if cap.isOpened():
                    break
        if cap is None or not cap.isOpened():
            cap = cv2.VideoCapture(self.camera_source)
        cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.frame_w)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.frame_h)
        cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera: {self.camera_source}")

        print("[✓] Camera open. Press Q to quit.")
        frame_idx = 0
        cached_boxes, cached_cls, cached_confs = [], [], []

        try:
            while True:
                # Flush stale buffer frames
                for _ in range(self.camera_flush):
                    cap.grab()
                ok, frame = cap.read()
                if not ok or frame is None:
                    self.robot.stop()
                    time.sleep(0.05)
                    continue

                frame = cv2.resize(frame, (self.frame_w, self.frame_h))

                # Adaptive confidence based on brightness
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                bright = np.mean(gray)
                aconf = self.confidence
                if bright < 50:
                    aconf = max(0.10, aconf - 0.10)
                elif bright > 200:
                    aconf = min(0.80, aconf + 0.10)

                # Run YOLO every N frames
                frame_idx += 1
                if frame_idx % self.detect_every == 0 or not len(cached_boxes):
                    res = self.model(frame, imgsz=self.infer_imgsz,
                                     device="cpu", conf=aconf, verbose=False)
                    cached_boxes, cached_cls, cached_confs = self._extract(res[0])

                target  = self._best_target(cached_boxes, cached_cls, cached_confs)
                obs     = self._obstacles(cached_boxes, cached_cls, cached_confs)
                detected = target is not None

                err, close = 0.0, 0.0

                if detected:
                    x1, y1, x2, y2 = target["box"]
                    cx_t = (x1 + x2) / 2.0
                    err  = self.error_filter.add((cx_t - self.frame_w/2) / (self.frame_w/2))
                    close = max((x2-x1)/self.frame_w, (y2-y1)/self.frame_h)
                    # Kalman update
                    self.kalman.predict()
                    self.kalman.update(np.array([cx_t, (y1+y2)/2.0]))
                    self.last_det_time   = time.time()
                    self.last_error_norm = err
                    self.last_close_ratio = close
                    self.last_bbox = target["box"]
                    self.last_label = target["label"]
                else:
                    # Use Kalman prediction for up to 0.5 s after last sight
                    if time.time() - self.last_det_time < 0.5:
                        self.kalman.predict()
                        kx = self.kalman.x[0]
                        err   = self.error_filter.add((kx - self.frame_w/2) / (self.frame_w/2))
                        close = self.last_close_ratio
                        detected = True  # treat prediction as detected

                # Decide
                self.state = self._select_state(detected, err, close)

                # Input vector for neural/RL: [err, close, obstacles, batt, state_idx, detected, angle]
                state_list = list(RobotState)
                state_idx = state_list.index(self.state) if self.state in state_list else 0
                curr_vec = [float(err), float(close), float(len(obs)),
                            self.survival.battery/100.0, float(state_idx),
                            1.0 if detected else 0.0, self.mapper.car_angle/360.0]

                if self.ai_brain_mode == "mistral":
                    action, ai_src = self._mistral_action(self.state, err, close, obs, detected)
                elif self.ai_brain_mode == "neural":
                    idx = self.ai_brain.get_action(curr_vec)
                    action = ["stop", "left", "right", "forward", "backward"][idx]
                    ai_src = "neural"
                else:
                    action, ai_src = self._select_action(self.state, err, close, obs), "classic"

                action = self._safety(action, close, obs)

                # Voice overrides
                if self.voice_state:
                    self.state = self.voice_state
                if self.voice_cmd:
                    action = self.voice_cmd
                    self.voice_cmd = None

                # Q-Learning / Neural update
                rwd = (0.5 if detected and close > 0.3 else -0.1) - (0.2 if obs else 0.0)
                if self.survival.is_stuck: rwd -= 5.0

                cur_rl = (round(err,2), round(close,2), len(obs), self.state.value)
                if self.last_rl_state is not None:
                    self.rl_agent.learn(self.last_rl_state, self.last_rl_action, rwd, cur_rl)

                    # Also train the Neural Brain online
                    actions_list = ["stop", "left", "right", "forward", "backward"]
                    act_idx = actions_list.index(action) if action in actions_list else 0
                    if hasattr(self, 'last_vec'):
                        self.ai_brain.train_step(self.optimizer, self.last_vec, act_idx, rwd, curr_vec, False)

                self.last_rl_state  = cur_rl
                self.last_rl_action = action
                self.last_vec = curr_vec

                # Execute motor command
                {"forward": self.robot.forward,
                 "backward": self.robot.backward,
                 "left":    self.robot.left,
                 "right":   self.robot.right,
                 "stop":    self.robot.stop}.get(action, self.robot.stop)()

                # Survival logic
                self.survival.update(self, action)
                if self.survival.needs_charge() and not isinstance(self.tasks.current, GoToTask):
                     print("[!] Low Battery - Returning to Home")
                     self.tasks.add(GoToTask(0, 0), priority=True)
                     self.state = RobotState.TASK

                if self.survival.is_stuck:
                    print("[!] Robot STUCK - Attempting escape")
                    self.robot.backward()
                    time.sleep(0.5)
                    self.robot.left()
                    time.sleep(0.5)
                    self.survival.is_stuck = False

                # ── Mapper / Odometry ────────────────
                move_speed = 0.8 if action == "forward" else (0.5 if action == "backward" else 0.0)
                turn_speed = 8.0 if action in ("left", "right") else 0.0
                if action == "left": turn_speed = -turn_speed

                self.mapper.update_odometry(action, move_speed, abs(turn_speed))

                # Record obstacles in map
                for ox1, oy1, ox2, oy2, lbl in obs:
                    obj_center_x = (ox1 + ox2) / 2
                    rel_angle_deg = (obj_center_x - self.frame_w/2) / (self.frame_w/2) * 30
                    dist = 12.0 / (max(0.01, (ox2 - ox1) / self.frame_w))
                    
                    # Convert polar (dist, rel_angle) to relative Cartesian (rel_x, rel_y)
                    # rel_x is forward, rel_y is side
                    rel_x = dist * np.cos(np.radians(rel_angle_deg))
                    rel_y = dist * np.sin(np.radians(rel_angle_deg))
                    self.mapper.add_landmark(rel_x, rel_y, lbl)

                # Speech feedback
                _speak_map = {
                    RobotState.SEARCH:   "Searching",
                    RobotState.CENTER:   "Centering",
                    RobotState.APPROACH: "Approaching",
                    RobotState.STOP:     "Target reached",
                }
                if self.state in _speak_map:
                    self._speak(_speak_map[self.state])

                # Draw & show
                bbox_draw = self.last_bbox if detected else None
                self._draw(frame, self.state, action, err, close, ai_src, bbox_draw, obs)
                cv2.imshow("AI Robot Car", frame)

                key = cv2.waitKey(1) & 0xFF
                if key in (ord("q"), 27):
                    break

        finally:
            self.robot.stop()
            cap.release()
            cv2.destroyAllWindows()
            print("[✓] Robot stopped safely.")


# ─────────────────────────────────────────
# CLI
# ─────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="AI Robot Car — YOLOv11 + ESP8266")
    p.add_argument("--camera",         default="0",                          help="Camera index or stream URL")
    p.add_argument("--esp-ip",         default="192.168.4.1",                help="ESP8266 IP address")
    p.add_argument("--target",         default="person",                     help="Object class to follow")
    p.add_argument("--model",          default="yolo11n.pt",                 help="YOLO model file")
    p.add_argument("--conf",           type=float, default=0.35,             help="Detection confidence threshold")
    p.add_argument("--width",          type=int,   default=640,              help="Frame width")
    p.add_argument("--height",         type=int,   default=480,              help="Frame height")
    p.add_argument("--imgsz",          type=int,   default=416,              help="YOLO inference size (smaller = faster)")
    p.add_argument("--detect-every",   type=int,   default=2,                help="Run YOLO every N frames")
    p.add_argument("--camera-flush",   type=int,   default=2,                help="Discard N buffered frames per loop")
    p.add_argument("--esp-timeout",    type=float, default=0.08,             help="ESP HTTP timeout (s)")
    p.add_argument("--voice",          action="store_true",                  help="Enable voice feedback & commands")
    p.add_argument("--ai-brain",       default="classic", choices=["classic","mistral","neural"], help="Decision mode")
    p.add_argument("--mistral-model",  default="mistral",                    help="Ollama model name")
    p.add_argument("--ollama-url",     default="http://127.0.0.1:11434/api/generate")
    p.add_argument("--mistral-timeout",type=float, default=0.12)
    p.add_argument("--ai-interval",    type=float, default=1.2,              help="Seconds between LLM calls")
    return p.parse_args()


def main():
    args = parse_args()
    print("=" * 55)
    print("  AI Robot Car Controller")
    print("=" * 55)
    print(f"  Camera  : {args.camera}")
    print(f"  ESP IP  : {args.esp_ip}")
    print(f"  Target  : {args.target}")
    print(f"  Model   : {args.model}")
    print(f"  AI Brain: {args.ai_brain}")
    print("=" * 55)
    car = RobotCarAI(args)
    car.run()


if __name__ == "__main__":
    main()
