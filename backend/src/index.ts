import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import morgan from 'morgan';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import { proxyRouter } from './routes/proxy.js';
import { healthRouter } from './routes/health.js';

dotenv.config();

const app = express();
const PORT = process.env['PORT'] || 3000;

// Security middleware
app.use(helmet());
app.use(cors({
    origin: ['http://localhost:5173', 'http://localhost:3000'],
    credentials: true,
}));
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Rate limiting
const limiter = rateLimit({
    windowMs: 15 * 60 * 1000, // 15 minutes
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: 'Too many requests, please try again later.' },
});
app.use('/api/', limiter);

// Routes
app.use('/health', healthRouter);
app.use('/api', proxyRouter);

// Root endpoint
app.get('/', (_req, res) => {
    res.json({
        service: 'MarketMind AI Backend',
        version: '1.0.0',
        status: 'running',
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`Backend listening on port ${PORT}`);
    console.log(`ML Services proxy target: ${process.env['ML_SERVICES_URL'] || 'http://localhost:8000'}`);
});

export default app;
