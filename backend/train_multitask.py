import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
import os
from ml_model import MultitaskBlendshapeNet

def train_model():
    data_path = os.path.join(os.path.dirname(__file__), 'real_dataset.pt')
    if not os.path.exists(data_path):
        print(f"Error: Dataset {data_path} not found. Run extract_features.py first.")
        return
        
    print("Loading real dataset...")
    data = torch.load(data_path)
    X = data['X']
    y_emo = data['y_emo']
    y_fat = data['y_fat']
    
    dataset = TensorDataset(X, y_emo, y_fat)
    dataloader = DataLoader(dataset, batch_size=64, shuffle=True)
    
    model = MultitaskBlendshapeNet(num_blendshapes=52)
    optimizer = optim.Adam(model.parameters(), lr=0.001)
    
    # Loss functions for both tasks
    criterion_emo = nn.CrossEntropyLoss()
    criterion_fat = nn.CrossEntropyLoss()
    
    epochs = 40 # Increased epochs slightly for real data
    print("Starting training...")
    for epoch in range(epochs):
        model.train()
        total_loss = 0
        correct_emo = 0
        correct_fat = 0
        total_samples = 0
        
        for batch_x, batch_y_emo, batch_y_fat in dataloader:
            optimizer.zero_grad()
            
            emo_logits, fat_logits = model(batch_x)
            
            loss_emo = criterion_emo(emo_logits, batch_y_emo)
            loss_fat = criterion_fat(fat_logits, batch_y_fat)
            
            loss = loss_emo + loss_fat
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
            
            _, predicted_emo = torch.max(emo_logits.data, 1)
            _, predicted_fat = torch.max(fat_logits.data, 1)
            
            total_samples += batch_y_emo.size(0)
            correct_emo += (predicted_emo == batch_y_emo).sum().item()
            correct_fat += (predicted_fat == batch_y_fat).sum().item()
            
        acc_emo = 100 * correct_emo / total_samples
        acc_fat = 100 * correct_fat / total_samples
        
        if (epoch + 1) % 5 == 0 or epoch == 0:
            print(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(dataloader):.4f}, Emo Acc: {acc_emo:.2f}%, Fat Acc: {acc_fat:.2f}%")
        
    model_path = os.path.join(os.path.dirname(__file__), 'multitask_model.pth')
    torch.save(model.state_dict(), model_path)
    print(f"Training complete. Model saved to {model_path}")

if __name__ == "__main__":
    train_model()
