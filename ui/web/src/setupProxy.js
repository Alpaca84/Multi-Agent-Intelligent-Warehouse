const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:8002',
      changeOrigin: true,
      secure: false,
      logLevel: 'debug',
      timeout: 30000,
      onError: function (err, req, res) {
        console.log('Proxy error:', err.message);
        res.status(500).json({ error: 'Proxy error: ' + err.message });
      },
      onProxyReq: function (proxyReq, req, res) {
        console.log('Proxying request to:', proxyReq.path);
      },
      onProxyRes: function (proxyRes, req, res) {
        console.log('Proxy response:', proxyRes.statusCode, req.url);
      }
    })
  );
};
