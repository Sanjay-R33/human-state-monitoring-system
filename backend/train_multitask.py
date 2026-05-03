import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import numpy as np
import os
from ml_model import MultitaskBlendshapeNet

def generate_synthetic_data(num_samples=5000):
    # 52 blendshapes
    X = np.random.rand(num_samples, 52).astype(np.float32) * 0.2  # Base neutral noise
    
    y_emotion = np.zeros(num_samples, dtype=np.int64)
    y_fatigue = np.zeros(num_samples, dtype=np.int64)
    
    # Let's map arbitrary indices for synthetic generation (assuming 0-51)
    # MediaPipe usually has smile around 44, 45; frown 46, 47; jawOpen 25; blink 9, 10
    # We will just inject strong signals in a few columns and assign labels based on them.
    for i in range(num_samples):
        # Determine Emotion (0: Happy, 1: Sad, 2: Angry, 3: Surprise, 4: Neutral)
        emo_type = np.random.randint(0, 5)
        if emo_type == 0: # Happy
            X[i, 44] = np.random.uniform(0.6, 1.0)
            X[i, 45] = np.random.uniform(0.6, 1.0)
        elif emo_type == 1: # Sad
            X[i, 46] = np.random.uniform(0.6, 1.0)
            X[i, 47] = np.random.uniform(0.6, 1.0)
        elif emo_type == 2: # Angry
            X[i, 3] = np.random.uniform(0.6, 1.0) # browDown
            X[i, 4] = np.random.uniform(0.6, 1.0)
        elif emo_type == 3: # Surprise
            X[i, 25] = np.random.uniform(0.6, 1.0) # jawOpen
            X[i, 1] = np.random.uniform(0.6, 1.0) # browInnerUp
        y_emotion[i] = emo_type
        
        # Determine Fatigue
        fat_type = np.random.randint(0, 3)
        if fat_type == 0:
            X[i, 9] = np.random.uniform(0.0, 0.2) # blinkLeft
            X[i, 10] = np.random.uniform(0.0, 0.2) # blinkRight
        elif fat_type == 1:
            X[i, 9] = np.random.uniform(0.3, 0.6)
            X[i, 10] = np.random.uniform(0.3, 0.6)
        elif fat_type == 2:
            X[i, 9] = np.random.uniform(0.7, 1.0)
            X[i, 10] = np.random.uniform(0.7, 1.0)
        y_fatigue[i] = fat_type
            
    return torch.tensor(X), torch.tensor(y_emotion), torch.tensor(y_fatigue)

def train_model():
    print("Generating synthetic blendshape data...")
    X, y_emo, y_fat = generate_synthetic_data(5000)
    dataset = TensorDataset(X, y_emo, y_fat)
    dataloader = DataLoader(dataset, batch_size=32, shuffle=True)
    
    model = MultitaskBlendshapeNet(num_blendshapes=52)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Loss functions for both tasks
    criterion_emo = nn.CrossEntropyLoss()
    criterion_fat = nn.CrossEntropyLoss()
    
    epochs = 20
    print("Starting training...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        for batch_x, batch_y_emo, batch_y_fat in dataloader:
            optimizer.zero_grad()
            
            emo_logits, fat_logits = model(batch_x)
            
            loss_emo = criterion_emo(emo_logits, batch_y_emo)
            loss_fat = criterion_fat(fat_logits, batch_y_fat)
            
            loss = loss_emo + loss_fat
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
        print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}")
        
    model_path = os.path.join(os.path.dirname(__file__), 'multitask_model.pth')
    torch.save(model.state_dict(), model_path)
    print(f"Training complete. Model saved to {model_path}")

if __name__ == "__main__":
    train_model()
