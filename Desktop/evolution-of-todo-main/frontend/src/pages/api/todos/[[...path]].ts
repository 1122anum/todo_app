import type { NextApiRequest, NextApiResponse } from 'next';

/**
 * Proxy API route for todos endpoints
 * Forwards all /api/todos/* requests to FastAPI backend
 */
export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  const { path } = req.query;

  // Construct the backend URL
  const backendUrl = process.env.BACKEND_URL || 'http://localhost:8080';

  // Handle both /api/todos and /api/todos/:id
  const pathString = Array.isArray(path) ? path.join('/') : path || '';
  const targetUrl = pathString
    ? `${backendUrl}/api/todos/${pathString}`
    : `${backendUrl}/api/todos`;

  try {
    // Forward the request to FastAPI
    const response = await fetch(targetUrl, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        // Forward authorization header (required for protected routes)
        ...(req.headers.authorization && {
          Authorization: req.headers.authorization,
        }),
      },
      // Forward body for POST/PUT/PATCH requests
      ...(req.method !== 'GET' && req.method !== 'HEAD' && {
        body: JSON.stringify(req.body),
      }),
    });

    // Handle 204 No Content (DELETE success) - no body to parse
    if (response.status === 204) {
      return res.status(204).end();
    }

    // Get response data
    const contentType = response.headers.get('content-type');
    let data;

    // Try to parse as JSON, fallback to text
    if (contentType && contentType.includes('application/json')) {
      try {
        data = await response.json();
      } catch (e) {
        // If JSON parsing fails, return error
        return res.status(500).json({
          detail: 'Backend returned invalid JSON',
        });
      }
    } else {
      // Non-JSON response (shouldn't happen with our backend, but handle it)
      const text = await response.text();
      return res.status(response.status).json({
        detail: text || 'Backend returned non-JSON response',
      });
    }

    // Forward the response status and data
    return res.status(response.status).json(data);
  } catch (error: any) {
    // Network error or backend is down
    console.error('Proxy error:', error);

    return res.status(503).json({
      detail: 'Unable to connect to todos service',
      error: error.message,
    });
  }
}
