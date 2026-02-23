import { Router, Request, Response } from 'express';
import { authenticateJWT, type AuthenticatedRequest } from '../middleware/auth.js';

const ML_SERVICES_URL = process.env['ML_SERVICES_URL'] || 'http://localhost:8000';

const router = Router();

/**
 * Generic proxy handler — forwards requests to ML services FastAPI.
 */
async function proxyToML(req: Request, res: Response): Promise<void> {
    const targetPath = req.originalUrl.replace(/^\/api/, '/api');
    const targetUrl = `${ML_SERVICES_URL}${targetPath}`;

    try {
        const headers: Record<string, string> = {
            'Content-Type': req.headers['content-type'] || 'application/json',
        };

        // Forward auth header if present
        if (req.headers.authorization) {
            headers['Authorization'] = req.headers.authorization;
        }

        const fetchOptions: RequestInit = {
            method: req.method,
            headers,
        };

        if (['POST', 'PUT', 'PATCH'].includes(req.method) && req.body) {
            fetchOptions.body = JSON.stringify(req.body);
        }

        const response = await fetch(targetUrl, fetchOptions);
        const contentType = response.headers.get('content-type') || '';

        if (contentType.includes('application/json')) {
            const data = await response.json();
            res.status(response.status).json(data);
        } else {
            const text = await response.text();
            res.status(response.status).send(text);
        }
    } catch (error) {
        console.error(`Proxy error to ${targetUrl}:`, error);
        res.status(502).json({
            error: 'ML Services unavailable',
            detail: 'Could not connect to ML services backend',
        });
    }
}

// Public endpoints
router.get('/status', proxyToML);
router.get('/compliance/*path', proxyToML);
router.get('/news', proxyToML);
router.get('/stocks/*path', proxyToML);

// Auth endpoints (forwarded directly)
router.post('/auth/register', proxyToML);
router.post('/auth/login', proxyToML);

// Protected endpoints (require JWT)
router.get('/portfolio', authenticateJWT, proxyToML as (req: AuthenticatedRequest, res: Response) => void);
router.get('/admin/*path', authenticateJWT, proxyToML as (req: AuthenticatedRequest, res: Response) => void);
router.post('/backtest/*path', authenticateJWT, proxyToML as (req: AuthenticatedRequest, res: Response) => void);
router.get('/monitor/*path', authenticateJWT, proxyToML as (req: AuthenticatedRequest, res: Response) => void);

// Catch-all for other API routes
router.all('/*path', proxyToML);

export { router as proxyRouter };
