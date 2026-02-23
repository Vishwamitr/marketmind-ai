import { Router, Request, Response } from 'express';

const ML_SERVICES_URL = process.env['ML_SERVICES_URL'] || 'http://localhost:8000';

const router = Router();

interface HealthStatus {
    status: 'healthy' | 'degraded' | 'unhealthy';
    uptime: number;
    timestamp: string;
    services: {
        backend: { status: string };
        ml_services: { status: string; url: string; detail?: string };
    };
}

router.get('/', async (_req: Request, res: Response) => {
    const health: HealthStatus = {
        status: 'healthy',
        uptime: process.uptime(),
        timestamp: new Date().toISOString(),
        services: {
            backend: { status: 'running' },
            ml_services: { status: 'unknown', url: ML_SERVICES_URL },
        },
    };

    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 3000);

        const response = await fetch(`${ML_SERVICES_URL}/`, {
            signal: controller.signal,
        });
        clearTimeout(timeout);

        if (response.ok) {
            health.services.ml_services.status = 'running';
        } else {
            health.services.ml_services.status = 'error';
            health.status = 'degraded';
        }
    } catch (error) {
        health.services.ml_services.status = 'unreachable';
        health.services.ml_services.detail = 'Cannot connect to ML services';
        health.status = 'degraded';
    }

    const statusCode = health.status === 'healthy' ? 200 : 503;
    res.status(statusCode).json(health);
});

export { router as healthRouter };
