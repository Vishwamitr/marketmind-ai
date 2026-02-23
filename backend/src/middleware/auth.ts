import { Request, Response, NextFunction } from 'express';
import jwt from 'jsonwebtoken';

const JWT_SECRET = process.env['JWT_SECRET'] || 'supersecretkey';

export interface AuthenticatedRequest extends Request {
    user?: {
        username: string;
        sub: string;
    };
}

/**
 * JWT authentication middleware.
 * Validates the Bearer token from the Authorization header.
 */
export function authenticateJWT(req: AuthenticatedRequest, res: Response, next: NextFunction): void {
    const authHeader = req.headers.authorization;

    if (!authHeader || !authHeader.startsWith('Bearer ')) {
        res.status(401).json({ detail: 'Missing or invalid authorization header' });
        return;
    }

    const token = authHeader.split(' ')[1];
    if (!token) {
        res.status(401).json({ detail: 'Token not provided' });
        return;
    }

    try {
        const decoded = jwt.verify(token, JWT_SECRET) as { sub: string; username?: string };
        req.user = {
            username: decoded.username || decoded.sub,
            sub: decoded.sub,
        };
        next();
    } catch (err) {
        res.status(401).json({ detail: 'Invalid or expired token' });
    }
}

/**
 * Optional auth — attaches user if token present, continues without if not.
 */
export function optionalAuth(req: AuthenticatedRequest, _res: Response, next: NextFunction): void {
    const authHeader = req.headers.authorization;

    if (authHeader && authHeader.startsWith('Bearer ')) {
        const token = authHeader.split(' ')[1];
        if (token) {
            try {
                const decoded = jwt.verify(token, JWT_SECRET) as { sub: string; username?: string };
                req.user = {
                    username: decoded.username || decoded.sub,
                    sub: decoded.sub,
                };
            } catch {
                // Token invalid — continue without user
            }
        }
    }
    next();
}
