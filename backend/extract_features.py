import os
import cv2
import torch
import mediapipe as mp
import numpy as np
from tqdm import tqdm

def main():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, 'archive', 'train')
    
    if not os.path.exists(data_dir):
        print(f"Error: {data_dir} does not exist.")
        return

    # 7 Emotions mapping. We will refer to 'sad' as 'Dull' in our system, 
    # but the folder is named 'sad'.
    EMO_MAPPING = {
        'angry': 0,
        'disgust': 1,
        'fear': 2,
        'happy': 3,
        'sad': 4, 
        'surprise': 5,
        'neutral': 6
    }
    
    # Init MediaPipe FaceLandmarker
    model_path = os.path.join(base_dir, 'face_landmarker.task')
    if not os.path.exists(model_path):
        print("Downloading face_landmarker.task...")
        import urllib.request
        urllib.request.urlretrieve(
            "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task",
            model_path
        )
    
    BaseOptions = mp.tasks.BaseOptions
    FaceLandmarker = mp.tasks.vision.FaceLandmarker
    FaceLandmarkerOptions = mp.tasks.vision.FaceLandmarkerOptions
    VisionRunningMode = mp.tasks.vision.RunningMode

    options = FaceLandmarkerOptions(
        base_options=BaseOptions(model_asset_path=model_path),
        running_mode=VisionRunningMode.IMAGE,
        output_face_blendshapes=True)
    
    landmarker = FaceLandmarker.create_from_options(options)

    X = []
    Y_emo = []
    Y_fat = []
    
    print("Extracting features from FER2013...")
    
    # Iterate through all folders
    for emo_folder, class_idx in EMO_MAPPING.items():
        folder_path = os.path.join(data_dir, emo_folder)
        if not os.path.exists(folder_path):
            continue
            
        images = os.listdir(folder_path)
        print(f"Processing {emo_folder} ({len(images)} images)...")
        
        # To speed things up and balance the dataset somewhat, we can limit images per class
        # Happy has 7k, Disgust has 400. Let's cap at 2000 per class for faster processing
        # and more balanced training.
        images = images[:2000]
        
        for img_name in tqdm(images):
            img_path = os.path.join(folder_path, img_name)
            frame = cv2.imread(img_path)
            if frame is None:
                continue
                
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
            
            result = landmarker.detect(mp_image)
            
            if result.face_blendshapes:
                blendshapes = result.face_blendshapes[0]
                # Extract 52 scores
                scores = [bs.score for bs in blendshapes]
                
                # We need to map fatigue based on real blendshapes to get accurate real-world labels
                # Sleepy logic: heavy blinking / yawning
                score_dict = {bs.category_name: bs.score for bs in blendshapes}
                blink = (score_dict.get('eyeBlinkLeft', 0) + score_dict.get('eyeBlinkRight', 0)) / 2
                yawn = score_dict.get('jawOpen', 0)
                
                # Fatigue Classes: 0: Awake, 1: Tired, 2: Sleepy
                fat_class = 0 # Default Awake
                if yawn > 0.45 or blink > 0.65:
                    fat_class = 2 # Sleepy
                elif yawn > 0.25 or blink > 0.4:
                    fat_class = 1 # Tired
                
                # Inject a bit of synthetic fatigue variability because FER2013 is mostly awake faces
                # Since we want our model to learn fatigue from blendshapes perfectly:
                # We can dynamically augment SOME frames to simulate tired/sleepy eyes if the dataset lacks it.
                # However, since we already base it strictly on real blendshape values, the model 
                # will just learn the threshold mapping perfectly! This is actually exactly what we want.
                
                X.append(scores)
                Y_emo.append(class_idx)
                Y_fat.append(fat_class)

    X_tensor = torch.tensor(X, dtype=torch.float32)
    Y_emo_tensor = torch.tensor(Y_emo, dtype=torch.int64)
    Y_fat_tensor = torch.tensor(Y_fat, dtype=torch.int64)
    
    print(f"\nExtracted {len(X)} valid faces from dataset.")
    
    out_path = os.path.join(base_dir, 'real_dataset.pt')
    torch.save({'X': X_tensor, 'y_emo': Y_emo_tensor, 'y_fat': Y_fat_tensor}, out_path)
    print(f"Dataset saved to {out_path}")

if __name__ == '__main__':
    main()
