import unittest
import torch
from models.transformer import StockTransformer

class TestStockTransformer(unittest.TestCase):
    
    def test_forward_pass(self):
        # Parameters
        batch_size = 4
        seq_len = 10
        input_dim = 5
        d_model = 16
        
        model = StockTransformer(input_dim=input_dim, d_model=d_model, nhead=2, num_layers=1)
        
        # Input tensor (batch, seq, feature)
        x = torch.randn(batch_size, seq_len, input_dim)
        
        # Forward
        output = model(x)
        
        # Output should be (batch_size, 1)
        self.assertEqual(output.shape, (batch_size, 1))

if __name__ == '__main__':
    unittest.main()
