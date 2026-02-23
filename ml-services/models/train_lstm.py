import logging
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, random_split
from models.lstm import StockLSTM
from models.data_loader import TimeSeriesDataset
import os

# Configure logs
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("Trainer")

def train_model(symbol='INFY', epochs=10, batch_size=32, lr=0.001):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Using device: {device}")
    
    # 1. Prepare Data
    dataset = TimeSeriesDataset(symbol=symbol, seq_len=60)
    
    if len(dataset) == 0:
        logger.error("Dataset Empty. Exiting.")
        return

    # Split Train/Val
    train_size = int(0.8 * len(dataset))
    val_size = len(dataset) - train_size
    train_dataset, val_dataset = random_split(dataset, [train_size, val_size])
    
    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
    
    # 2. Init Model
    # Get input dim from dataset scaler features
    input_dim = dataset.scaler.n_features_in_
    model = StockLSTM(input_dim=input_dim, hidden_dim=64, num_layers=2, output_dim=1)
    model.to(device)
    
    criterion = nn.MSELoss()
    optimizer = optim.Adam(model.parameters(), lr=lr)
    
    logger.info("Starting training...")
    
    for epoch in range(epochs):
        model.train()
        train_loss = 0.0
        
        for X_batch, y_batch in train_loader:
            X_batch, y_batch = X_batch.to(device), y_batch.to(device)
            
            optimizer.zero_grad()
            outputs = model(X_batch)
            # outputs shape: (batch_size, 1), y_batch shape: (batch_size)
            loss = criterion(outputs.squeeze(), y_batch)
            loss.backward()
            optimizer.step()
            
            train_loss += loss.item() * X_batch.size(0)
            
        train_loss /= len(train_loader.dataset)
        
        # Validation
        model.eval()
        val_loss = 0.0
        with torch.no_grad():
            for X_val, y_val in val_loader:
                X_val, y_val = X_val.to(device), y_val.to(device)
                val_out = model(X_val)
                loss = criterion(val_out.squeeze(), y_val)
                val_loss += loss.item() * X_val.size(0)
                
        val_loss /= len(val_loader.dataset)
        
        logger.info(f"Epoch {epoch+1}/{epochs} | Train Loss: {train_loss:.6f} | Val Loss: {val_loss:.6f}")

    # Save Model
    os.makedirs("checkpoints", exist_ok=True)
    save_path = f"checkpoints/lstm_{symbol}.pth"
    torch.save(model.state_dict(), save_path)
    logger.info(f"Model saved to {save_path}")

if __name__ == "__main__":
    train_model(symbol='INFY')
