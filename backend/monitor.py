import cv2
import serial
import threading
import time
import os
import urllib.request
import mediapipe as mp

try:
    import torch
    from .ml_model import load_model
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

class MonitorService:
    def __init__(self):
        self.is_monitoring = False
        self.pulse_rate = 75 # Default normal
        self.face_emotion = "Neutral"
        self.final_emotion = "Neutral"
        self.final_fatigue = "Neutral"
        self.current_frame = None
        self.dl_emotion = "Neutral"
        self.dl_fatigue = "Neutral"
        self.last_face_time = time.time()
        
        self.dl_model = None
        if HAS_TORCH:
            model_file = os.path.join(os.path.dirname(__file__), 'multitask_model.pth')
            if os.path.exists(model_file):
                self.dl_model = load_model(model_file)
                print("Loaded Multitask DL Model successfully.")
            else:
                print("Multitask DL Model weights not found.")
        
        self.serial_port = 'COM5' # Configure this based on actual arduino port
        self.baud_rate = 9600
        self.ser = None
        
        self.cap = None
        
        # Download MediaPipe face landmarker model if not exists
        self.model_path = os.path.join(os.path.dirname(__file__), 'face_landmarker.task')
        if not os.path.exists(self.model_path):
            print("Downloading face_landmarker.task...")
            try:
                urllib.request.urlretrieve(
                    "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
                    self.model_path
                )
                print("Download complete.")
            except Exception as e:
                print(f"Warning: Could not download model {e}")

        # Initialize MediaPipe Face Landmarker
        try:
            BaseOptions = mp.tasks.BaseOptions
            FaceLandmarker = mp.tasks.vision.FaceLandmarker
            FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
            VisionRunningMode = mp.tasks.vision.RunningMode

            options = FaceLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=self.model_path),
                running_mode=VisionRunningMode.IMAGE,
                output_face_blendshapes=True)
            
            self.landmarker = FaceLandmarker.create_from_options(options)
        except Exception as e:
            print(f"Warning: Could not initialize MediaPipe FaceLandmarker: {e}")
            self.landmarker = None
        
        self.thread_cam = None
        self.thread_pulse = None
        self.thread_fusion = None



    def start(self):
        if self.is_monitoring:
            return
        
        self.is_monitoring = True
        
        # Try to open serial port
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            print(f"Connected to {self.serial_port}")
        except Exception as e:
            print(f"Warning: Could not open serial port {self.serial_port}. Generating simulated pulse.")
            self.ser = None

        # Try to open webcam
        self.cap = cv2.VideoCapture(0)
        
        self.thread_pulse = threading.Thread(target=self._read_pulse, daemon=True)
        self.thread_cam = threading.Thread(target=self._read_cam, daemon=True)
        self.thread_fusion = threading.Thread(target=self._fusion_logic, daemon=True)
        
        self.thread_pulse.start()
        self.thread_cam.start()
        self.thread_fusion.start()

    def stop(self):
        self.is_monitoring = False
        if self.ser:
            self.ser.close()
        if self.cap:
            self.cap.release()
            
    def get_current_data(self):
        return {
            "emotion": self.final_emotion,
            "pulse_rate": self.pulse_rate,
            "dl_emotion": self.dl_emotion,
            "dl_fatigue": self.final_fatigue
        }

    def _read_pulse(self):
        while self.is_monitoring:
            if self.ser and self.ser.is_open:
                try:
                    line = self.ser.readline().decode('utf-8').strip()
                    if line.startswith("BPM:"):
                        bpm_str = line.split(":")[1]
                        new_bpm = int(bpm_str)
                        # Noise cancellation: filter abnormal spikes and apply exponential moving average
                        if 30 <= new_bpm <= 220:
                            if self.pulse_rate == 0 or self.pulse_rate == 75: # First valid reading
                                self.pulse_rate = new_bpm
                            else:
                                self.pulse_rate = int(0.3 * new_bpm + 0.7 * self.pulse_rate)
                except Exception:
                    pass
            else:
                # Simulate if no hardware
                import random
                self.pulse_rate = 60 + random.randint(0, 20)
                time.sleep(2)
            time.sleep(0.1)

    def _read_cam(self):
        frame_count = 0
        while self.is_monitoring:
            if self.cap and self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret:
                    # Detect emotion using MediaPipe
                    if getattr(self, 'landmarker', None) and frame_count % 15 == 0:  # process every 15 frames
                        try:
                            # Convert to RGB for MediaPipe
                            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
                            result = self.landmarker.detect(mp_image)
                            
                            if result.face_blendshapes:
                                self.last_face_time = time.time()
                                blendshapes = result.face_blendshapes[0]
                                scores = {bs.category_name: bs.score for bs in blendshapes}
                                
                                # Deep Learning Multitask Inference
                                if getattr(self, 'dl_model', None):
                                    try:
                                        blendshape_list = [bs.score for bs in blendshapes]
                                        if len(blendshape_list) == 52:
                                            with torch.no_grad():
                                                input_tensor = torch.tensor([blendshape_list], dtype=torch.float32)
                                                emo_logits, fat_logits = self.dl_model(input_tensor)
                                                
                                                emo_classes = ['Happy', 'Sad', 'Angry', 'Surprise', 'Neutral']
                                                fat_classes = ['Awake', 'Tired', 'Sleepy']
                                                
                                                self.dl_emotion = emo_classes[torch.argmax(emo_logits, dim=1).item()]
                                                self.dl_fatigue = fat_classes[torch.argmax(fat_logits, dim=1).item()]
                                    except Exception as e:
                                        print(f"DL Model error: {e}")
                                
                                # Map blendshapes to basic emotions
                                happy_score = (scores.get('mouthSmileLeft', 0) + scores.get('mouthSmileRight', 0)) / 2
                                sad_score = (scores.get('mouthFrownLeft', 0) + scores.get('mouthFrownRight', 0)) / 2
                                eyebrow_lift = (scores.get('browInnerUp', 0) + scores.get('browOuterUpLeft', 0) + scores.get('browOuterUpRight', 0)) / 3
                                surprise_score = max(scores.get('jawOpen', 0), eyebrow_lift)
                                angry_score = (scores.get('browDownLeft', 0) + scores.get('browDownRight', 0)) / 2
                                
                                emotions = {
                                    'Happy': happy_score,
                                    'Sad': sad_score,
                                    'Surprise': surprise_score,
                                    'Angry': angry_score
                                }
                                
                                max_emotion = max(emotions, key=emotions.get)
                                if emotions[max_emotion] > 0.3:
                                    self.face_emotion = max_emotion
                                else:
                                    self.face_emotion = "Neutral"
                            else:
                                # Reset states to Neutral if no face detected for over 2 seconds
                                if time.time() - getattr(self, 'last_face_time', time.time()) > 2.0:
                                    self.face_emotion = "Neutral"
                                    self.dl_emotion = "Neutral"
                                    self.dl_fatigue = "Neutral"
                        except Exception as e:
                            print(f"MediaPipe error: {e}")
                    
                    # Encode frame as JPEG for streaming
                    ret_jpg, buffer = cv2.imencode('.jpg', frame)
                    if ret_jpg:
                        self.current_frame = buffer.tobytes()
                    
                    frame_count += 1
                time.sleep(0.03) # ~30 frames per second
            else:
                import random
                emotions = ['Happy', 'Sad', 'Angry', 'Neutral', 'Surprise']
                self.face_emotion = random.choice(emotions)
                self.current_frame = None
                time.sleep(1)

    def _fusion_logic(self):
        while self.is_monitoring:
            face = self.face_emotion
            pulse = self.pulse_rate
            dl_fat = self.dl_fatigue
            
            # Emotion fusion
            if pulse > 100:
                if face in ["Angry", "Sad"]:
                   self.final_emotion = "High Stress"
                elif face == "Surprise":
                    self.final_emotion = "Shock"
                elif face == "Happy":
                    self.final_emotion = "Excited"
                else:
                    self.final_emotion = "Anxious"
            elif 60 <= pulse <= 100:
                # Per user request: depending upon the facial expression, predict final emotion states like neutral, happy, sad
                if face in ["Happy", "Sad", "Neutral", "Surprise", "Angry"]:
                    self.final_emotion = face
                else:
                    self.final_emotion = "Neutral"
            elif pulse < 60:
                if face in ["Sad", "Neutral"]:
                    self.final_emotion = "Fatigued"
                else:
                    self.final_emotion = face
            else:
                self.final_emotion = face if face else "Neutral"
                
            # Fatigue fusion
            if dl_fat == "Neutral":
                self.final_fatigue = "Neutral"
            else:
                if pulse < 60:
                    if dl_fat in ["Tired", "Sleepy"] or face in ["Sad", "Neutral"]:
                        self.final_fatigue = "Sleepy"
                    else:
                        self.final_fatigue = "Tired"
                elif pulse > 100:
                    self.final_fatigue = "Awake"
                else:
                    if dl_fat == "Sleepy" and face in ["Sad", "Neutral"]:
                        self.final_fatigue = "Sleepy"
                    elif dl_fat in ["Tired", "Sleepy"] or face == "Sad":
                        self.final_fatigue = "Tired"
                    else:
                        self.final_fatigue = "Awake"
                
            time.sleep(5) # Update every 5 seconds

# Global instance
monitor_service = MonitorService()
