import torch
import torch.nn as nn
import torch.nn.functional as F

class MultitaskBlendshapeNet(nn.Module):
    def __init__(self, num_blendshapes=52):
        super(MultitaskBlendshapeNet, self).__init__()
        
        # Shared feature extractor
        self.shared_fc1 = nn.Linear(num_blendshapes, 128)
        self.shared_fc2 = nn.Linear(128, 64)
        self.dropout = nn.Dropout(0.3)
        
        # Task 1 Head: Emotion (7 classes: Angry, Disgust, Fear, Happy, Dull, Surprise, Neutral)
        self.emotion_head = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 7)
        )
        
        # Task 2 Head: Fatigue (3 classes: Awake, Tired, Sleepy)
        self.fatigue_head = nn.Sequential(
            nn.Linear(64, 32),
            nn.ReLU(),
            nn.Linear(32, 3)
        )
        
    def forward(self, x):
        # Forward pass through shared layers
        x = F.relu(self.shared_fc1(x))
        x = self.dropout(x)
        x = F.relu(self.shared_fc2(x))
        x = self.dropout(x)
        
        # Branch to separate task heads
        emotion_logits = self.emotion_head(x)
        fatigue_logits = self.fatigue_head(x)
        
        return emotion_logits, fatigue_logits

def load_model(filepath):
    model = MultitaskBlendshapeNet()
    try:
        model.load_state_dict(torch.load(filepath, map_location=torch.device('cpu')))
        model.eval()
        return model
    except Exception as e:
        print(f"Error loading model: {e}")
        return None
