import torch
import torch.nn as nn
import math

class PositionalEncoding(nn.Module):
    def __init__(self, d_model, max_len=5000):
        super(PositionalEncoding, self).__init__()
        
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        pe = pe.unsqueeze(0) # (1, max_len, d_model)
        self.register_buffer('pe', pe)

    def forward(self, x):
        # x shape: (batch_size, seq_len, d_model)
        # pe shape: (1, max_len, d_model) -> slice to (1, seq_len, d_model)
        x = x + self.pe[:, :x.size(1), :]
        return x

class StockTransformer(nn.Module):
    """
    Time-Series Transformer for next-day price prediction.
    """
    def __init__(self, input_dim, d_model=64, nhead=4, num_layers=2, output_dim=1, dropout=0.1):
        super(StockTransformer, self).__init__()
        
        self.d_model = d_model
        
        # Feature projection: input_dim -> d_model
        self.input_linear = nn.Linear(input_dim, d_model)
        
        self.pos_encoder = PositionalEncoding(d_model)
        
        encoder_layers = nn.TransformerEncoderLayer(d_model=d_model, nhead=nhead, dropout=dropout, batch_first=True)
        self.transformer_encoder = nn.TransformerEncoder(encoder_layers, num_layers=num_layers)
        
        self.decoder = nn.Linear(d_model, output_dim)

    def forward(self, x):
        # x shape: (batch_size, seq_len, input_dim)
        
        # Project inputs to d_model space
        x = self.input_linear(x) * math.sqrt(self.d_model)
        
        # Add positional encoding
        x = self.pos_encoder(x)
        
        # Transformer Encounter
        # Output shape: (batch_size, seq_len, d_model)
        output = self.transformer_encoder(x)
        
        # We take the output of the last time step to predict target
        # shape: (batch_size, d_model)
        last_step_output = output[:, -1, :]
        
        # Decode to target space
        prediction = self.decoder(last_step_output)
        
        return prediction
