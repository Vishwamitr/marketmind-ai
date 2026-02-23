import React from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

interface ChartData {
  timestamp: string;
  close: number;
  sma_50: number;
  sma_200: number;
}

interface StockChartProps {
  data: ChartData[];
  symbol: string;
}

const StockChart: React.FC<StockChartProps> = ({ data, symbol }) => {
  return (
    <div className="bg-white p-4 rounded-lg shadow-md w-full h-96">
      <h2 className="text-xl font-bold mb-4">{symbol} Price History</h2>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis 
            dataKey="timestamp" 
            tickFormatter={(tick) => new Date(tick).toLocaleDateString()}
          />
          <YAxis domain={['auto', 'auto']} />
          <Tooltip 
            labelFormatter={(label) => new Date(label).toLocaleString()}
          />
          <Legend />
          <Line type="monotone" dataKey="close" stroke="#2563eb" name="Price" dot={false} />
          <Line type="monotone" dataKey="sma_50" stroke="#16a34a" name="SMA 50" dot={false} />
          <Line type="monotone" dataKey="sma_200" stroke="#dc2626" name="SMA 200" dot={false} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
};

export default StockChart;
